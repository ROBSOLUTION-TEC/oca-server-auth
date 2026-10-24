System parameters (Settings > Technical > System Parameters):

| Key | Default | Meaning |
|---|---|---|
| `auth_brute_force.max_by_ip` | 50 | Failures from one IP (any login) before ban |
| `auth_brute_force.max_by_ip_user` | 10 | Failures for one IP + login before ban |
| `auth_brute_force.window_minutes` | 1440 | Only failures inside this window count (0 = no window, OCA legacy behaviour) |
| `auth_brute_force.whitelist_remotes` | (empty) | Comma separated IPs or CIDR networks never banned |
| `auth_brute_force.retention_days` | 90 | Attempts older than this are purged by the autovacuum (0 = keep) |
| `auth_brute_force.check_remote` | False | Query ip-api.com (plain HTTP) for IP metadata in the form view |

Odoo must run with `proxy_mode = True` behind a reverse proxy, otherwise every
attempt is recorded with the proxy address and a single ban blocks everybody.
