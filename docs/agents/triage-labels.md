# Triage labels → local Status vocabulary

This repo uses a single `Status:` line (one value at a time). Matt's five triage roles
map onto it as follows:

| Status        | Emoji | Matt triage role(s)            |
|---------------|-------|--------------------------------|
| ready         | ⬜    | ready-for-agent                |
| in-progress   | 🔄    | —                              |
| waiting-human | 🧑    | ready-for-human, needs-info    |
| done          | ✅    | —                              |
| wontfix       | 🚫    | wontfix                        |

Lifecycle-only states (no triage-role equivalent): `in-progress` 🔄, `done` ✅.

`needs-triage` is not used — lots are created already specified, not triaged from raw
external reports. `/to-prd` and `/to-issues` create artifacts at `ready` ⬜. The five
roles stay mappable so `/triage` keeps working if adopted later.

The `Status:` line is the **headline** status of a PRD (editorial — the lot's overall
state) or the precise status of a single ticket. It is not a computed rollup.
