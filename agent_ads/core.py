"""Relevance-gated GSP auction for sponsored agent recommendations."""

from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass, field

__all__ = ["Campaign", "AdServer", "relevance"]

RESERVE_CPC = 0.10
MIN_RELEVANCE = 0.35
SLOTS = 2


@dataclass
class Campaign:
    campaign_id: str
    advertiser: str
    offer: str
    intents: set
    keywords: set
    bid: float
    daily_budget: float
    quality: float = 0.7
    attributes: dict = field(default_factory=dict)  # e.g. {"price": 120}
    spent: float = 0.0
    clicks: int = 0
    impressions: int = 0
    conversions: int = 0
    revenue: float = 0.0


def _tokens(s: str) -> set:
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def relevance(c: Campaign, query: str, intent: str) -> float:
    if intent not in c.intents:
        return 0.0
    q = _tokens(query)
    kw = {t for k in c.keywords for t in _tokens(k)}
    overlap = len(q & kw) / max(1, len(q))
    return round(0.4 + 0.6 * min(1.0, overlap * 2), 3)


def _passes(c: Campaign, constraints: dict) -> bool:
    for key, limit in constraints.items():
        if key.startswith("max_"):
            attr = key[4:]
            if attr in c.attributes and c.attributes[attr] > limit:
                return False
        elif key.startswith("min_"):
            attr = key[4:]
            if attr in c.attributes and c.attributes[attr] < limit:
                return False
        elif c.attributes.get(key, limit) != limit:
            return False
    return True


class AdServer:
    def __init__(self):
        self.campaigns: dict[str, Campaign] = {}
        self.impressions: dict[str, dict] = {}
        self._ids = itertools.count(1)

    def add(self, advertiser, offer, intents, keywords, bid, daily_budget, quality=0.7, **attributes) -> Campaign:
        for name, v in (("bid", bid), ("daily_budget", daily_budget)):
            if not (math.isfinite(v) and v > 0):
                raise ValueError(f"{name} must be a finite number > 0, got {v!r}")
        if not 0 < quality <= 1:
            raise ValueError("quality must be in (0, 1]")
        cid = f"C{next(self._ids)}"
        self.campaigns[cid] = Campaign(
            cid, advertiser, offer, set(intents), set(keywords), bid, daily_budget, quality, attributes
        )
        return self.campaigns[cid]

    def auction(
        self, query: str, intent: str, constraints: dict | None = None, organic: list[str] | None = None
    ) -> dict:
        constraints = constraints or {}
        eligible = []
        for c in self.campaigns.values():
            if c.spent + RESERVE_CPC > c.daily_budget:
                continue
            if not _passes(c, constraints):
                continue
            rel = relevance(c, query, intent)
            if rel < MIN_RELEVANCE:
                continue
            eligible.append((c.bid * c.quality * rel, c, rel))
        eligible.sort(key=lambda x: -x[0])
        winners = []
        for i, (_rank_score, c, rel) in enumerate(eligible[:SLOTS]):
            nxt = eligible[i + 1][0] if i + 1 < len(eligible) else 0.0
            price = max(RESERVE_CPC, nxt / (c.quality * rel) + 0.01) if nxt else RESERVE_CPC
            price = round(min(price, c.bid), 2)
            imp_id = f"I{next(self._ids)}"
            self.impressions[imp_id] = {"campaign": c.campaign_id, "cpc": price}
            c.impressions += 1
            winners.append(
                {
                    "impression_id": imp_id,
                    "sponsored": True,
                    "label": f"Sponsored by {c.advertiser}",
                    "offer": c.offer,
                    "cpc": price,
                    "relevance": rel,
                }
            )
        organic = [o for o in (organic or []) if o not in {w["offer"] for w in winners}]
        return {
            "sponsored": winners,
            "organic": organic,
            "disclosure": "Results marked sponsored are paid placements." if winners else "",
        }

    def click(self, impression_id: str) -> float:
        imp = self.impressions[impression_id]
        if imp.get("clicked"):
            return 0.0  # repeat clicks on one impression are free: no double billing, no click-fraud lever
        c = self.campaigns[imp["campaign"]]
        charge = min(imp["cpc"], max(0.0, c.daily_budget - c.spent))
        c.spent = round(c.spent + charge, 2)
        c.clicks += 1
        imp["clicked"] = True
        return charge

    def convert(self, impression_id: str, value: float):
        imp = self.impressions[impression_id]
        if not imp.get("clicked"):
            raise ValueError("conversion without click")
        if imp.get("converted"):
            raise ValueError("impression already converted")
        if not (math.isfinite(value) and value >= 0):
            raise ValueError("conversion value must be a finite number >= 0")
        imp["converted"] = True
        c = self.campaigns[imp["campaign"]]
        c.conversions += 1
        c.revenue += value

    def reset_day(self):
        for c in self.campaigns.values():
            c.spent = 0.0

    def report(self) -> list[dict]:
        rows = []
        for c in self.campaigns.values():
            rows.append(
                {
                    "campaign": c.campaign_id,
                    "advertiser": c.advertiser,
                    "impressions": c.impressions,
                    "clicks": c.clicks,
                    "ctr": round(c.clicks / c.impressions, 3) if c.impressions else 0,
                    "spend": c.spent,
                    "conversions": c.conversions,
                    "roas": round(c.revenue / c.spent, 2) if c.spent else None,
                }
            )
        return rows
