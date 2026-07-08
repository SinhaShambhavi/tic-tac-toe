"""FastAPI server: dashboard, API, and 07:00/20:00 briefing scheduler."""
import datetime as dt
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler

import memory
import personal
from integrations import weather, linear_client, github_client, google_client

ROOT = Path(__file__).resolve().parent
BRIEFINGS = ROOT / "data" / "briefings"
BRIEFINGS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Personal Assistant")
scheduler = BackgroundScheduler()


def _generate(kind: str) -> dict:
    import agent  # deferred so the app can boot without an API key
    text = agent.morning_briefing() if kind == "morning" else agent.evening_wrapup()
    stamp = dt.datetime.now().strftime("%Y-%m-%d")
    (BRIEFINGS / f"{stamp}-{kind}.md").write_text(text, encoding="utf-8")
    return {"kind": kind, "date": stamp, "text": text}


@app.on_event("startup")
def _start_scheduler():
    scheduler.add_job(_generate, "cron", args=["morning"], hour=7, minute=0,
                      id="morning", replace_existing=True)
    scheduler.add_job(_generate, "cron", args=["evening"], hour=20, minute=0,
                      id="evening", replace_existing=True)
    scheduler.start()


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "dashboard.html")


@app.get("/api/status")
def status():
    return {
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "linear": linear_client.configured(),
        "github": github_client.configured(),
        "google": google_client.configured(),
        "google_credentials_present": google_client.credentials_present(),
        "home_city": memory.get_home_city(),
        "travel_city": memory.get_travel_city(),
        "scheduler": [str(j.next_run_time) for j in scheduler.get_jobs()] if scheduler.running else [],
    }


@app.get("/api/briefing/latest")
def latest_briefing():
    files = sorted(BRIEFINGS.glob("*.md"), reverse=True)
    if not files:
        return {"text": None}
    return {"file": files[0].name, "text": files[0].read_text(encoding="utf-8")}


@app.post("/api/briefing/{kind}")
def make_briefing(kind: str):
    if kind not in ("morning", "evening"):
        raise HTTPException(400, "kind must be morning|evening")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "ANTHROPIC_API_KEY not set — add it to .env")
    try:
        return _generate(kind)
    except Exception as e:
        raise HTTPException(500, str(e))


class ChatMsg(BaseModel):
    message: str


@app.post("/api/chat")
def chat(body: ChatMsg):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "ANTHROPIC_API_KEY not set — add it to .env")
    import agent
    try:
        return {"reply": agent.chat(body.message)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/memory")
def memory_all():
    return memory.read_all()


class MemoryBody(BaseModel):
    content: str


@app.put("/api/memory/{name}")
def memory_put(name: str, body: MemoryBody):
    try:
        memory.write(name, body.content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.get("/api/weather")
def api_weather():
    home = memory.get_home_city()
    dest = memory.get_travel_city()
    return {
        "home": weather.get_weather(home) if home else None,
        "destination": weather.get_weather(dest) if dest else None,
    }


@app.get("/api/calendar")
def api_calendar():
    ev = google_client.get_events(days=2)
    return JSONResponse({"connected": ev is not None, "events": ev or []})


@app.get("/api/emails")
def api_emails():
    em = google_client.get_unread_emails()
    return JSONResponse({"connected": em is not None, "emails": em or []})


@app.get("/api/personal")
def api_personal():
    return personal.snapshot()


@app.get("/api/work")
def api_work():
    return {"linear": linear_client.get_work(), "github": github_client.get_work()}


@app.post("/api/google/auth")
def google_auth():
    if not google_client.credentials_present():
        raise HTTPException(400, "Put your OAuth client file at data/credentials.json first (see README)")
    ok = google_client.authorize()
    return {"ok": ok}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8756"))
    print(f"Personal Assistant → http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
