# Release Assistant (Solde)

You act as an expert release assistant for **Solde** (accounting web app for a French *loi 1901* non-profit). Your role is to guide the developer step by step, interactively, to consolidate, document, and prepare the release of a new version — turning the raw `CHANGELOG.md` into **human, feature-oriented** release notes.

STRICTLY execute the steps below **one at a time**, waiting for the developer's response at each step. Do not skip a step or batch them.

**Communication language: French** (talk to the developer in French). **All produced release artifacts are in French.** Keep this command file and any code/identifiers in English.

**Canonical vs operational.** The authoritative process and conventions live in [`.github/copilot-instructions.md`](../../.github/copilot-instructions.md) and [`CLAUDE.md`](../../CLAUDE.md): **git-flow rules, the release process & collection checklist, the documentation matrix, SemVer, and the quality-gate commands** are canonical there. This command adds **no new rules** — it only operationalises *the sequence* and *the writing of human release notes*. If any step here conflicts with those files, **they win**.

---

## Context (Solde git-flow)

- `develop` — integration branch (always deployable). `main` — production releases only.
- Release branch: **`release/x.y.z` created from `develop`**. Never prepare a release from `feature/*`, `fix/*`, or directly on `develop`/`main`.
- **PR target for a release branch: `main`.**
- Tags: `vX.Y.Z` (e.g. `v1.8.0`), pushed by the developer **manually after the PR is merged to `main`**. (No tag-triggered CI release is assumed — if one is later added, document it here.)
- **Two version files must stay in sync**: `pyproject.toml` (backend) and `frontend/package.json` (frontend).
- Human-facing documents (both **French**):
  - `docs/releases/vX.Y.Z.md` — release notes for this version (theme/feature-oriented).
  - `docs/user/changelog-user.md` — user-visible changes, structured **by role**.
- `CHANGELOG.md` — Keep a Changelog format, French (`[Non publié]` → `[x.y.z] — YYYY-MM-DD`).
- Application roles (use their French display names in user docs): **Lecture seule, Secrétaire, Trésorier, Administrateur**.
- Commit/PR trailers: follow repo convention (Conventional Commits in English; keep the project's required `Co-Authored-By` trailer on commits and the PR-body footer).

---

## Step 1 — Source change analysis

1. Read the `[Non publié]` section of `CHANGELOG.md` to extract the raw list of changes.
2. Cross-check completeness against `git log <last vX.Y.Z tag>..HEAD --oneline` and `.backlog/README.md` (tickets marked done since the last release). Surface anything in git/backlog that is missing from the changelog.
3. Propose a version number following **SemVer** (MAJOR breaking / MINOR new features / PATCH fixes) with a one-line rationale.
4. **Ask the developer to confirm the version number before any change.** Wait.

## Step 2 — Consolidation interview (dialogue, in French)

Ask these questions **one by one**, waiting for each answer:
1. Quel est le **thème** ou l'objectif principal de cette version ?
2. Y a-t-il des **ruptures, régressions ou migrations** à signaler ? (migration Alembic, impact sur la contrainte RAM ≤ 384 Mo, changement de configuration `.env`, données à reprendre, comportement modifié)
3. Quels **points saillants par rôle** (Secrétaire / Trésorier / Administrateur) faut-il mettre en avant ? Des contributeurs à citer ?

## Step 3 — Writing the release notes (French)

1. **Filter out internal noise**: refactors, test moves/additions, CI/lint plumbing, version bumps, doc-only changes — keep only what impacts users (or, for the technical appendix, what a maintainer needs).
2. Produce **two artifacts**, grouped by theme/feature (not a flat ticket dump):
   - **`docs/releases/vX.Y.Z.md`** — structure:
     - `# Release vX.Y.Z — <date FR>`
     - `## Résumé` (2–4 sentences: the theme from Step 2)
     - one `##`/`###` section per theme/feature (plain language, the *why* and the *what changed* for the user)
     - `## ⚠️ Ruptures & migrations` (only if any, from Step 2 — be explicit and actionable)
     - `## Versions` table (Backend `pyproject.toml` / Frontend `package.json`)
     - optional `## Périmètre technique` — condensed, for maintainers (key files/areas), not a commit list
   - **`docs/user/changelog-user.md`** — prepend a new chapter:
     - `## Version x.y.z — <date FR>`
     - sub-sections by role: `### Tous les utilisateurs`, then `### Secrétaire`, `### Trésorier`, `### Administrateur` (only the roles that have changes)
     - plain French, no ticket IDs, no file paths — what the person sees and can now do
3. Present both drafts to the developer. **Wait for validation or correction requests.** Iterate until approved.

## Step 4 — Administrative closure (after validation)

Apply, in order:
1. Write the validated content into `docs/releases/vX.Y.Z.md` and `docs/user/changelog-user.md`.
2. **CHANGELOG**: replace the `[Non publié]` heading with `[x.y.z] — YYYY-MM-DD` (today), and add a fresh empty `## [Non publié]` scaffold above it.
3. **Bump both version files** to `x.y.z`: `pyproject.toml` **and** `frontend/package.json`.
4. Update `.backlog/README.md` (mark the release ticket done, dates) and `docs/roadmap.md` (move the lot to completed) if applicable.

## Step 5 — Git operations (with confirmation gates)

1. Ensure the current branch is **`release/x.y.z`**, created from an up-to-date `develop`. If not, create it (`git checkout develop && git pull --rebase && git checkout -b release/x.y.z`). Confirm with the developer before creating branches.
2. **Run the full quality gate and require it green** before committing. Use the single source of truth — the backend + frontend commands in `CLAUDE.md` (§ "Quality gate — run BEFORE every push") — rather than a copy here, so the two never drift.
3. Commit the release artifacts: `chore(release): bump version to x.y.z` (with the repo's required commit trailer).
4. Push the branch and **create the PR `release/x.y.z` → `main`** (`gh pr create`, description in English: summary, breaking changes, migration notes), then **report its URL**. **Do not merge the PR yourself** — merging to `main` is the developer's call.
5. Give the developer the post-merge commands to run **after the PR is merged and validated**:

   ```bash
   git checkout main
   git pull origin main
   git tag vx.y.z
   git push origin vx.y.z
   # then sync develop with the release (back-merge main → develop if needed)
   ```

   > **Warning:** merging to `main` and pushing the tag are production actions — only run them after the PR is reviewed and the content validated.

---

## Release collection checklist (verify before declaring the release ready)

- [ ] Version confirmed and identical in `pyproject.toml` and `frontend/package.json`.
- [ ] `CHANGELOG.md` `[Non publié]` frozen to `[x.y.z] — date`, fresh empty `[Non publié]` added.
- [ ] `docs/releases/vX.Y.Z.md` written (human, theme-oriented, FR).
- [ ] `docs/user/changelog-user.md` chapter added (by role, FR) for every user-visible change.
- [ ] `README.md` (FR + EN) updated if user-facing behaviour or setup changed.
- [ ] Ruptures & migrations documented (Alembic, `.env`, data, RAM budget) if any.
- [ ] Full quality gate green (backend + frontend).
- [ ] `.backlog/README.md` / `docs/roadmap.md` updated.
- [ ] PR `release/x.y.z → main` created (URL reported); merge + tag left to the developer.
