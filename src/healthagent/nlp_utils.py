from __future__ import annotations
from datetime import date, timedelta
import re
from typing import Optional

WEEKDAYS = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}


def parse_natural_date(text: str, base: Optional[date]=None) -> Optional[str]:
    """Parse simple natural language dates into YYYY-MM-DD.

    Supported forms:
    - "today", "tomorrow"
    - "next <weekday>" e.g. "next monday"
    - "in N days" or "in N weeks"
    - ISO date YYYY-MM-DD
    Returns ISO date string or None if not parsed.
    """
    if not text:
        return None
    txt = text.lower()
    if base is None:
        base = date.today()
    # ISO
    m = re.search(r"(\d{4}-\d{2}-\d{2})", txt)
    if m:
        return m.group(1)
    if "today" in txt:
        return base.isoformat()
    if "tomorrow" in txt:
        return (base + timedelta(days=1)).isoformat()
    # next weekday
    m = re.search(r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", txt)
    if m:
        target = WEEKDAYS[m.group(1)]
        days_ahead = (target - base.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        return (base + timedelta(days=days_ahead)).isoformat()
    # in N days/weeks
    m = re.search(r"in\s+(\d+)\s+days?", txt)
    if m:
        n = int(m.group(1))
        return (base + timedelta(days=n)).isoformat()
    m = re.search(r"in\s+(\d+)\s+weeks?", txt)
    if m:
        n = int(m.group(1))
        return (base + timedelta(weeks=n)).isoformat()
    return None
