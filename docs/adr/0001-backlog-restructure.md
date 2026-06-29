---
status: accepted
date: 2026-06-27
---

# 0001 — Backlog restructure to `.backlog/` per-lot directories (+ `doc/` → `docs/`)

## Context

The backlog lived in a single ~62 KB `doc/backlog.md` (+ ~26 KB `doc/backlog-archive.md`).
With one branch/PR per lot (copilot-instructions §"Project planning"), the monolith was a
recurring merge-conflict surface across the two dev machines, and loading it cost
significant agent context. We also wanted to drive the backlog with the Matt Pocock
engineering skills (`/to-prd`, `/to-issues`, `/triage`), which are issue-tracker-agnostic
and configured per repo (no fork required).

Separately, the documentation tree was `doc/` (singular), diverging from the more common
`docs/` convention and from the reference layout used to wire these skills.

This is the **first ADR** for the project; it also establishes `docs/adr/` as the place
where architectural decisions are recorded going forward.

## Decision

1. **Rename `doc/` → `docs/`.** All documentation moves under `docs/`. Live references
   were updated: backend runtime paths (`backend/routers/chat.py`,
   `backend/services/chat_service.py`), `Dockerfile` (`COPY docs/ ./docs/`), `README.md`,
   `CLAUDE.md`, `.github/copilot-instructions.md`, `.claude/commands/release.md`,
   and internal dev-doc links. `CHANGELOG.md` is an append-only historical ledger and was
   left untouched (its past entries describe the state at the time).

2. **Adopt a per-lot `.backlog/` structure:**
   - **Active lots** are directories — `.backlog/<LOT-ID>/PRD.md` plus one
     `tickets/<NN>-<slug>.md` per ticket (numbered from `01` in dependency order).
   - **Completed lots** are compact `.backlog/archive/<LOT-ID>.md` files (ticket table
     preserved, not split). Deep pre-restructure history is consolidated in
     `.backlog/archive/_legacy-history.md`.
   - A single `Status:` vocabulary (⬜ ready · 🔄 in-progress · 🧑 waiting-human ·
     ✅ done · 🚫 wontfix) maps onto Matt's triage roles.
   - The lot index `.backlog/README.md` is maintained by hand (no generator script);
     it also holds the running estimation **calibration** note.
   - `.backlog/` is a dotfolder: internal working state, not published documentation.

3. **Keep project-specific conventions.** Ticket IDs keep the `BIZ/TEC/CHR-NNN`
   taxonomy (load-bearing, referenced in CHANGELOG/git); the `NN-` file prefix is only
   for ordering. Backlog artifacts are written in **French** (prose) with the skills'
   **English** section headers.

4. **Wire the skills per repo, unmodified.** Config under `docs/agents/*`
   (`issue-tracker.md`, `triage-labels.md`, `domain.md`) plus an `## Agent skills` block
   in `CLAUDE.md`. The Matt Pocock skills stay globally installed and unforked.

5. **Source-of-truth split.** `docs/roadmap.md` remains the **sequencing** source of
   truth; `.backlog/` is the **scope + status** source of truth.

## Consequences

- No more backlog merge conflicts; agents load only the relevant lot.
- `/to-prd` / `/to-issues` work against the local backlog with no upstream fork.
- One-time migration cost; the rename touched code (chat manual/changelog paths) so the
  change ships on a branch + PR, not as a doc-only commit.
- The old `doc/backlog.md` is removed; its content survives in git history and is
  migrated into `.backlog/` (active lots BK3, EDIT-OPS, CREANCES-RAPPEL; archives RF, RR,
  ML, BK2; legacy ledger).
