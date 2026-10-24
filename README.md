# agent-ads

[![CI](https://github.com/eliem08/agent-ads/actions/workflows/ci.yml/badge.svg)](https://github.com/eliem08/agent-ads/actions/workflows/ci.yml)

> **Google Ads for agents** — pay to be what the agent recommends.

When a user asks their agent "book me a hotel in Lisbon" or "what CRM should
we use?", the agent picks for them. Brands will pay to be in that shortlist.
`agent-ads` is an ad server built for agents — with the guardrails that keep
it from poisoning recommendations.

## What the MVP does

- **Campaigns**: advertiser, offer, intent categories + keywords, max CPC or
  CPA bid, daily budget, landing / action URL
- **Agent-side request**: query, intent, user constraints (e.g. `max_price`),
  and the agent's organic candidates
- **Relevance gate**: a sponsored offer is only eligible if it matches the
  intent, passes hard constraints and clears a relevance threshold —
  irrelevant money can't buy a slot
- **Auction**: generalised second-price, ranked by `bid × quality × relevance`;
  winners pay the minimum needed to keep their rank (never more than their bid)
- **Disclosure**: every sponsored result carries `sponsored: true` + advertiser
  label that the agent must surface to the user
- **Budget pacing** (daily caps), click / conversion **attribution**, campaign report

## Quickstart

```bash
pip install -e .
agent-ads demo
```

## Roadmap

- Agent publisher SDK (MCP tool `ads.get_sponsored(query, intent)`) + revenue share
- Conversion attribution through agent purchase receipts (pairs with agent-plaid)
- Policy engine: no ads for health/finance advice categories without certification

## Development

Zero runtime dependencies; Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m unittest discover -s tests -t .           # unit + CLI smoke tests
ruff check . && ruff format --check .               # lint + format
```

```
agent_ads/core.py       domain logic (pure, importable, fully tested)
agent_ads/__main__.py   CLI (`agent-ads ...` / `python -m agent_ads ...`)
tests/                unit tests + generated CLI smoke tests
```

CI runs lint and tests on Ubuntu and Windows across Python 3.10, 3.12 and 3.13.
Design, data model, trade-offs and production path: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

Part of the [agent-economy](https://github.com/eliem08/agent-economy) portfolio (idea #30).
