# BL-026 — Validation Findings for Excel Imports

## Reminder

This document records the effective result of quantified validation between source Excel files and the data visible in Solde.

Reference method: `doc/dev/bl-026-cadrage-validation-imports-excel.md`.

## Preconditions for this capture

- Database used: `local dev database after reset`
- Capture date: `2026-04-15`
- `Gestion 2024` import: `success with warnings`
- `Gestion 2025` import: `not started`
- `Comptabilité 2024` import: `success with warnings`
- `Comptabilité 2025` import: `not started`
- Fiscal years present in Solde: `2023`, `2024`, and `2025` (created via the `créer le socle comptable` button)
- Prior observations: `test focused on fiscal year 2024 only; fiscal years 2023, 2024, and 2025 all show figures in the Balance screen; for management screens, the capture is done with fiscal year 2024 selected; Bank/Cash visual capture was reconfirmed on 2026-04-16 after setting the system opening date to 2024-08-01 (bank 8 155,62 €; cash 226,79 €)`

## Quick capture during the 2024 test

### Import result to capture immediately

- `Gestion 2024` result: `success with warnings`
- `Gestion 2024` counters: `contacts=66`, `factures=303`, `paiements=308`, `salaires=23`, `caisse=102`, `banque=210`, `écritures=1445`
- `Gestion 2024` ignored / blocked rows: `ignored=5`, `blocked=0`
- `Comptabilité 2024` result: `success with warnings`
- `Comptabilité 2024` counters: `écritures=23`, `ignored=1367`, `blocked=0`
- Warning or error messages to retain: `none`

### Solde checks to capture right after import

- Exact bounds for fiscal year `2024` in Solde: `2024-08-01 -> 2025-07-31` (status `Ouvert`)
- `Factures clients`: visible total `245`, total amount `22357.00 €`, paid amount `22253.00 €`, overdue amount `0.00 €`
- `Factures fournisseurs`: visible total `36`, total amount `4403.81 €`
- `Paiements`: visible total `266`, total amount `23028.00 €`, not yet deposited `2`
- `Caisse`: current balance `54.98 €`, period delta `+54.98 €`, number of entries `103`, visible counts `0`; visual capture confirmed on the `Caisse` screen with fiscal year `2024` selected
- `Banque`: current balance `2674.77 €`, period delta `+2674.77 €`, number of transactions `204`, visible deposit slips `0`; visual capture confirmed on the `Banque` screen with fiscal year `2024` selected
- `Salaires`: visible total `22`, gross `20 509,94 €`, net `15 964,81 €`, total cost `25 221,81 €`; visual capture confirmed on the `Salaires` screen with fiscal year `2024` selected
- `Journal`: number of entries `670`, total debit `184 989,16 €`, total credit `184 989,16 €`, distinct sources `5`; visual capture confirmed on the `Journal comptable` screen with fiscal year `2024` selected
- `Balance`: visible balance rows confirmed on the `Balance générale` screen with fiscal year `2024` selected; the screen still shows no visible global total, so totals `debit 184 989,16 €` and `credit 184 989,16 €` still come from the local database computation
- `Bilan`: total assets `54 196,45 €`, total liabilities `-60 018,54 €`, result `-5 822,09 €`; visual capture confirmed on the `Bilan simplifié` screen with fiscal year `2024` selected; the UI explicitly shows `Total passif : -60 018,54 €` and `Résultat de l'exercice : -5 822,09 €`
- `Résultat`: total expenses `31 052,56 €`, total income `25 230,47 €`, net result `-5 822,09 €`; visual capture confirmed on the `Compte de résultat` screen with fiscal year `2024` selected; the UI shows `Déficit : -5 822,09`

## Fiscal year 2024

- Fiscal-year bounds in Solde: `2024-08-01 -> 2025-07-31` (status `Ouvert`)
- Reference Excel file(s): `Gestion 2024.xlsx` and `Comptabilite 2024.xlsx`

