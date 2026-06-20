# ADR-0004: Reframe from Commercial Platform to Portfolio/Credibility Project

**Status:** Accepted

## Context

The project was originally scoped as "WordPress for RAG" — a modular, multi-tenant SaaS platform sold to data teams via Slack (and later Teams), monetized through a freemium plus flat per-workspace fee model. Working through go-to-market strategy surfaced a structural problem: the buyer profile best suited to "buy, not build" (lean data teams inside slow-moving, non-tech-core enterprises) is also the buyer profile with the slowest, most bureaucratic procurement cycles. A solo, part-time, bootstrapped SaaS targeting that buyer was assessed as very unlikely to reach meaningful revenue within an accelerated 1-2 year corporate-exit timeline.

## Decision

Reframe the project's purpose entirely: build for resume, portfolio, and interview credibility rather than commercial viability. Drop all multi-tenant, billing, and multi-workspace distribution work. Keep the Slack app as the centerpiece deliverable — the channel reasoning in ADR-0003 still holds, just for a different reason now (most practical surface to build and demo, not a customer-acquisition strategy). Drop Microsoft Teams as a planned second channel entirely. Retain the connector/persona architecture, since it costs nothing extra to build correctly and remains a legitimate craftsmanship signal, but stop treating "prove it's extensible to other verticals" as a roadmap milestone.

## Consequences

The roadmap simplifies considerably. Effort shifts toward polish, documentation, and reliable demoability rather than business infrastructure. The project's value is realized through career capital (a stronger Solutions Architect / Data Architect candidacy) rather than standalone revenue. If a real commercial opportunity ever materializes later, this decision can itself be revisited and superseded.
