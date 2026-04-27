# Excel Import — Solde ⚖️

---

### Overview

The Excel import feature allows importing historical data from Excel workbooks used before migrating to Solde. It is restricted to **administrators**.

Solde recognises two types of workbooks:

| Type | Processed content | Use |
|---|---|---|
| **Gestion** | Contacts, invoices, payments, cash, bank transactions, auto-generated accounting entries | Historical management data migration |
| **Comptabilite** | Accounting journal only | Historical journal entries migration |

---

### Expected Excel file structure

#### Gestion workbook

| Sheet | Key columns | Notes |
|---|---|---|
| `Contacts` | `Nom`, `Prénom` (opt.), `Email` (opt.) | Created if not already in the database |
| `Factures` | Date, client, amount, number (opt.) | Number is auto-generated if missing |
| `Paiements` | Amount, invoice reference (opt.), contact (opt.) | Reference must match a known invoice |
| `Caisse` | Date, amount | Opening balance or undated rows ignored |
| `Banque` | Date, amount | Descriptive rows without movement ignored |

**Blocking rows:** missing contact name, invalid/zero/missing amount, invalid/missing date, payment with no matchable invoice.

**Blocking ambiguities:** multiple contacts match the same normalized name; multiple invoice candidates for a payment.

#### Comptabilite workbook

| Sheet | Key columns | Notes |
|---|---|---|
| `Journal` | Date, account, label, debit, credit | Reporting sheets ignored |

**Ignored rows:** both debit and credit zero; exact duplicates already in the database; exact re-import of a previously imported file.

---

### Prerequisites

Before any historical import:

1. **Back up the database** (see [administration.en.md](./administration.en.md)).
2. **Create fiscal years** covering all dates in the files.
3. **Set up the chart of accounts** (the import does not create accounts).
4. **Create accounting rules** if the Gestion workbook should auto-generate entries.
5. **Do not modify the source file** between attempts (the hash safeguard detects exact re-imports).

---

### Recommended import order

```
Gestion 2022.xlsx
Gestion 2023.xlsx
Gestion 2024.xlsx
Gestion 2025.xlsx
Comptabilite 2024.xlsx   ← after the matching Gestion year
Comptabilite 2025.xlsx
```

---

### Step-by-step procedure

#### Step 1 — Preview

Preview is **mandatory** before every import.

1. Go to **Administration → Excel Import**.
2. Select the file type: **Gestion** or **Comptabilite**.
3. Choose the Excel file.
4. Click **Preview**.
5. Read the result:
   - **Can execute**: the import can proceed.
   - **Blocked**: one or more errors prevent the import — do not force it.
6. Review sheet by sheet: creation counters, ignored rows, blocking rows, warnings.

**If the preview is blocked:** fix the source file or the import strategy. Never run an import on a blocked state.

#### Step 2 — Execute

If the preview is green, click **Execute import** and wait for completion.

#### Step 3 — Post-import checks

1. Verify that the expected contacts, invoices, payments, and entries are present.
2. Confirm that accounting entries are attached to the correct fiscal years.
3. For a Gestion import, check that no accounting error is surfaced as a warning.

---

### Import history and undo

Solde keeps a reversible log for each import run.

- **Undo an import**: go to import history, select the run, and click **Undo**.
- **Redo after undo**: click **Redo**.

**Undo limitations:** if an imported object was subsequently modified through the application, undo is blocked to prevent inconsistency. In that case, restore a database backup taken before the import.
