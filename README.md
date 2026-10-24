# agent-ads

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
