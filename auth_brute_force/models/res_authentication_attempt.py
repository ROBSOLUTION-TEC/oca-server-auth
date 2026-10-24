# Copyright 2015 GRAP - Sylvain LE GAL
# Copyright 2017 Tecnativa - Jairo Llopis
# Copyright 2026 ROBSOLUTION - port 20.0
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import ipaddress
import logging
from datetime import timedelta

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

GEOLOCALISATION_URL = "http://ip-api.com/json/{}"
PARAM = "auth_brute_force.{}"


class ResAuthenticationAttempt(models.Model):
    _name = "res.authentication.attempt"
    _description = "Authentication Attempt"
    _order = "create_date desc, id desc"

    login = fields.Char(string="Tried Login", index=True)
    remote = fields.Char(string="Remote IP", index=True)
    result = fields.Selection(
        string="Authentication Result",
        selection=[
            ("successful", "Successful"),
            ("failed", "Failed"),
            ("banned", "Banned"),
            ("unbanned", "Unbanned"),
        ],
        index=True,
    )
    remote_metadata = fields.Text(
        string="Remote IP metadata",
        compute="_compute_remote_metadata",
        help="Metadata publicly available for remote IP "
        "(only when 'auth_brute_force.check_remote' is enabled)",
    )
    whitelisted = fields.Boolean(compute="_compute_whitelisted")

    # ------------------------------------------------------------------ config
    def _param_int(self, key, default):
        return self.env["ir.config_parameter"].sudo().get_int(PARAM.format(key), default)

    def _whitelist_remotes(self):
        raw = self.env["ir.config_parameter"].sudo().get_str(
            PARAM.format("whitelist_remotes"), ""
        )
        return {item.strip() for item in raw.split(",") if item.strip()}

    # --------------------------------------------------------------- computes
    @api.depends("remote")
    def _compute_remote_metadata(self):
        check = self.env["ir.config_parameter"].sudo().get_bool(
            PARAM.format("check_remote"), False
        )
        for item in self:
            item.remote_metadata = ""
            if not (check and item.remote):
                continue
            url = GEOLOCALISATION_URL.format(item.remote)
            try:
                data = requests.get(url, timeout=4).json()
                item.remote_metadata = "\n".join(f"{k}: {v}" for k, v in data.items())
            except Exception:  # noqa: BLE001 - metadata is best effort
                _logger.warning("Could not fetch remote details from %s", url)

    def _compute_whitelisted(self):
        for item in self:
            item.whitelisted = self._is_whitelisted(item.remote)

    # ------------------------------------------------------------------ logic
    @api.model
    def _is_whitelisted(self, remote):
        """Whitelist entries may be single IPs or CIDR networks."""
        if not remote:
            return False
        try:
            address = ipaddress.ip_address(remote)
        except ValueError:
            return False
        for entry in self._whitelist_remotes():
            try:
                if address in ipaddress.ip_network(entry, strict=False):
                    return True
            except ValueError:
                _logger.warning("Invalid entry in auth_brute_force whitelist: %r", entry)
        return False

    @api.model
    def _hits_limit(self, limit, remote, login=None):
        """Failures since the last success (or unban) for ``remote``
        (optionally ``remote`` + ``login``) within the configured window."""
        domain = [("remote", "=", remote)]
        if login is not None:
            domain.append(("login", "=", login))
        window = self._param_int("window_minutes", 1440)
        if window > 0:
            since = fields.Datetime.now() - timedelta(minutes=window)
            domain.append(("create_date", ">=", since))
        last_ok = self.search(
            domain + [("result", "in", ["successful", "unbanned"])],
            order="id desc",
            limit=1,
        )
        if last_ok:
            domain.append(("id", ">", last_ok.id))
        failures = self.search_count(domain + [("result", "in", ["failed", "banned"])])
        return failures >= limit

    @api.model
    def _trusted(self, remote, login):
        """``True`` if the attempt may proceed, ``False`` if it is banned."""
        if not remote or self._is_whitelisted(remote):
            return True
        if self._hits_limit(self._param_int("max_by_ip", 50), remote):
            _logger.warning(
                "Authentication refused from banned remote %s (login tried: %r)",
                remote,
                login,
            )
            return False
        if login and self._hits_limit(
            self._param_int("max_by_ip_user", 10), remote, login
        ):
            _logger.warning(
                "Authentication refused from banned remote+login %s / %r",
                remote,
                login,
            )
            return False
        return True

    @api.model
    def _log_attempt(self, remote, login, result):
        """Persist the attempt in its own transaction: a failed login rolls
        back the request transaction, but the attempt must be kept."""
        if not remote:
            return
        try:
            with self.env.registry.cursor() as cr:
                self.with_env(self.env(cr=cr, su=True)).create(
                    {"remote": remote, "login": login or False, "result": result}
                )
        except Exception:  # noqa: BLE001 - never break authentication on logging
            _logger.exception("Could not log authentication attempt from %s", remote)

    @api.autovacuum
    def _gc_old_attempts(self):
        days = self._param_int("retention_days", 90)
        if days > 0:
            limit = fields.Datetime.now() - timedelta(days=days)
            self.sudo().search([("create_date", "<", limit)]).unlink()

    # ---------------------------------------------------------------- actions
    def action_unban(self):
        self.filtered(lambda a: a.result == "banned").write({"result": "unbanned"})

    def _set_whitelist(self, remotes):
        self.env["ir.config_parameter"].sudo().set_str(
            PARAM.format("whitelist_remotes"), ",".join(sorted(remotes))
        )

    def action_whitelist_add(self):
        self._set_whitelist(self._whitelist_remotes() | set(self.mapped("remote")))

    def action_whitelist_remove(self):
        self._set_whitelist(self._whitelist_remotes() - set(self.mapped("remote")))
