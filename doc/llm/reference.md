# Solde ⚖️ — User Assistance Reference

## Purpose

This document is a reference for an LLM chatbot that assists end users of the Solde application. It covers every user-facing workflow, UI navigation, terminology, business rules, role restrictions, administrator actions available to users, and guidance on reporting bugs — written to help the LLM answer questions like "how do I create an invoice?", "why can't I delete this payment?", "I forgot my password — what do I do?", or "I think I found a bug — where do I report it?".

Language of the application interface: French. This document is in English.

---

## Application overview

Solde is a web application for managing the day-to-day finances of a French non-profit association (loi 1901). It handles:
- Client invoicing and payment tracking
- Supplier invoice recording
- Cash register movements
- Bank account transactions and reconciliation
- Payroll (salary slips)
- Double-entry bookkeeping (automated + manual)
- Historical Excel data import

Users access Solde through a web browser. There is no mobile app.

---

## Roles and permissions

Every user has one role. The role determines which menus and features are accessible.

| Role | French label | What they can do |
|---|---|---|
| `secretaire` | Gestionnaire | Contacts, client invoices, payments, bank, cash, salaries |
| `tresorier` | Comptable | Everything a Gestionnaire can do, plus the full Accounting module |
| `admin` | Administrateur | Everything, plus: user management, application settings, system supervision, Excel import |
| `readonly` | Lecture seule | View-only access to most screens |

**Common confusion:** A Gestionnaire cannot access the Accounting menu. If a user says they cannot see "Comptabilité", they probably have the Gestionnaire role.

---

## Login and session

- The access token expires after 60 minutes but is transparently refreshed in the background. The refresh token is valid for 30 days; after that, the user must log in again.
- On first login (or after an admin resets their password), users must change their password immediately. They cannot skip this step.
- **Password rules:** minimum 8 characters, at least one uppercase letter, at least one digit.
- If a user forgets their password, an admin must reset it — there is no self-service "forgot password" link.

---

## Navigation

The left sidebar contains all main navigation links. The visible links depend on the user's role.

Main sections:
- **Tableau de bord** — Dashboard with KPIs and quick-action cards
- **Contacts** — Client and supplier contacts
- **Factures** — Client and supplier invoices
- **Paiements** — Payments received
- **Banque** — Bank transactions, reconciliation, deposits
- **Caisse** — Cash register
- **Salaires** — Employees and payroll
- **Comptabilité** — Journal, chart of accounts, accounting rules, ledger, balance sheet *(Comptable/Admin only)*
- **Paramètres** — Application settings, users, fiscal years *(Admin only)*
- **Administration** — System supervision, Excel import *(Admin only)*

---

## Dashboard

The dashboard shows:
- Key financial indicators for the current fiscal year (income, expenses, balance)
- A list of overdue or nearly-due client invoices
- **Quick-action cards**: create a client invoice, record a payment, add a cash entry — each opens an inline creation dialog

---

## Contacts

**What a contact is:** a person or organisation linked to invoices, payments, and cash movements. A contact can be a client, a supplier, both, or an employee.

**Creating a contact:** click “Nouveau contact”. Only the name is required. Email is optional but required to send invoices by email. Up to 2 additional email addresses can be added in the “Adresses e-mail supplémentaires” section, each with a free-form label (e.g. “Comptabilité”, “Direction”).

**Editing a contact:** click the contact in the list, modify, save. Additional email addresses can be added, edited, or removed in the same form.

**Blocking a client (client indésirable):** available for contacts of type “Client” or “Les deux” only. Activate the “Client indésirable” toggle and save. A red badge “Indésirable” appears in the contact list. Creating an invoice for a blocked contact is prevented — the Valider button is disabled in the form and the wizard stops at the contact selection step with an error. To unblock: deactivate the same toggle and save.

**Contact history:** the “Historique” tab on a contact’s record shows all their invoices and payments. Clicking an invoice opens an inline preview with previous/next navigation.

**Why can't I delete a contact?** Contacts that have invoices or payments linked to them cannot be deleted. Deactivate them instead.

**Searching contacts:** use the search bar at the top of the contact list to filter by name or email.

---

## Client invoices

### Typical workflow

1. Create the invoice (quick wizard from the dashboard, or full form from the Factures menu).
2. Validate to assign a permanent number.
3. Send by email to the client.
4. When payment arrives, record a payment and link it to the invoice — the status updates automatically.
5. If payment is by cheque or cash, create a bank deposit (remise en banque) to trace it.

### Statuses

| Status | Meaning |
|---|---|
| Brouillon | Draft — not yet finalised, can be freely edited |
| Validée | Validated — finalised, awaiting payment |
| Payée | Fully paid |
| Partiellement payée | One or more payments received, balance remaining |
| En retard | Past due date, not paid |
| Irrécouvrable | Written off as a bad debt |

