"""Google Calendar + Gmail via OAuth (Desktop-app flow).

Setup: put OAuth client JSON at data/credentials.json (see README), then
call authorize() once — a browser opens for consent; token cached in data/.
"""
import datetime as dt
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CREDS_FILE = DATA / "credentials.json"
TOKEN_FILE = DATA / "google_token.json"
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def configured() -> bool:
    return TOKEN_FILE.exists()


def credentials_present() -> bool:
    return CREDS_FILE.exists()


def _creds():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def authorize() -> bool:
    """Run the local OAuth consent flow (opens a browser). Returns True on success."""
    if not CREDS_FILE.exists():
        return False
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    DATA.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())
    return True


def get_events(days: int = 2) -> list | None:
    if not configured():
        return None
    try:
        from googleapiclient.discovery import build
        svc = build("calendar", "v3", credentials=_creds(), cache_discovery=False)
        now = dt.datetime.now(dt.timezone.utc)
        res = svc.events().list(
            calendarId="primary", timeMin=now.isoformat(),
            timeMax=(now + dt.timedelta(days=days)).isoformat(),
            singleEvents=True, orderBy="startTime", maxResults=25,
        ).execute()
        return [
            {"summary": e.get("summary", "(no title)"),
             "start": e["start"].get("dateTime", e["start"].get("date")),
             "end": e["end"].get("dateTime", e["end"].get("date")),
             "location": e.get("location", "")}
            for e in res.get("items", [])
        ]
    except Exception:
        return None


def get_unread_emails(max_results: int = 10) -> list | None:
    if not configured():
        return None
    try:
        from googleapiclient.discovery import build
        svc = build("gmail", "v1", credentials=_creds(), cache_discovery=False)
        res = svc.users().messages().list(
            userId="me", q="is:unread newer_than:2d category:primary",
            maxResults=max_results).execute()
        out = []
        for m in res.get("messages", []):
            msg = svc.users().messages().get(
                userId="me", id=m["id"], format="metadata",
                metadataHeaders=["From", "Subject"]).execute()
            hdrs = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            out.append({"from": hdrs.get("From", "?"), "subject": hdrs.get("Subject", "?"),
                        "snippet": msg.get("snippet", "")[:150]})
        return out
    except Exception:
        return None
