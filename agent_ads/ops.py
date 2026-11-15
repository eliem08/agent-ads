"""Operating commands: run the ad server against a persistent store (also served by the web app).

Spend is a ledger: `report` shows what each advertiser owes. Daily budgets reset by themselves when the
date changes, and impressions older than a week are dropped so the store stays small.
"""

import itertools
import json
import os
from dataclasses import asdict
from datetime import date, timedelta

from .core import AdServer, Campaign

OPS = ("campaign-add", "campaign-pause", "serve", "click", "convert", "report")
KEEP_DAYS = 7


class AdsError(ValueError):
    pass


def load(path: str, today: date | None = None) -> AdServer:
    today = today or date.today()
    srv = AdServer()
    srv.paused, srv.billed = set(), {}
    try:
        with open(path, encoding="utf-8-sig") as fh:
            doc = json.load(fh)
    except FileNotFoundError:
        srv.day = today.isoformat()
        return srv
    if not isinstance(doc, dict) or "campaigns" not in doc:
        raise AdsError(f"{path}: not an agent-ads store")
    for k, v in doc["campaigns"].items():
        v["intents"], v["keywords"] = set(v["intents"]), set(v["keywords"])
        srv.campaigns[k] = Campaign(**v)
    cutoff = (today - timedelta(days=KEEP_DAYS)).isoformat()
    srv.impressions = {k: v for k, v in doc.get("impressions", {}).items() if v.get("day", "") >= cutoff}
    srv.paused = set(doc.get("paused", []))
    srv.billed = dict(doc.get("billed", {}))  # lifetime, unlike Campaign.spent which resets daily
    srv._ids = itertools.count(int(doc.get("next_id", 1)))
    srv.day = doc.get("day", today.isoformat())
    if srv.day != today.isoformat():  # a new day: budgets refill
        srv.reset_day()
        srv.day = today.isoformat()
    return srv


def save(srv: AdServer, path: str):
    next_id = next(srv._ids)
    srv._ids = itertools.count(next_id)
    campaigns = {}
    for k, c in srv.campaigns.items():
        campaigns[k] = {**asdict(c), "intents": sorted(c.intents), "keywords": sorted(c.keywords)}
    doc = {
        "campaigns": campaigns,
        "impressions": srv.impressions,
        "paused": sorted(srv.paused),
        "billed": srv.billed,
        "next_id": next_id,
        "day": srv.day,
    }
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    os.replace(tmp, path)


def pairs(items, what: str) -> dict:
    """["price=120", "brand=acme"] -> {"price": 120.0, "brand": "acme"}"""
    out = {}
    for item in items or []:
        k, sep, v = item.partition("=")
        if not sep or not k.strip():
            raise AdsError(f"{what} must look like name=value, got {item!r}")
        try:
            out[k.strip()] = float(v)
        except ValueError:
            out[k.strip()] = v.strip()
    return out


def add_ops(sub):
    store = os.environ.get("AGENT_ADS_STORE", "ads.json")
    p = sub.add_parser("campaign-add", help="an advertiser buys sponsored placement for an offer")
    p.add_argument("advertiser")
    p.add_argument("offer")
    p.add_argument("--intents", nargs="+", required=True, help="e.g. buy compare")
    p.add_argument("--keywords", nargs="+", required=True)
    p.add_argument("--bid", type=float, required=True, help="max cost per click, USD")
    p.add_argument("--daily-budget", type=float, required=True)
    p.add_argument("--quality", type=float, default=0.7, help="0-1, from your review of the offer")
    p.add_argument("--attr", action="append", default=[], help="offer attribute, e.g. price=120 (repeatable)")
    sub.add_parser("campaign-pause", help="stop serving a campaign").add_argument("campaign_id")
    p = sub.add_parser("serve", help="an agent asks for sponsored results for a user query (prints JSON)")
    p.add_argument("--query", required=True)
    p.add_argument("--intent", required=True)
    p.add_argument("--constraint", action="append", default=[], help="user constraint, e.g. max_price=150")
    p.add_argument("--organic", nargs="*", default=[], help="the agent's own unpaid picks, kept apart")
    sub.add_parser("click", help="the user chose a sponsored result: bill the click").add_argument("impression_id")
    p = sub.add_parser("convert", help="the click led to a purchase")
    p.add_argument("impression_id")
    p.add_argument("--value", type=float, required=True)
    sub.add_parser("report", help="impressions, clicks, spend and return per campaign")
    for name in OPS:
        sub.choices[name].add_argument("--store", default=store)


def run_ops(a) -> int:
    try:
        srv = load(a.store)
        _run(srv, a)
        save(srv, a.store)
        return 0
    except ValueError as e:  # AdsError and the engine's own validation
        print(f"refused: {e}")
        return 1


def _imp(srv: AdServer, imp_id: str) -> dict:
    if imp_id not in srv.impressions:
        raise AdsError(f"no impression {imp_id!r} (impressions expire after {KEEP_DAYS} days)")
    return srv.impressions[imp_id]


def _run(srv: AdServer, a):
    c = a.cmd
    if c == "campaign-add":
        camp = srv.add(
            a.advertiser, a.offer, a.intents, a.keywords, a.bid, a.daily_budget, a.quality, **pairs(a.attr, "attr")
        )
        print(f"{camp.campaign_id}: {camp.advertiser} bids ${camp.bid:.2f}/click, ${camp.daily_budget:.2f}/day")
    elif c == "campaign-pause":
        if a.campaign_id not in srv.campaigns:
            raise AdsError(f"no campaign {a.campaign_id!r}")
        srv.paused.add(a.campaign_id)
        print(f"{a.campaign_id} paused")
    elif c == "serve":
        live = srv.campaigns
        srv.campaigns = {k: v for k, v in live.items() if k not in srv.paused}
        try:
            result = srv.auction(a.query, a.intent, pairs(a.constraint, "constraint"), a.organic)
        finally:
            srv.campaigns = live
        for w in result["sponsored"]:
            srv.impressions[w["impression_id"]]["day"] = srv.day
        print(json.dumps(result, indent=2))
    elif c == "click":
        cid = _imp(srv, a.impression_id)["campaign"]
        charge = srv.click(a.impression_id)
        srv.billed[cid] = round(srv.billed.get(cid, 0.0) + charge, 2)
        print(f"billed ${charge:.2f}")
    elif c == "convert":
        _imp(srv, a.impression_id)
        srv.convert(a.impression_id, a.value)
        print(f"conversion of ${a.value:,.2f} recorded")
    else:
        print(
            f"{'campaign':<9}{'advertiser':<18}{'impr':>6}{'clicks':>7}{'today':>8}{'billed':>9}{'conv':>6}{'ROAS':>7}"
        )
        for r in srv.report():
            billed = srv.billed.get(r["campaign"], 0.0)
            roas = f"{srv.campaigns[r['campaign']].revenue / billed:.1f}x" if billed else "-"
            state = " (paused)" if r["campaign"] in srv.paused else ""
            print(
                f"{r['campaign']:<9}{r['advertiser']:<18}{r['impressions']:>6}{r['clicks']:>7}"
                f"{r['spend']:>8.2f}{billed:>9.2f}{r['conversions']:>6}{roas:>7}{state}"
            )
        if not srv.campaigns:
            print("no campaigns yet")
