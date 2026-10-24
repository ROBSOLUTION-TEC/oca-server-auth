===================================
Authentication - Brute-Force Filter
===================================

Tracks every authentication attempt (web login, XML-RPC/JSON-RPC, per-call RPC
password checks and API keys) and bans a remote IP, or an IP + login pair,
after too many failures. State is persistent and shared by all workers.

20.0 port: hooks ``res.users._assert_can_auth``. The core in-memory cooldown
keeps working.

Configuration
=============

System parameters:

* ``auth_brute_force.max_by_ip`` (50): failures from one IP before ban
* ``auth_brute_force.max_by_ip_user`` (10): failures for one IP + login
* ``auth_brute_force.window_minutes`` (1440): counting window, 0 = unlimited
* ``auth_brute_force.whitelist_remotes``: comma separated IPs / CIDR networks
* ``auth_brute_force.retention_days`` (90): autovacuum retention, 0 = keep
* ``auth_brute_force.check_remote`` (False): query ip-api.com for IP metadata

Run Odoo with ``proxy_mode = True`` behind a reverse proxy.

Usage
=====

Settings > Users & Companies > Authentication Attempts (administrators).
Open a banned attempt and click *Unban*, or manage the whitelist.
