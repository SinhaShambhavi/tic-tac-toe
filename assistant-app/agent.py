"""The brain: gathers context and asks Claude for briefings / chat replies."""
import datetime as dt
import json
import os
import re

import anthropic

import memory
from integrations import weather, linear_client, github_client, google_client

MODEL = os.getenv("ASSISTANT_MODEL", "claude-sonnet-4-5")

SYSTEM = """You are Shambhavi's proactive personal assistant. You are concise, warm, and
practical — no filler. Her memory files (profile, important dates, travel, pantry,
meal schedule, shopping list, work preferences) are provided, plus live data from
integrations. Rules:
- Apply the nudge rules in important-dates.md: for far-away people remind 7 days
  before (gift/plan), 1 day before (message), and day-of (call); same city 3 days
  before and day-of. Be concrete: say exactly what to do today.
- If travel.md shows an active/imminent trip, always report date, local time and
  weather for BOTH home and destination.
- Cross-reference meals against pantry status; flag missing ingredients.
- For work, respect the preferences in work.md (max suggestions, quiet days).
- If a memory file needs updating (e.g. she says "out of milk", a trip ended),
  include the full new file content in a block:
  <memory-update file="pantry.md">...entire new content...</memory-update>
- Treat <FILL IN> placeholders as absent data; mention (once, briefly) what filling
  them would unlock."""


def gather_context() -> dict:
    home = memory.get_home_city()
    dest = memory.get_travel_city()
    ctx = {
        "now_local": dt.datetime.now().strftime("%A %Y-%m-%d %H:%M"),
        "memory": memory.read_all(),
        "weather_home": weather.get_weather(home) if home else None,
        "weather_destination": weather.get_weather(dest) if dest else None,
        "calendar": google_client.get_events(days=2),
        "unread_emails": google_client.get_unread_emails(),
        "linear": linear_client.get_work(),
        "github": github_client.get_work(),
    }
    return ctx


def _call(user_msg: str, max_tokens: int = 1500) -> str:
    client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY
    ctx = gather_context()
    resp = client.messages.create(
        model=MODEL, max_tokens=max_tokens, system=SYSTEM,
        messages=[{"role": "user", "content":
                   f"CONTEXT (JSON):\n{json.dumps(ctx, default=str)}\n\n{user_msg}"}],
    )
    text = resp.content[0].text
    return _apply_memory_updates(text)


def _apply_memory_updates(text: str) -> str:
    """Apply <memory-update file="x"> blocks and strip them from the reply."""
    pattern = re.compile(r'<memory-update file="([^"]+)">\n?(.*?)</memory-update>', re.S)
    for name, content in pattern.findall(text):
        try:
            memory.write(name, content.strip() + "\n")
        except ValueError:
            pass
    return pattern.sub(lambda m: f"_(updated {m.group(1)})_", text).strip()


def morning_briefing() -> str:
    return _call(
        "Write my MORNING BRIEFING with sections: Today (date/time/weather, home and "
        "destination if traveling), Important dates (nudges), Schedule (calendar + "
        "emails needing action), Meals (today's, with pantry flags), Work (assigned "
        "issues, tickets I could take on, PRs awaiting review, at most one codebase "
        "improvement idea). Under 350 words, markdown."
    )


def evening_wrapup() -> str:
    return _call(
        "Write my EVENING WRAP-UP with sections: Tomorrow at a glance (weather, first "
        "event), Important dates (tonight/tomorrow nudges), Meals & shopping (check "
        "next 3 days of meals against pantry; REWRITE shopping-list.md via a "
        "memory-update block with 'Buy now' and 'For this week's meals' sections and "
        "today's date on the Last-updated line), Work close-out (max 3 lines). Under "
        "250 words, calm tone, markdown."
    )


def chat(message: str) -> str:
    return _call(
        f"Shambhavi says: {message}\n\nReply helpfully. If this reports a change to "
        "pantry/travel/dates/meals/work preferences, update the relevant memory "
        "file(s) via memory-update blocks.", max_tokens=1200
    )
