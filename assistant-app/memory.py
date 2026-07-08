"""Read/write layer over the shared memory files in ../assistant/."""
from pathlib import Path

MEMORY_DIR = Path(__file__).resolve().parent.parent / "assistant"

FILES = [
    "profile.md", "important-dates.md", "travel.md", "pantry.md",
    "meal-schedule.md", "shopping-list.md", "work.md",
]


def read_all() -> dict[str, str]:
    out = {}
    for name in FILES:
        p = MEMORY_DIR / name
        out[name] = p.read_text(encoding="utf-8") if p.exists() else ""
    return out


def read(name: str) -> str:
    _validate(name)
    p = MEMORY_DIR / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write(name: str, content: str) -> None:
    _validate(name)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    (MEMORY_DIR / name).write_text(content, encoding="utf-8")


def _validate(name: str) -> None:
    if name not in FILES:
        raise ValueError(f"Unknown memory file: {name}")


def get_home_city() -> str | None:
    """Parse 'Home city:' from profile.md; ignore <FILL IN> placeholders."""
    for line in read("profile.md").splitlines():
        if "home city:" in line.lower():
            val = line.split(":", 1)[1].strip()
            if val and not val.startswith("<"):
                return val.split(",")[0].split("—")[0].strip()
    return None


def get_travel_city() -> str | None:
    """Parse 'Destination:' from travel.md's current-trip section, ignoring comments."""
    text = read("travel.md")
    # strip HTML comments so template examples don't match
    while "<!--" in text:
        pre, _, rest = text.partition("<!--")
        text = pre + rest.partition("-->")[2]
    for line in text.splitlines():
        if "destination:" in line.lower():
            val = line.split(":", 1)[1].strip()
            if val and not val.startswith("<"):
                return val.split(",")[0].strip()
    return None
