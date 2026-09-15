# ADR-0001: Use Qdrant as the Vector Store

**Status:** Accepted

## Context

The platform needs a vector store that's free, self-hostable, and portable across future customers, not tied to any one customer's existing infrastructure (e.g., Snowflake Cortex Search would lock the core to Snowflake-using customers specifically).

## Decision

Use Qdrant, self-hosted via Docker. Clean Python client, supports metadata filtering (useful for future multi-tenant separation), not tied to any customer's existing stack.

## Consequences

The core stays portable across verticals and customers. Self-hosting means we own uptime/backups once this is customer-facing — deferred until that's a real problem.

---

**Update (see ADR-0004):** The project's purpose has shifted from a commercial multi-tenant platform to a portfolio/credibility build. Qdrant remains the right choice on its own merits (free, self-hostable, portable, clean Python client), but the multi-tenant-separation and multi-customer-portability reasoning above no longer applies — there is no second customer or tenant to separate.