| Domain | Excel figures | Solde figures | Status | Comment |
|---|---|---|---|---|
| Client invoices | `245 invoices; total 22 357,00 €; paid 22 253,00 €; overdue 104,00 € (computed)` | `245 invoices; total 22 357,00 €; paid 22 253,00 €; overdue 0,00 €` | `to clarify` | `count, total, and paid amount match; the remaining 104,00 € correspond to invoices 2024-0277 (78,00 €) and 2025-0010 (26,00 €), still in sent status without due_date, so they are not counted as overdue by the UI` |
| Supplier invoices | `36 FF-* references rebuilt from Banque/Caisse; Banque = 20 rows / 3 811,00 €; Caisse = 16 rows / 592,81 €; total 4 403,81 €` | `36 invoices; total 4 403,81 €; paid 4 403,81 €` | `compliant` | `reconstruction from FF-* references over the 2024-08-01 -> 2025-07-31 range maps exactly to the supplier invoices created in Solde` |
| Payments | `266 payments; total 23 028,00 €; 2 not deposited` | `266 payments; total 23 028,00 €; 2 not deposited` | `compliant` | `count, total, and not-deposited flag match` |
| Cash | `102 imported movements; net flow -171,81 €; system opening outside file = +226,79 €` | `balance 54,98 €; delta +54,98 €; 103 entries; 0 visible counts` | `justified delta` | `visual capture reconfirmed on 2026-04-16; BL-027 applied: Solde displays the cumulative effect of imported flows and an explicit system opening on 2024-08-01` |
| Bank | `203 imported movements; net flow -5 480,85 €; system opening outside file = +8 155,62 €` | `balance 2 674,77 €; delta +2 674,77 €; 204 transactions; 0 visible deposit slips` | `justified delta` | `visual capture reconfirmed on 2026-04-16; BL-027 applied: the visible balance includes the system opening on 2024-08-01 in addition to imported transactions` |
| Salaries | `25 candidate rows in the Aide Salaires tab; 22 distinct salaries after month + employee deduplication; gross 20 509,94 €; net 15 964,81 €; total cost 25 221,81 €` | `22 salaries for fiscal year 2024; gross 20 509,94 €; net 15 964,81 €; total cost 25 221,81 €` | `to clarify` | `screen visual capture confirmed on 2026-04-16; Solde figures match current import logic; methodological caveat: the Excel column still comes from the import parser rather than from an independent workbook reading` |
| Journal | `1 390 journal rows; 1 385 importable rows (5 zero entries ignored); 660 operations (N° column from 0 to 659); debit 181 885,84 €; credit 181 885,84 €` | `670 operations; debit 184 989,16 €; credit 184 989,16 €; 5 distinct sources` | `to clarify` | `the delta does not come from ChangeNum over-splitting: the Journal sheet also yields 660 groups; Solde shows 670 groups because 107 base-only groups and 97 Excel-only groups do not share the same date + account + amount signature, which is a net delta of +10 groups and +3 103,32 €` |
| Trial balance | `debit 181 885,84 €; credit 181 885,84 €; debit balance 87 045,59 €; credit balance 87 045,59 €` | `displayed trial balance visually confirmed on fiscal year 2024; Solde debit/credit totals = 184 989,16 € / 184 989,16 €` | `to clarify` | `the 3 103,32 € delta follows the same pattern as the Journal: some auto-generated management entries, especially supplier flows via 401000 and some salary groups, do not map to a signature identical to the Excel journal` |
| Balance sheet |  | `assets 54 196,45 €; liabilities -60 018,54 €; result -5 822,09 €` | `to clarify` | `screen visual capture confirmed on 2026-04-16; the UI explicitly shows a negative liabilities total, and it still needs to be decided whether this display convention is the one expected for validation` |
| Income statement |  | `expenses 31 052,56 €; income 25 230,47 €; result -5 822,09 €` | `visual capture` | `screen confirmed on 2026-04-16; the UI explicitly labels the result as a deficit` |

