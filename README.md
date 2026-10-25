<!-- sell-kit:start -->
# Agent Ads

[![CI](https://github.com/eliem08/agent-ads/actions/workflows/ci.yml/badge.svg)](https://github.com/eliem08/agent-ads/actions/workflows/ci.yml)

> **Pay to be the option an AI agent recommends, with honest disclosure.**

**Who it's for:** Assistant and agent platforms that want an ad business, and the brands that advertise.

**The problem:** Agents will recommend products, and without a fair auction and clear disclosure, sponsored answers become hidden ads.

**What you get:** A relevance-gated second-price auction with mandatory sponsored labels, single-billed clicks, conversion tracking and budget control.

## Quickstart

Customers receive a release archive with the wheel and the examples. Python 3.10+ and no other dependencies.

```bash
pip install agent_ads-0.1.0-py3-none-any.whl
agent-ads auction examples/campaigns.json --query "hotel in lisbon" --intent hotel
agent-ads demo
```

## Web app and API

Every command is also a JSON API endpoint and a browser form, served by the built-in web app.

```bash
agent-ads-web --port 8000          # then open http://127.0.0.1:8000
docker build -t agent-ads . && docker run -p 8000:8000 -v agent-ads-data:/data agent-ads
```

Endpoints: `POST /api/demo`, `POST /api/auction`, plus `GET /healthz` and `GET /api/spec` (machine-readable field list).
Files are sent as `{"name": ..., "content": ...}`, folders as `{"files": [...]}` or a base64 zip.

## Pricing

Every plan starts with a 14-day free trial. Prices in USD, billed monthly unless noted.

| Plan | Price | Includes |
|---|---|---|
| **Platform Starter** | $499 per month | Up to 1M auctions a month; Disclosure built in; Reporting |
| **Platform Growth** | $1,999 per month | Unlimited auctions; Custom relevance rules; Advertiser console |
| **Rev share** | Custom (% of ad revenue, contact sales) | No fixed fee; Managed demand; Dedicated support |

To start a trial or buy a plan, email **sales@YOUR-DOMAIN.com**.

## Licence

Proprietary. Copyright (c) 2026 eliem08. All rights reserved. Use requires a paid plan or an active trial; see [LICENSE](LICENSE).
<!-- sell-kit:end -->

## What it does

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
- Conversion attribution through agent purchase receipts (pairs with grantgate)
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
