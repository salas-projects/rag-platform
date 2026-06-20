# RAG Platform

A modular retrieval-augmented generation platform — "WordPress for RAG." The core is generic; each vertical ("theme") is a connector + persona config, not a rewrite.

**v1 vertical:** a documentation assistant for the modern data stack (dbt, Snowflake, Matillion), delivered as a Slack app.

See `/docs/PROJECT_SCOPE.md` for the full architecture and roadmap, `/PROCESS.md` for how work gets tracked and reviewed, and `/adr/` for architecture decisions and their rationale.

## Guardrail

This project ingests public documentation only. No proprietary employer data, repos, or credentials are used anywhere in this codebase.
