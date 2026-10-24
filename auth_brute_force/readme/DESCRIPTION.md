Tracks every authentication attempt (web login, XML-RPC/JSON-RPC, per-call RPC
password checks and API keys) and bans a remote IP — or an IP + login pair —
after too many failures, persistently and shared across all workers.

Port to 20.0 hooks `res.users._assert_can_auth`, the single entry point core uses
for credential checks since 17.0. The core in-memory cooldown keeps working.