### Targeted checks for 2024

- Sensitive accounts or entries verified: `531000 Caisse`, `512100 Compte courant`, `512102 Compte d'épargne`, `110000 Report à nouveau`, `431100 URSSAF`
- Known explicitly ignored rows: `Gestion 2024: 5 ignored, 0 blocking; Comptabilité 2024: 1367 ignored, 0 blocking`
- Technical reconciliation of the 2024 Journal: `the single Journal tab contains 1 385 importable accounting rows, 660 operations (N° column = 0..659), and 181 885,84 € in both debit and credit; the import algorithm also reconstructs 660 groups from that tab, so the Solde delta is not caused by ChangeNum; unmatched groups on the database side come only from auto-generated invoice/payment/salary sources, never from manual groups imported from Comptabilité`
- Deltas still to investigate: `Excel -> Solde reconciliation still needs to be finalized domain by domain; for Journal and Trial Balance, the retained comparison convention between Solde final state and Excel journal must be stated explicitly instead of targeting raw line-by-line identity when the modeling differs; the business convention for overdue client amount must be decided when an invoice remains unpaid without due_date or overdue status; confirm whether the sign of liabilities total in Bilan matches the expected display convention; clarify in the final summary the retained convention for comparing imported treasury flows with the system opening outside the file; confirm whether salaries should be reconciled only on business amounts or also on strict date and grouping conventions`

## Fiscal year 2025

- Fiscal-year bounds in Solde: `...`
- Reference Excel file(s): `...`
- Closing decision for `BL-026`: `fiscal year 2025 is not pursued in this ticket; the next step for strict validation is deferred until after BL-008 framing and the fixes identified as BL-029 are handled`

| Domain | Excel figures | Solde figures | Status | Comment |
|---|---|---|---|---|
| Client invoices |  |  |  |  |
| Supplier invoices |  |  |  |  |
| Payments |  |  |  |  |
| Cash |  |  |  |  |
| Bank |  |  |  |  |
| Salaries |  |  |  |  |
| Journal |  |  |  |  |
| Trial balance |  |  |  |  |
| Balance sheet |  |  |  |  |
| Income statement |  |  |  |  |

### Targeted checks for 2025

- Sensitive accounts or entries verified: `...`
- Known explicitly ignored rows: `...`
- Deltas still to investigate: `...`

## Global summary

- Confidence level for `Gestion` replay: `high on fiscal year 2024 for visible business figures: supplier invoices, payments, bank, and cash are compliant or justified; 2025 validation remains to be done and some business-convention points remain open on client invoices and salaries`
- Confidence level for `Comptabilité` replay: `medium to good on fiscal year 2024: the main statements are coherent and the identified residual deltas partly come from modeling differences between Excel and Solde; 2025 validation is not pursued in BL-026 and the target accounting comparison rule still needs to be fixed explicitly`
- Blocking deltas: `no blocking delta demonstrated at this stage on the 2024 replay; however, there is still no explicit enough reconciliation convention to conclude to raw Excel = Solde accounting convergence on the final journal, which motivates the shift toward BL-008 and BL-029`
- Non-blocking deltas: `overdue client amount depends on the UI convention (`due_date` / `overdue`); 2024 treasury comparison requires integration of the system opening outside the file; 2024 accounting comparison is sensitive to granularity differences (supplier invoice + settlement in Solde vs direct payment in Excel, client-side revenue splitting, salary regroupings)`
- Topics to turn into separate fixes: `BL-029 for client invoice entry and line-driven allocation, including mixed invoices; BL-008 for an iterative validation mode that distinguishes global convergence from validation of the Gestion engine; possibly a dedicated topic if the liabilities display convention in Bilan must be revised; future 2025 validation should be resumed in that new frame rather than extended as-is inside BL-026`