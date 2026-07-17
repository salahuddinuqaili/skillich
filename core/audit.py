"""Taxonomy staleness audit — finds roles whose last_reviewed date is older than a threshold."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from core.taxonomy import TaxonomyLoader


@dataclass
class StaleRole:
    """A role whose AI impact data is older than the requested threshold."""
    function_id: str
    function_name: str
    role_id: str
    role_name: str
    last_reviewed: Optional[str]
    days_since_review: Optional[int]
    ai_impact_level: str
    skill_count: int
    confidence: str


_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _parse_date(raw: str) -> Optional[date]:
    """Parse a YYYY-MM-DD date string; return None on failure."""
    if not raw:
        return None
    m = _DATE_RE.search(raw)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def find_stale_roles(loader: TaxonomyLoader, days: int = 180) -> List[StaleRole]:
    """Return roles whose last_reviewed date is older than *days* from today.

    Roles with a missing or unparseable last_reviewed date are always included
    (treat unknown freshness as stale).
    """
    threshold = date.today() - timedelta(days=days)
    stale: List[StaleRole] = []

    for fn in loader.list_functions():
        for role in loader.list_roles(fn.id):
            full = loader.get_role(fn.id, role.id)
            if full is None:
                continue

            ai = full.ai_impact
            raw_date = ai.last_reviewed if ai else ""
            confidence = ai.confidence if ai else ""
            ai_level = ai.level if ai else "unknown"

            parsed = _parse_date(raw_date)
            days_since: Optional[int] = None

            if parsed is None:
                is_stale = True
            else:
                days_since = (date.today() - parsed).days
                is_stale = parsed < threshold

            if is_stale:
                stale.append(StaleRole(
                    function_id=fn.id,
                    function_name=fn.name,
                    role_id=role.id,
                    role_name=role.name,
                    last_reviewed=raw_date or None,
                    days_since_review=days_since,
                    ai_impact_level=ai_level,
                    skill_count=len(full.skills),
                    confidence=confidence,
                ))

    stale.sort(key=lambda r: (r.days_since_review is None, -(r.days_since_review or 0)))
    return stale
