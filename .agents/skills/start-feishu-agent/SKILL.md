---
name: start-feishu-agent
description: Start and monitor the local Feishu Agent in this repository. Use when the user asks to start, run, restart, launch,联调, or monitor the Feishu bot project, including checking its WebSocket connection, watching message events, and confirming Water Pipe and Feishu reply results.
---

# Start Feishu Agent

Run all commands from the repository root. Preserve `.env` secrets and never print API keys, App Secrets, access tokens, full WebSocket URLs, or user identifiers.

## Start workflow

1. Reuse and poll an existing live terminal session for this project when one is already known. Do not start a duplicate process.
2. If no session is known, check that `.venv/bin/python` and `.env` exist. Check required values by presence or length only:
   - `FEISHU_APP_ID`
   - `FEISHU_APP_SECRET`
   - `AGENT_MODEL`
   - `OPENAI_BASE_URL`
   - `OPENAI_API_KEY`
3. Check for duplicate `.env` definitions, especially `OPENAI_API_KEY`; a later empty definition overrides an earlier value.
4. If `.venv` is missing, use Python 3.11+ to create it and install the project:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install -e '.[dev]'
   ```

5. Start the deterministic launcher in a persistent TTY session and retain its session ID:

   ```bash
   bash .agents/skills/start-feishu-agent/scripts/start_agent.sh
   ```

6. Poll logs until both the HTTPS endpoint request succeeds and the SDK reports `connected to wss://`. Report only that the connection succeeded; do not reproduce the full URL because it contains temporary credentials.
7. Tell the user to send `/help` or `你好` to the bot. Continue polling the same session.

## Acceptance signals

Treat the end-to-end path as successful only when logs show:

- an `im.message.receive_v1` event;
- a Water Pipe `/chat/completions` response with HTTP 200 for normal messages;
- a Feishu `/reply` response with HTTP 200;
- continuing WebSocket ping/pong heartbeats.

For `/help`, no model call is expected; only the event and Feishu reply must succeed.

## Troubleshooting

- `CERTIFICATE_VERIFY_FAILED`: the launcher already exports the `certifi` CA bundle. Confirm `python -m certifi` succeeds.
- Heartbeats but no message event: verify `im.message.receive_v1` is subscribed, required message permissions are approved, and the latest Feishu app version is published. Group messages must @ the bot.
- `missing bearer token`: inspect duplicate or empty `OPENAI_API_KEY` definitions without displaying the value.
- Water Pipe 401/403: verify the `wp-v1-...` key and model permission.
- Feishu reply failure: inspect the returned code and message, but redact tokens and user identifiers.

## Stop or restart

Only stop the process when the user asks. Send Ctrl-C to the retained terminal session, confirm shutdown, then run the launcher again for a restart.

