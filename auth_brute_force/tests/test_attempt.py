# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAttempt(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attempt = cls.env["res.authentication.attempt"]
        cls.icp = cls.env["ir.config_parameter"].sudo()
        cls.icp.set_int("auth_brute_force.max_by_ip", 5)
        cls.icp.set_int("auth_brute_force.max_by_ip_user", 3)
        cls.icp.set_str("auth_brute_force.whitelist_remotes", "")

    def _fail(self, n, remote="203.0.113.7", login="admin"):
        for _i in range(n):
            self.Attempt.create({"remote": remote, "login": login, "result": "failed"})

    def test_combo_limit(self):
        self._fail(2)
        self.assertTrue(self.Attempt._trusted("203.0.113.7", "admin"))
        self._fail(1)
        self.assertFalse(self.Attempt._trusted("203.0.113.7", "admin"))
        # other login from same IP still allowed until the IP limit
        self.assertTrue(self.Attempt._trusted("203.0.113.7", "other"))

    def test_ip_limit(self):
        for i in range(5):
            self._fail(1, login=f"user{i}")
        self.assertFalse(self.Attempt._trusted("203.0.113.7", "brand_new"))
        self.assertTrue(self.Attempt._trusted("203.0.113.8", "brand_new"))

    def test_success_resets(self):
        self._fail(3)
        self.Attempt.create(
            {"remote": "203.0.113.7", "login": "admin", "result": "successful"}
        )
        self.assertTrue(self.Attempt._trusted("203.0.113.7", "admin"))

    def test_unban(self):
        self._fail(3)
        banned = self.Attempt.create(
            {"remote": "203.0.113.7", "login": "admin", "result": "banned"}
        )
        self.assertFalse(self.Attempt._trusted("203.0.113.7", "admin"))
        banned.action_unban()
        self.assertEqual(banned.result, "unbanned")
        self.assertTrue(self.Attempt._trusted("203.0.113.7", "admin"))

    def test_whitelist_cidr(self):
        self._fail(10)
        self.icp.set_str("auth_brute_force.whitelist_remotes", "203.0.113.0/24, bogus")
        self.assertTrue(self.Attempt._trusted("203.0.113.7", "admin"))
        self.assertFalse(self.Attempt._is_whitelisted("198.51.100.1"))

    def test_whitelist_actions(self):
        self._fail(1)
        attempt = self.Attempt.search([("remote", "=", "203.0.113.7")], limit=1)
        attempt.action_whitelist_add()
        self.assertTrue(attempt.whitelisted)
        attempt.invalidate_recordset(["whitelisted"])
        attempt.action_whitelist_remove()
        attempt.invalidate_recordset(["whitelisted"])
        self.assertFalse(attempt.whitelisted)

    def test_window(self):
        self._fail(3)
        old = fields.Datetime.now() - timedelta(minutes=120)
        self.env.cr.execute(
            "UPDATE res_authentication_attempt SET create_date = %s WHERE remote = %s",
            (old, "203.0.113.7"),
        )
        self.Attempt.invalidate_model()
        self.icp.set_int("auth_brute_force.window_minutes", 60)
        self.assertTrue(self.Attempt._trusted("203.0.113.7", "admin"))
        self.icp.set_int("auth_brute_force.window_minutes", 0)
        self.assertFalse(self.Attempt._trusted("203.0.113.7", "admin"))

    def test_metadata_disabled_by_default(self):
        self._fail(1)
        attempt = self.Attempt.search([("remote", "=", "203.0.113.7")], limit=1)
        self.assertEqual(attempt.remote_metadata, "")