### Quick invoice wizard

The wizard creates and validates a client invoice in 3 steps, accessible from the dashboard or the "+ Facture rapide" button:

1. **Step 1 — Contact**: select the client. If the contact is marked as "Indésirable" (blocked), creation is blocked at this step.
2. **Step 2 — Lines**: add invoice lines (type, description, quantity, unit price). Prices are pre-filled from settings.
3. **Step 3 — Confirmation**: the invoice is created and validated. The confirmation shows the invoice number and client name. Buttons available: "Envoyer par e-mail" (opens the email dialog without closing the wizard), "Nouvelle facture" (restart wizard), "Voir la facture" (open full record).

The wizard always creates invoices in "Validée" status — there is no draft step.

### Creating an invoice (full form)

1. Click "Nouvelle facture" (from Factures menu or dashboard quick card).
2. Select the contact (required). If the contact is blocked, the Valider button is disabled.
3. Set the date. The due date is filled automatically based on the default delay configured in settings.
4. Add invoice lines: choose the type (cours / adhésion / autre), enter a description, quantity, and unit price. Prices are pre-filled from defaults configured in settings.
5. Save as draft (Enregistrer) or finalise (Valider).

The invoice number is assigned automatically when the invoice is validated. It cannot be changed manually.

### Editing an invoice

- **Draft invoices** can be fully edited.
- **Validated invoices**: the due date and notes can be modified, but the lines cannot.

### Deleting an invoice

Only **draft invoices with no payments** can be deleted.

### Sending an invoice by email

Open the invoice → click "Envoyer par e-mail" (or use the button in the wizard confirmation screen).

- If the contact has **one email address**: the recipient field is read-only and pre-filled.
- If the contact has **multiple email addresses**: checkboxes appear, all pre-ticked. The user can untick addresses to exclude them. Sending is blocked if no recipient is selected.

A PDF preview is shown on the right side of the dialog. The PDF is attached automatically to the email. A successful send is recorded in the invoice history.

**Why can't I send?** Either the contact has no email address at all, or the SMTP server is not configured (ask an admin).

### Downloading the PDF

Open the invoice → click "Télécharger PDF".

### Writing off an invoice (irrécouvrable)

Open the invoice → "Passer en irrécouvrable". This marks the invoice as a bad debt and generates accounting entries automatically. The invoice disappears from the unpaid list.

To reverse this: open the invoice → "Annuler le statut irrécouvrable".

### Invoice numbering

The format is configured by an admin (e.g. `2026-001`, `F-2026-001`). The sequence increments automatically. Users cannot manually set the number.

---

## Payments

### Typical workflow

1. Receive the payment (bank transfer, cheque, cash).
2. Click “Nouveau paiement”, enter the amount, date, and reference.
3. Link the payment to the relevant invoice(s) in the “Factures liées” section — the invoice status updates automatically.
4. If payment is by cheque or cash, associate it with a bank deposit (remise en banque).

### Recording a payment

1. Click "Nouveau paiement".
2. Select the contact (optional if the invoice is known).
3. Enter the amount, date, and reference (cheque number, transfer reference, etc.).
4. Optionally link the payment to one or more invoices.
5. Save.

When a payment is linked to an invoice, the invoice status updates automatically.

### Why is an invoice still shown as unpaid after I recorded a payment?

The payment must be explicitly **linked to the invoice**. Check the payment record and verify the invoice is selected in the "Factures liées" section.

### Bank deposits (remises en banque)

A bank deposit groups several payments remitted to the bank at the same time (e.g. a batch of cheques). Create a deposit from Banque → Remises en banque.

---

## Supplier invoices

Record invoices received from suppliers under Factures → Fournisseurs. The workflow is similar to client invoices. You can attach the supplier's PDF file.

---

## Cash register (Caisse)

The cash register tracks physical cash movements.

- **Creating a movement:** click "Nouveau mouvement". Amount: positive = cash in, negative = cash out.
- **Counting (comptage):** enter the physical amount counted. The app computes and displays the discrepancy.
- **Deleting a movement:** only possible if no validated accounting entry is linked to it.

---

## Bank (Banque)

### Typical workflow for a monthly bank statement

1. Export the OFX file from your bank.
2. Import it into Solde (Banque → Importer).
3. Check and correct the automatically detected **categories** on each transaction (pencil icon in the Category column).
4. Reconcile transactions with recorded payments or bank deposits — individually or in bulk.
5. Verify the balance matches the paper statement.

### Importing bank transactions

Import an OFX file exported from your bank: click “Importer”, select the file, confirm. Exact duplicates are skipped automatically. Files with multiple bank accounts are rejected — ask the administrator.

### Correcting a transaction category

