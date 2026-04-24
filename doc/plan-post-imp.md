# Post-IMP Follow-Up Plan

## Progress since resuming work

- [x] **`Comptabilite 2025` journal issue closed**: the frontend view now loads up to `1000` entries instead of `500`, which covers the real diagnosed case (`930` entries) without changing the import itself.
- [x] **Historical contact `first_name LAST_NAME` split fixed**: the `Contacts` import now splits `first_name` / `last_name` when the trailing part looks reliably uppercase, while keeping a conservative fallback for ambiguous cases.
- [x] **Contact identity chain realigned**: preview, deduplication, contact creation from invoices, and payment matching now use the same display representation (`first_name last_name`) to avoid false duplicates and mismatches after the split.
- [x] **Historical supplier invoice import delivered**: `Bank` and `Cash` lines carrying an `FF-...` reference now create the supplier contact, the historical supplier invoice, and its linked payment, while still importing the treasury movement and keeping preview/idempotence coherent.

## Problem statement

The IMP initiative is closed, but functional testing has surfaced a new batch of transversal needs:

1. contacts imported from historical files sometimes still keep `first_name LAST_NAME` in the `last_name` field, leaving `first_name` empty;
2. tables currently mix ad hoc sorting and a global text filter, but do not yet offer a full Excel-like behavior across all visible fields;
3. bank deposit entry still does not display the expected total during create/edit flows;
4. manual treasury flows (bank/cash) still do not enforce an invoice reference;
5. the issue raised on `Comptabilite 2025` has now been diagnosed: the import was correct, but the Journal screen truncated display at `500` entries while the real file produces `930`.

## Current observations

- `parse_contact_sheet(...)` now applies a defensive heuristic to split `first_name LAST_NAME` when the uppercase suffix is reliable; ambiguous cases remain intentionally unchanged.
- The backend domain already supports supplier contacts and invoices (`InvoiceType.FOURNISSEUR`, dedicated views and APIs), and the historical import can now create those invoices from `FF-...` references detected in `Bank` and `Cash`, with linked payments and coherent diagnostics.
- Frontend lists already provide:
  - ad hoc sorting through `sortable` columns;
  - a shared generic text filter (`useTableFilter`);
  - sometimes richer business filters (journal, invoices).
  However, there is still no homogeneous sort + per-column filter system across all displayed fields.
- `BankView.vue` currently supports deposit creation, but does not explicitly display the expected total based on selected payments.
- `BankTransactionCreate.reference` and `CashEntryCreate.reference` are still optional.
- The `Comptabilite 2025` point is now fixed in the UI: the Journal screen no longer truncates that real case after the limit was raised to `1000`.

## Proposed approach

Handle the remaining work through five coordinated tracks:

1. **Fix first-name / last-name split for imported contacts**
   - add a safe heuristic for historical contacts when the first name is embedded in the last name field;
   - rely on the observed convention that last names are usually uppercase;
   - keep ambiguous cases on the conservative fallback path.

2. **Roll out sorting and filters to all tables**
   - explicitly target a **global rollout**;
   - extract a shared frontend foundation to avoid re-implementing the logic screen by screen;
   - distinguish between:
     - native PrimeVue sorting on all relevant columns;
     - per-column filters adapted to type (text, date, enum, bool, amount);
     - preserving richer business filters where they go beyond the generic filter.

3. **Harden treasury flows**
   - require an invoice reference, or an explicitly equivalent business rule, for all manual money inflows and outflows;
   - cover bank, cash, and possibly derived flows when the form allows creation outside an invoice;
   - clarify the allowed cases where the reference is not a standard client or supplier invoice.

4. **Improve bank deposit UX**
   - display the expected total in the deposit workflow;
   - verify whether a true deposit editing screen is still missing;
   - if editing does not exist, decide whether the need belongs in the current creation dialog or in a future dedicated editing screen.

## Proposed TODOs

1. [x] Fix the first-name / last-name split in historical import with unit and integration tests.
2. [x] Design and implement historical supplier invoice import, with preview/import/idempotence/tests/docs.
3. Design a shared frontend layer for sorting + per-column filters, then roll it out across all tables.
4. Harden bank/cash schemas, services, and forms to require an invoice reference for manual treasury flows.
5. Add the expected total to the bank deposit flow and decide whether creation/editing needs diverge.
6. Revalidate backend, frontend, documentation, and user procedure after integrating the remaining tracks.

## Recommended order

1. Mandatory bank/cash reference
2. Expected total for deposits
3. Global sorting/filter rollout
4. Final validation and documentation

## Notes / watch points

- The **sorting/filtering on all tables** item is the widest part of the remaining work. It should be treated as a transversal UX effort, not as a series of isolated micro-fixes.
- The `Comptabilite 2025` point is **closed**: the real issue was Journal display truncation, and the corresponding frontend fix is in place.
- **Supplier invoice import** is now connected to the real `FF-...` signals in `Bank` / `Cash`; supplier payments coming from `Cash` also use a dedicated cash accounting trigger to produce coherent entries.
- The first-name / last-name split remains intentionally defensive: the uppercase-last-name convention is useful, but some real cases remain too ambiguous to correct automatically without risk.
