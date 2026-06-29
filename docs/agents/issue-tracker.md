# Issue tracker: local `.backlog/` directory

Lots, PRDs, and tickets for this repo live as markdown under `.backlog/` (a dotfolder:
internal working state, ignored by doc-site generators — not published documentation).

## Conventions

- One lot per directory: `.backlog/<LOT-ID>/`
- The PRD is `.backlog/<LOT-ID>/PRD.md` (Matt's PRD template; no separate `## Goal`)
- Tickets are `.backlog/<LOT-ID>/tickets/<NN>-<slug>.md`, numbered from `01` in dependency order
- **Ticket IDs keep the project taxonomy** (`BIZ-NNN` business / `TEC-NNN` technical /
  `CHR-NNN` chore). The `<NN>-` file prefix is only for ordering inside the lot — it is
  not the ticket ID. A new ticket takes the next free number in the project sequence.
- Status is a `Status:` line near the top of each PRD/ticket file (see `triage-labels.md`)
- The lot index (recap table of every lot + status) is `.backlog/README.md`, maintained by hand
- Completed lots are compacted into `.backlog/archive/<LOT-ID>.md` (ticket table preserved,
  not split) once closed > 3 days. The deep historical ledger is `.backlog/archive/_legacy-history.md`
- Sequencing is **not** here — it lives in `docs/roadmap.md`. `.backlog/` owns **scope + status**.

## When a skill says "publish to the issue tracker"

- A PRD → write `.backlog/<LOT-ID>/PRD.md`, create the directory if needed, and add a row
  to the **Lots actifs** table in `.backlog/README.md`.
- An issue → write `.backlog/<LOT-ID>/tickets/<NN>-<slug>.md`.
- New artifacts are created at `Status: ⬜ ready`.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user normally passes the lot ID or ticket path
directly (e.g. `BK3` or `.backlog/BK3/tickets/02-mirror-nonregenerable-only.md`).

## Lot lifecycle

1. `/to-prd` creates `.backlog/<LOT-ID>/PRD.md` (⬜ ready) + a README row.
2. `/to-issues` splits it into `tickets/<NN>-<slug>.md` (⬜ ready), blockers first.
3. Work flips statuses (⬜ → 🔄 → ✅) on the ticket/PRD and in the README index.
4. After a lot is done > 3 days, compact it to `.backlog/archive/<LOT-ID>.md` and update the index.

One branch + one PR per lot (not per ticket), targeting `develop`. Branch named on the
PRD `Branch:` line (`feature/<id>` or `fix/<id>`).
