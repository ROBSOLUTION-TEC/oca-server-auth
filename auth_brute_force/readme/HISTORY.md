## 20.0.1.0.0

- Hook `_assert_can_auth` instead of overriding `_login` / `authenticate` /
  `_check_credentials` (signatures changed in 18.0/20.0); covers API keys too.
- No request state stored on the class (was not thread/greenlet safe).
- `ir.access` ACL (replaces `ir.model.access` in 20.0); `ir.config_parameter` typed API (`get_int` / `get_str` / `get_bool`), required in 20.0.
- Whitelist accepts CIDR networks; failure counting window (`window_minutes`).
- Attempts readable by administrators only (was: every internal and portal user).
- Remote IP metadata lookup disabled by default; autovacuum purges old attempts.
- Core login cooldown no longer disabled on install.
