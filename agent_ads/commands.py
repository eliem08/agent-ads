"""Stateless commands: read a JSON request, print a JSON decision (also served by the web app)."""

import json

from .core import AdServer


def add_commands(sub):
    c = sub.add_parser("auction", help="run a relevance-gated sponsored auction for an agent query")
    c.add_argument("campaigns", help="JSON list of campaigns")
    c.add_argument("--query", required=True)
    c.add_argument("--intent", required=True)
    c.add_argument("--constraint", action="append", default=[], help="e.g. max_price=200")


def run(a):
    with open(a.campaigns, encoding="utf-8-sig") as fh:
        campaigns = json.load(fh)
    if not isinstance(campaigns, list) or not all(isinstance(c, dict) for c in campaigns):
        raise ValueError("campaigns must be a JSON list of objects")
    srv = AdServer()
    for c in campaigns:
        srv.add(
            c["advertiser"],
            c["offer"],
            c["intents"],
            c["keywords"],
            float(c["bid"]),
            float(c["daily_budget"]),
            float(c.get("quality", 0.7)),
            **c.get("attributes", {}),
        )
    constraints = {}
    for item in a.constraint:
        key, _, value = item.partition("=")
        if not key or not value:
            raise ValueError(f"constraint must look like key=value, got {item!r}")
        try:
            constraints[key] = float(value)
        except ValueError:
            constraints[key] = value
    res = srv.auction(a.query, a.intent, constraints)
    print(json.dumps(res, indent=2))
    return 0 if res["sponsored"] else 1