Click the pencil icon in the Categorie column to change the detected category. The category determines which accounting entries are generated during reconciliation.

### Reconciliation

Reconciliation links a bank transaction to a payment or deposit recorded in Solde, and generates the corresponding accounting entries.

- **One at a time**: click the “Rapprocher” button on the transaction row, select the matching payment or deposit, confirm.
- **Bulk — all**: click “Tout rapprocher” in the toolbar to reconcile all loaded transactions at once.
- **Bulk — up to a date**: click “Rapprocher avant…”, pick a cutoff date, confirm.

Reconciled transactions show a green “Rapproché” badge and disappear when filtering on “Non rapprochées”.

---

## Salaries (Salaires)

### Typical workflow

1. Retrieve salary slips for the month from the CEA platform (or equivalent).
2. For each employee, create a salary slip under Salaires → Fiches de salaire → Nouvelle fiche.
3. Verify the read-only **Net calculé** field matches the net amount on the bulletin. Any discrepancy indicates a data entry error.
4. Save — accounting entries are generated automatically.
5. Check the monthly summary (“Récapitulatif mensuel”) to verify totals (gross, net, contributions, total cost).

### Employees

Manage employees under Salaires → Employés. Create an employee with name, optional contract details, and optional hourly/monthly rate. Employees cannot be deleted if they have salary slips; deactivate them instead.

### Salary slips

Create a salary slip under Salaires → Fiches de salaire. Select the employee, the period (month/year), enter gross salary, employer contributions, employee contributions (and withholding tax), net pay. For CDD employees, entering hours automatically computes the gross (hours × hourly rate). The “Copier la fiche précédente” button pre-fills contributions from the previous month to save time. Validating a salary slip generates accounting entries automatically.

---

## Accounting (Comptabilité) — Comptable and Admin only

### Journal

Lists all accounting entries. Entries are generated automatically from invoices, payments, cash, bank, and salaries. Manual entries can also be created. Manual entries must be balanced (total debit = total credit).

### Chart of accounts (Plan comptable)

Lists all accounts. Accounts are identified by a number (e.g. `707000`) and a label.

### Accounting rules

Rules define what journal entries are generated automatically when an invoice is validated, a payment is received, etc. Readable by Comptable and Admin; creation, modification, and deletion restricted to Admin only.

### General ledger (Grand livre)

Shows the balance of each account with all its movements. Filterable by account and period.

### Balance sheet and income statement

The Bilan screen shows assets and liabilities. The Résultat screen shows income vs expenses for the fiscal year.

---

## Fiscal years (Exercices)

Each accounting period is a fiscal year. Objects (invoices, entries) are assigned to a fiscal year based on their date.

**Closing a fiscal year** is irreversible. Only do it when all entries for the period are final.

---

## My profile (Mon profil)

Accessible by clicking the username in the top-right corner → Mon profil.

- Change name and email.
- Change password: requires entering the current password first.

---

## Settings (Paramètres) — Admin only

- **Association information**: name, address, SIRET, logo — shown on invoices.
- **Invoice numbering templates**: format of invoice numbers.
- **Default due date**: days added to invoice date to auto-compute the due date.
- **Default prices**: pre-filled unit prices by invoice line type.
- **SMTP**: email sending configuration.
- **Users**: create, edit, deactivate accounts; reset passwords.
- **Fiscal years**: create and manage accounting periods.

---

## Administration — Admin only

### System supervision

Located at Administration → Supervision système. Shows application version, database size, uptime, log viewer, and audit log.

### Excel import

Allows importing historical data from Excel workbooks. End users should not need to use this. Redirect to the administrator.

---

## What the administrator can do for users

When a user cannot resolve a problem themselves, they need to contact their administrator. Here is what requires admin intervention:

### Account and access
- **Create a new user account** — Paramètres → Utilisateurs → Nouvel utilisateur. The admin sets the name, email, username, role, and a temporary password. The user will be forced to change it on first login.
- **Reset a forgotten password** — Paramètres → Utilisateurs → click the user → Réinitialiser le mot de passe. The admin sets a new temporary password and communicates it to the user.
- **Change a user's role** — same screen, edit the role field.
- **Deactivate a user account** — prevents login without deleting the user's history.

### Email sending
- **Configure SMTP** — Paramètres → SMTP. Required for the "Envoyer par e-mail" feature on invoices to work. Fields: host, port, username, password, sender address, TLS/SSL options.
- If SMTP is not configured, sending invoices by email is disabled for all users.

### Invoice numbering and defaults
- **Change the invoice number format** — Paramètres → Association → Numérotation des factures.
- **Change the default due date delay** — Paramètres → Association → Délai d'échéance par défaut (days added to invoice date).
- **Change default unit prices** — Paramètres → Prix par défaut (pre-filled prices per invoice line type).

