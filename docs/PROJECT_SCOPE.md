# RAG Platform — Project Scope

## Vision

A retrieval-augmented generation project built for portfolio, resume, and interview credibility, not commercial viability. (See ADR-0004 for the full reasoning behind this reframe — it was originally scoped as a sellable multi-tenant platform.) The core idea, a documentation assistant for the modern data stack (dbt, Snowflake, Matillion), stays the same, since it plays directly to existing expertise and is genuinely demoable. The deliverable is a working Slack bot, not a business.

**Channel decision:** Slack is still the build target, now simply because it's the most practical, lowest-friction surface to actually build and demo (per ADR-0003), not because of a customer-acquisition strategy. Microsoft Teams, multi-workspace distribution, and a standalone web app are no longer part of the plan.

## Guardrail

v1 ingests **public documentation only** — official dbt, Snowflake, and Matillion docs, blogs, and community content. Never NCLH's internal dbt repos, schemas, or proprietary configs. This keeps the project cleanly separate from employer IP.

## Architecture Layers

1. **Ingestion** — pulls raw content from a source (a docs site, a PDF folder, a GitHub repo). Each source type is a "connector."
2. **Processing/Chunking** — splits raw content into retrieval-sized chunks with metadata (source, section, last-updated).
3. **Embedding** — converts chunks into vectors. Provider-agnostic so the embedding model can be swapped later.
4. **Vector Store** — stores and searches embeddings (Qdrant).
5. **Retrieval** — takes a user query, embeds it, searches the vector store, returns top-matching chunks.
6. **Persona/Prompt** — config-driven system prompt, tone, and citation style. This is what makes the same core feel like "a dbt assistant" vs. "an HR handbook bot" later, just by swapping a config file.
7. **Orchestration** — scheduled jobs that keep the knowledge base fresh (Airflow). This is also where you build real, legitimate Airflow experience.
8. **Application/Channel** — two distinct surfaces, both calling the same core logic directly (no network API needed): Streamlit as your own internal dev/testing tool for verifying retrieval quality, and a Slack app (via Socket Mode, which avoids needing a public URL or hosting) as the real deliverable people would actually see in a demo.

## Tech Stack (v1)

- **Vector DB:** Qdrant, self-hosted via Docker. Portable, free, good Python client.
- **Embeddings:** Voyage AI (Anthropic's recommended embeddings partner for Claude-based apps), starting with a cost-effective model (e.g., `voyage-3.5`). Pricing is cents-to-low-dollars for a project this size, even with heavy re-embedding during chunking experiments, and this matches the provider relationship a real launch would use rather than prototyping against a smaller local model.
- **Generation:** Claude via API (pay-as-you-go balance, separate from your Pro coding subscription).
- **Orchestration:** Airflow, self-hosted via Docker Compose.
- **Internal dev UI:** Streamlit — your own tool, never seen by anyone else.
- **Deliverable surface:** Slack app via the Bolt SDK, running in Socket Mode (no public endpoint or hosting required).
- **Dev tooling:** Claude Code CLI under your Pro subscription.

## Modularity — What's Abstracted Now vs. Later

To avoid the over-engineering trap, only build the seams that cost nothing extra now:

- **Now:** ingestion as a connector interface (even with only one connector implemented), persona as an external config file (not hardcoded prompts), vector store access behind a thin wrapper, core logic as plain importable functions (not Streamlit or Slack callback code). This costs nothing extra to build correctly and remains a legitimate architecture/craftsmanship signal even though there's no commercial reason to ever add a second connector.
- **Not building, period:** multiple connector types, a network API layer, multi-workspace/multi-tenant support, Microsoft Teams integration, public Slack App Directory listing, billing. These existed only to support a commercial platform that's no longer the plan (see ADR-0004).

## Proposed Repo Structure

```
rag-platform/
├── core/
│   ├── ingestion/        # connector interface + first connector
│   ├── embedding/        # embedding provider interface
│   ├── retrieval/        # vector store wrapper + retriever logic
│   ├── persona/          # persona/prompt config loader
│   └── orchestration/    # Airflow DAGs
├── connectors/
│   └── docs_site/        # v1: dbt/Snowflake/Matillion public docs
├── personas/
│   └── data_stack_assistant.yaml
├── app/
│   ├── streamlit_app.py   # your internal dev/testing tool — never customer-facing
│   └── slack_app.py       # v1 customer-facing surface, Bolt SDK + Socket Mode
├── evals/                # golden Q&A set, retrieval quality checks
└── infra/
    ├── docker-compose.yml  # Qdrant + Airflow local stack
    └── airflow/
```

## Phased Roadmap

- **Phase 0 — Setup:** Docker Compose for Qdrant + Airflow on your Linux box, repo scaffold, Voyage API key, Claude API key.
- **Phase 1 — Core pipeline:** one connector (dbt/Snowflake/Matillion public docs), chunking, embedding, retrieval. Provable end-to-end via command line before any UI or bot exists.
- **Phase 2 — Internal validation (Streamlit):** config-driven persona/prompt, a simple Streamlit chat interface with citations, used by you alone to verify retrieval quality before building the bot. This persona/prompt layer gets reused as-is by the Slack app in Phase 3 — no duplication.
- **Phase 3 — Slack app (the real deliverable):** Bolt SDK in Socket Mode, listens for @mentions or a slash command in a single workspace, calls the same core modules Streamlit uses, replies in-thread with a cited answer.
- **Phase 4 — Orchestration:** Airflow DAG to refresh the knowledge base on a schedule (fetch → chunk → embed → upsert). This is where the Airflow resume line becomes genuinely true.
- **Phase 5 — Evaluation:** a small golden Q&A set (20-30 questions with known-good answers) to measure retrieval quality and catch regressions as you iterate.
- **Phase 6 — Polish & documentation:** a clean README with screenshots, a short demo video or GIF, and the project left in a stable, reliably-demoable state, ready to walk through in an interview or link from a resume/LinkedIn post.

## Explicitly Out of Scope

Multi-tenant auth, billing/payments, fine-tuning, multi-agent orchestration, hosted deployment, Microsoft Teams integration, public Slack App Directory listing/multi-workspace OAuth, a network API layer, a second connector/vertical. None of this serves the credibility goal, so none of it gets built (see ADR-0004).

## Success Criteria

- Retrieval-grounded answers with citations for a representative set of dbt/Snowflake/Matillion questions, delivered through Slack.
- Airflow DAG running the refresh job on a schedule with no manual intervention.
- You can explain every layer of the stack, including why the original commercial-platform framing was reconsidered and reframed, in an interview without hand-waving.
- The project is left in a stable state you can reliably demo on request, not a constantly-moving work in progress.

## Resume/Credibility Tie-ins

This is the actual point of the project now, not a side benefit. Phase 1-3 makes "built a RAG application end-to-end, deployed as a Slack bot" a fully true resume line, including real event-driven bot architecture experience, not just a browser chat demo. Phase 4 makes Airflow a true, demonstrable skill. Phase 5's evaluation framework is what separates "I built a chatbot" from "I built and measured a retrieval system," which is a meaningfully stronger interview answer. And the pivot documented in ADR-0004, recognizing a weak commercial case and reframing rather than forcing it, is itself a legitimate answer to "why isn't this a startup," showing business judgment alongside the technical work.
