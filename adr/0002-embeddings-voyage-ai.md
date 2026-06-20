# ADR-0002: Use Voyage AI for Embeddings

**Status:** Accepted

## Context

Anthropic doesn't offer its own embedding model. The initial plan was a local open-source model for zero marginal cost, but that prototypes against different infrastructure than what a real launch would use.

## Decision

Use Voyage AI, Anthropic's recommended embeddings partner for Claude-based apps, starting with a cost-effective model. Cost for a project this size is cents to low dollars, even with heavy re-embedding during development.

## Consequences

Development mirrors production reality from day one — no later migration or re-testing step. A local model remains a documented, swappable option later if cost-at-scale or offline use becomes a real requirement.
