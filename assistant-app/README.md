# Personal Assistant App

Proactive personal assistant with a web dashboard. Generates morning/evening briefings (weather, calendar, birthday nudges, meals, work priorities), maintains pantry + shopping list, and suggests Linear tickets / GitHub improvements.

Memory lives in `../assistant/*.md` (shared with Claude Cowork, so both stay in sync).

## Run

```bash
cd assistant-app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
python server.py
```

Open http://localhost:8756

## Integrations (all optional — app works without them)

| Source | Setup |
|---|---|
| Weather | None. Open-Meteo, free, uses home city from `profile.md`. |
| Linear | Personal API key → `.env` `LINEAR_API_KEY`. |
| GitHub | Personal access token → `.env` `GITHUB_TOKEN`, repos in `GITHUB_REPOS`. |
| Google Calendar + Gmail | 1) console.cloud.google.com → create project → enable Calendar API + Gmail API. 2) OAuth consent screen (External, add yourself as test user). 3) Credentials → Create OAuth client ID → Desktop app → download JSON as `data/credentials.json`. 4) Click "Connect Google" in the dashboard — browser opens for consent. |

## How it works

- `server.py` — FastAPI + APScheduler. Briefings auto-generate at 07:00 and 20:00 (configurable in dashboard) and are saved to `data/briefings/`.
- `agent.py` — gathers memory files + live data (weather, calendar, email, Linear, GitHub) into one context and asks Claude for the briefing.
- `memory.py` — read/write layer over `../assistant/*.md`.
- `integrations/` — one thin client per source; each degrades gracefully if unconfigured.
- `static/dashboard.html` — the GUI. Briefing tab, memory editors, shopping list, integration status.

## Chat with your assistant

The dashboard's chat box sends your message + all memory files to Claude; replies can include memory updates (e.g. "out of milk" → pantry.md updated) which the server applies automatically.
