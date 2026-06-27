# Domain docs

Single-context repo (one accounting app, no sub-products).

- **Domain language / data model / business rules**: [`docs/llm/reference.md`](../llm/reference.md)
  (dense reference: full data model, API, business rules, conventions) and the
  architecture deep-dive [`docs/dev/architecture.md`](../dev/architecture.md).
- **Domain gotchas** (Decimal money, phantom `no_entry` bank category, `group_key`,
  WAL backup triplet, accounting engine / Excel import): the **Domain gotchas** section
  of [`CLAUDE.md`](../../CLAUDE.md).
- **Architectural decisions**: [`docs/adr/`](../adr/).

There is no separate `CONTEXT.md` glossary; `docs/llm/reference.md` plays that role.

Skills that read domain context (`improve-codebase-architecture`, `diagnose`, `tdd`)
should read `docs/llm/reference.md` + the CLAUDE.md gotchas and consult `docs/adr/` for
prior decisions in the area being changed.
