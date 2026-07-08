"""Parse memory files into structured data for the Personal tab."""
import datetime as dt
import re

import memory


def _tables(text: str) -> list[list[dict]]:
    """All markdown tables in text, each as a list of row-dicts."""
    tables, current = [], None
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue  # separator row
            if current is None:
                current = {"header": cells, "rows": []}
            else:
                current["rows"].append(dict(zip(current["header"], cells)))
        elif current:
            tables.append(current["rows"])
            current = None
    if current:
        tables.append(current["rows"])
    return tables


def upcoming_dates(days_ahead: int = 45) -> list[dict]:
    today = dt.date.today()
    out = []
    for table in _tables(memory.read("important-dates.md")):
        for row in table:
            raw = next(iter(row.values()), "")
            m = re.match(r"(\d{1,2})-(\d{1,2})", raw)
            if not m:
                continue
            month, day = int(m.group(1)), int(m.group(2))
            try:
                nxt = dt.date(today.year, month, day)
                if nxt < today:
                    nxt = dt.date(today.year + 1, month, day)
            except ValueError:
                continue
            days = (nxt - today).days
            if days > days_ahead:
                continue
            vals = list(row.values())
            out.append({
                "date": nxt.isoformat(),
                "days": days,
                "occasion": vals[1] if len(vals) > 1 else "",
                "person": vals[2] if len(vals) > 2 else "",
                "location": vals[3] if len(vals) > 3 else "",
                "nudge": vals[4] if len(vals) > 4 else "",
                "far": "far" in (vals[3] if len(vals) > 3 else "").lower(),
            })
    return sorted(out, key=lambda x: x["days"])


def pantry_gaps() -> list[dict]:
    out = []
    for table in _tables(memory.read("pantry.md")):
        for row in table:
            vals = list(row.values())
            status = (vals[1] if len(vals) > 1 else "").lower()
            if status in ("low", "out"):
                out.append({"item": vals[0], "status": status,
                            "notes": vals[2] if len(vals) > 2 else ""})
    return sorted(out, key=lambda x: x["status"])  # low before out? 'l'<'o' yes


def meals_today() -> dict | None:
    day = dt.date.today().strftime("%a")  # Mon, Tue…
    for table in _tables(memory.read("meal-schedule.md")):
        for row in table:
            vals = list(row.values())
            if vals and vals[0].lower().startswith(day.lower()):
                return {"day": vals[0],
                        "breakfast": vals[1] if len(vals) > 1 else "",
                        "lunch": vals[2] if len(vals) > 2 else "",
                        "dinner": vals[3] if len(vals) > 3 else ""}
    return None


def travel_summary() -> dict:
    text = memory.read("travel.md")
    while "<!--" in text:  # strip template comments
        pre, _, rest = text.partition("<!--")
        text = pre + rest.partition("-->")[2]
    current = re.search(r"## Current trip\s*\n(.*?)(?=\n## |\Z)", text, re.S)
    upcoming = re.search(r"## Upcoming trips\s*\n(.*?)(?=\n## |\Z)", text, re.S)
    clean = lambda m: (m.group(1).strip() if m else "") or "None"
    return {"current": clean(current), "upcoming": clean(upcoming)}


def snapshot() -> dict:
    return {
        "dates": upcoming_dates(),
        "pantry_gaps": pantry_gaps(),
        "meals_today": meals_today(),
        "travel": travel_summary(),
        "shopping_list": memory.read("shopping-list.md"),
    }