### Fiscal years
- **Create a new fiscal year** — Paramètres → Exercices → Nouvel exercice. Required at the start of each accounting year.
- **Close a fiscal year** — irreversible operation. All entries for the period must be finalised first.

### Backups
- The administrator is responsible for regular database backups. Users cannot trigger backups themselves.
- If data appears lost or corrupted, contact the administrator immediately — do not attempt to re-enter data.

### System supervision
- The admin can view application logs and the audit trail (Paramètres → Administration → Supervision système) to investigate issues reported by users.

---

## Reporting bugs and technical questions

If a user encounters a behaviour that appears to be a bug (e.g. an error message, a calculation that seems wrong, a missing feature), they should:

1. Note the exact error message or describe the unexpected behaviour precisely.
2. Contact their administrator.
3. The administrator can check the logs at Administration → Supervision système.

For technical issues, feature requests, or confirmed bugs, the source code and issue tracker are available at:

**https://github.com/davidp57/solde**

The administrator or a developer can open a GitHub issue with details of the problem.

---

## Common questions and answers

**Q: I can't see the Comptabilité menu.**
A: Your role is Gestionnaire (secretaire). Only Comptable (tresorier) and Admin roles can access accounting.

**Q: I can't send an invoice by email.**
A: Either the contact has no email address (not even an additional one), or the SMTP server is not configured. Ask your administrator.

**Q: I can send the invoice but I don't see the expected recipient.**
A: Only email addresses linked to the contact (main address or additional addresses added in the contact form) can be selected as recipients. Add the address to the contact first.

**Q: The invoice number was skipped — there's a gap in the sequence.**
A: A number is reserved when an invoice is validated. If a validated invoice was deleted after being tested, the number is consumed. This is normal.

**Q: I recorded a payment but the invoice still shows as unpaid.**
A: The payment must be linked to the invoice. Edit the payment and verify the invoice is selected in the related invoices list.

**Q: I can't create an invoice for a client.**
A: The contact may be marked as "Client indésirable" (blocked). A red "Indésirable" badge appears in the contact list. An admin or manager can remove the block by editing the contact and deactivating the toggle.

**Q: I can't delete a contact.**
A: The contact has invoices or payments linked to them. Deactivate the contact instead of deleting.

**Q: I can't edit the lines of an invoice.**
A: The invoice has already been validated. Validated invoices cannot have their lines changed. Only the due date and notes can be modified.

**Q: The session expired.**
A: Sessions last 30 days. Log in again. If this happens frequently, it is expected behaviour after the refresh token expires.

**Q: I forgot my password.**
A: Contact your administrator — they can reset your password from the user management screen.

**Q: How do I change the invoice numbering format?**
A: Only an administrator can change the invoice number template in Paramètres → Association.

**Q: Bank import gives an error about multiple accounts.**
A: The OFX file contains more than one bank account. Export a single-account OFX file from your bank, or contact your administrator.

**Q: Reconciliation generated wrong accounting entries.**
A: Check the category assigned to the transaction (pencil icon in the Category column). The category determines which accounting rule is applied. Correct the category and re-reconcile.

**Q: Can I undo a fiscal year closing?**
A: No. Closing a fiscal year is irreversible. Make sure all entries are final before closing.

**Q: What happens when I mark an invoice as irrécouvrable?**
A: The invoice is marked as a bad debt. It is removed from the unpaid invoice list. Accounting entries for the loss are generated automatically. The operation can be reversed if needed.

**Q: I see a red "En retard" status on an invoice.**
A: The due date has passed and the invoice is not fully paid. Record a payment to clear it.

**Q: How do I see what a contact owes?**
A: Open the contact's record → the Historique tab shows all their invoices and payments, including outstanding balances.

**Q: I forgot my password / I can't log in.**
A: Contact your administrator. They can reset your password from Paramètres → Utilisateurs. There is no self-service "forgot password" link.

**Q: I need a new user account created.**
A: Contact your administrator. They create accounts from Paramètres → Utilisateurs → Nouvel utilisateur.

**Q: Sending an invoice by email does not work.**
A: Either the contact has no email address, or the SMTP server is not configured. Ask your administrator to check Paramètres → SMTP.

**Q: The default due date or default prices on invoices seem wrong.**
A: These are configurable by an administrator in Paramètres → Association. Ask them to adjust the settings.

**Q: I think I found a bug or something is not working correctly.**
A: Note the exact error message or describe the behaviour precisely, then contact your administrator. For confirmed bugs, the administrator can open an issue on the GitHub repository: https://github.com/davidp57/solde

**Q: I have a feature request or suggestion.**
A: Pass it on to your administrator, who can open a feature request on GitHub: https://github.com/davidp57/solde
