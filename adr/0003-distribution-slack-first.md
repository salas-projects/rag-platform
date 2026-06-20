# ADR-0003: Slack as the v1 Customer-Facing Surface

**Status:** Accepted

## Context

Candidates considered: standalone web app, installable desktop tool, Slack app, Microsoft Teams app, VS Code extension, CLI tool, embeddable web widget, API-only offering. The target buyer (data engineering teams) already coordinates in Slack daily.

## Decision

Build the v1 customer-facing surface as a Slack app (Bolt SDK, Socket Mode, no public hosting required at single-workspace scale). Streamlit remains an internal dev/testing tool only, never customer-facing. Desktop tool was rejected for the multi-tenant product specifically, since it adds IT-approval and distribution friction that contradicts staying low-touch long-term. Microsoft Teams is a planned second integration once Slack proves the concept.

## Consequences

Adoption can spread organically within a team (one person asks, teammates see the answer) without sales effort. Platform risk shifts to Slack's API/policies, outside our control. Teams-only shops aren't reachable until the second integration ships.

---

**Update (see ADR-0004):** The project's purpose has shifted from a commercial multi-tenant platform to a portfolio/credibility build. The Slack-over-desktop reasoning above still holds for the demo surface, but Microsoft Teams as a second channel is no longer planned.
