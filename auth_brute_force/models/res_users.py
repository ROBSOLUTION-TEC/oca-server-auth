# Copyright 2017 Tecnativa - Jairo Llopis
# Copyright 2026 ROBSOLUTION - port 20.0
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Brute-force filter.

From 17.0 on, core funnels every credential check (web login, XML-RPC/JSON-RPC
``authenticate``, ``_check_uid_passwd`` on each RPC call and API-key checks)
through :meth:`res.users._assert_can_auth`. Hooking there replaces the old
classmethod overrides of ``_login``/``authenticate``/``_check_credentials``
(which changed signature in 18.0/20.0) and avoids storing request state on the
class, which was not thread/greenlet safe.

The core in-memory cooldown (``base.login_cooldown_*``) is kept: it is per
worker and volatile, while this module is persistent and shared by all workers.
"""

import contextlib
import logging

from odoo import _, models
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    def _auth_attempt_login(self, user):
        """Normalize the ``user`` hint given to ``_assert_can_auth``."""
        if isinstance(user, int):
            return self.sudo().browse(user).exists().login or str(user)
        return user or False

    @contextlib.contextmanager
    def _assert_can_auth(self, user=None):
        if not request:
            with super()._assert_can_auth(user=user):
                yield
            return

        remote = request.httprequest.remote_addr
        login = self._auth_attempt_login(user)
        attempts = self.env["res.authentication.attempt"].sudo()

        if not attempts._trusted(remote, login):
            attempts._log_attempt(remote, login, "banned")
            raise AccessDenied(
                _("Too many failed login attempts from your address. Access denied.")
            )

        try:
            with super()._assert_can_auth(user=user):
                yield
        except AccessDenied:
            attempts._log_attempt(remote, login, "failed")
            raise
        attempts._log_attempt(remote, login, "successful")
