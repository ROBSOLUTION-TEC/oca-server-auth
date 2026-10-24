# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo.tests import HttpCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestBruteForce(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        icp = cls.env["ir.config_parameter"].sudo()
        icp.set_int("auth_brute_force.max_by_ip", 50)
        icp.set_int("auth_brute_force.max_by_ip_user", 3)
        icp.set_str("auth_brute_force.whitelist_remotes", "")
        # isola o comportamento deste modulo do cooldown em memoria do core
        icp.set_int("base.login_cooldown_after", 0)
        cls.user = new_test_user(cls.env, login="bf_user", password="bf_user_pass_123")
        cls.Attempt = cls.env["res.authentication.attempt"]

    def _web_login(self, login, password):
        page = self.url_open("/web/login")
        token = re.search(r'name="csrf_token"\s+value="([^"]+)"', page.text).group(1)
        return self.url_open(
            "/web/login",
            data={"login": login, "password": password, "csrf_token": token},
            allow_redirects=False,
        )

    def _results(self, login):
        return self.Attempt.search([("login", "=", login)], order="id").mapped("result")

    def test_web_login_tracking_and_ban(self):
        self.assertEqual(self._web_login("bf_user", "bf_user_pass_123").status_code, 303)
        self.assertEqual(self._results("bf_user"), ["successful"])
        for _i in range(3):
            self.assertEqual(self._web_login("bf_user", "wrong").status_code, 200)
        self.assertEqual(self._results("bf_user")[-3:], ["failed"] * 3)
        # banido: mesmo com a senha correta
        response = self._web_login("bf_user", "bf_user_pass_123")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Too many failed login attempts", response.text)
        self.assertEqual(self._results("bf_user")[-1], "banned")
        # unban libera
        self.Attempt.search([("result", "=", "banned")]).action_unban()
        self.assertEqual(self._web_login("bf_user", "bf_user_pass_123").status_code, 303)

    def test_whitelisted_never_banned(self):
        self.env["ir.config_parameter"].sudo().set_str(
            "auth_brute_force.whitelist_remotes", "127.0.0.0/8,::1"
        )
        for _i in range(5):
            self._web_login("bf_user", "wrong")
        self.assertEqual(self._web_login("bf_user", "bf_user_pass_123").status_code, 303)
