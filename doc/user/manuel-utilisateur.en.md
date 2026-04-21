# User Manual - Step-by-Step Guide

## Purpose of this guide

This consolidated text version of the user manual covers the most useful everyday workflows in Solde. It helps users get started with the application, from signing in to reviewing the main accounting screens, including contacts, invoices, payments, cash, bank workflows, and Excel imports.

This document describes the screens currently available in the application. Annotated screenshots remain a separate work item and will be added later, once the interface is stable enough to avoid unnecessary documentation churn.

## How to use this manual

You can read this guide in two ways:

1. from start to finish if you are discovering Solde for the first time;
2. chapter by chapter if you only need to complete one specific task.

For each chapter, you will find:

- the goal of the screen or workflow;
- useful prerequisites;
- the steps to follow;
- the expected result;
- the points to watch before moving on.

## Quick paths by need

- If you are just getting started with Solde: read `Sign in`, `Find your way around the application`, then `Manage contacts`.
- If you need to invoice a client: read `Manage contacts`, then `Create and follow a client invoice`, then `Review and follow client payments`.
- If you need to record a supplier purchase: go directly to `Manage supplier invoices`.
- If you want to review treasury data: read `Manage cash` and `Manage bank workflows and deposits`.
- If you need to replay historical Excel data: read the Excel import chapter, then the companion guide [import-excel-et-reinitialisation.en.md](./import-excel-et-reinitialisation.en.md).
- If you want to understand an accounting figure: go to `Review the main accounting screens`.

## Scope of this version

This version covers:

1. sign-in;
2. navigation landmarks;
3. contact management;
4. client invoice creation and follow-up;
5. client payment review and follow-up;
6. supplier invoices;
7. cash management;
8. bank workflows and deposits;
9. Excel import;
10. the main accounting screens;
11. a short FAQ;
12. a simple business glossary.

It does not yet cover annotated screenshots or a final print-oriented layout.

## Before you start

### Useful companion guides

- For installation and initial prerequisites, read [installation.md](./installation.md).
- For historical imports, resets, reversible history, and pre-replay checks, read [import-excel-et-reinitialisation.en.md](./import-excel-et-reinitialisation.en.md).

### What you need

- an active user account;
- your username and password;
- at least one fiscal year already created by an administrator;
- if you want to create an invoice, the client contact must already exist in Solde.

### What you see depending on your role

The main management screens are available from the side menu or the mobile menu. Some administration screens, such as `Settings`, are only visible to administrator accounts.

## 1. Sign in

### Goal

Access the application with your user account.

### Steps

1. Open the Solde sign-in page.
2. Enter your username in the `Identifiant` field.
3. Enter your password in the `Mot de passe` field.
4. Click `Se connecter`.

### Expected result

If the credentials are valid, Solde opens the dashboard.

### If there is a problem

- If a message says that the username or password is incorrect, check your input and try again.
- If a message says that the server is unreachable, this is more likely a technical or network problem.

## 2. Find your way around the application

### Goal

Understand where to find the main everyday screens.

### Useful landmarks

- The main menu gives access to `Dashboard`, `Contacts`, `Client invoices`, `Payments`, `Bank`, `Cash`, and the accounting screens.
- On mobile, the menu opens through the button at the top of the screen.
- Your username and role are visible either in the side area or in the top bar depending on screen size.
- The logout button cleanly ends the session.

### Dashboard

The dashboard provides the most useful starting points:

- bank balance;
- cash balance;
- number and amount of unpaid invoices;
- number of overdue invoices;
- number of payments not yet deposited in bank;
- current fiscal year;
- current fiscal year result.

Start with this screen whenever you want a quick overall view before entering or reviewing data.

## 3. Manage contacts

### Goal

Create, find, and update people or organizations linked to the association.

### When to use this screen

Use the `Contacts` screen to:

- create a new client;
- register a supplier;
- update an e-mail, phone number, or address;
- review a contact history.

### Create a contact

1. Open `Contacts` in the main menu.
2. Click `Nouveau contact`.
3. Choose the contact type: `Client`, `Fournisseur`, or `Client & Fournisseur`.
4. Fill in at least the `Nom`.
5. Complete `Prénom`, `E-mail`, `Téléphone`, `Adresse`, and `Notes` if needed.
6. Click `Enregistrer`.

### Edit a contact

1. In the list, find the intended contact.
2. Use search or the type filter if needed.
3. Click the row edit button.
4. Adjust the required information.
5. Click `Enregistrer`.

### Review a contact history

1. From the contacts list, click the history button on the relevant row.
2. Solde displays a contact sheet with:
   - the contact details;
   - total invoiced amount;
   - total paid amount;
   - remaining due amount;
   - the invoice list;
   - the associated payment list.

This screen is useful to answer a simple question: where does this contact currently stand in invoicing and payment follow-up?

### Expected result

The contact becomes available in lookup lists, especially when creating an invoice.

### Points to watch

- If the contact must receive invoices, check that it was created with a compatible type: `Client` or `Client & Fournisseur`.
- The `Notes` field is useful for practical context, but it does not replace mandatory invoicing information.

## 4. Create and follow a client invoice

### Goal

Create a client invoice, review its status, and use the available follow-up actions.

### Prerequisites

- the client contact already exists in Solde;
- you know the invoice date and, if needed, the due date;
- you have the invoice line details to enter.

### Create a client invoice

1. Open `Factures clients` in the main menu.
2. Click `Nouvelle facture`.
3. Select the relevant `Contact`.
4. Fill in the invoice `Date`.
5. Fill in the `Échéance` if needed.
6. Optionally choose a `Type` of invoice if it helps you classify invoices.
7. Add a general `Description` if needed.
8. In the `Lignes` area, add one or more invoice lines.
9. For each line, enter:
   - description;
   - quantity;
   - unit price.
10. Check the automatically computed total.
11. Click `Enregistrer`.

### Find an invoice

The `Factures clients` screen lets you filter the list by:

- status;
- year;
- free-text search.

The list notably displays number, date, contact, type, total, and status.

### Available actions on an invoice

From the invoice row, you can:

- open invoice history;
- record a payment;
- edit the invoice;
- generate a PDF;
- send the invoice by e-mail;
- duplicate the invoice;
- delete the invoice.

### Read invoice history

Invoice history gives you a quick view of:

- total invoiced amount;
- amount already paid;
- remaining due amount;
- payments linked to the invoice.

From this window, you can also record a new payment as long as some amount is still due.

### Expected result

The invoice appears in the client portfolio with its status and total. If payments are linked to it, the history shows what has already been received and what remains to be collected.

### Points to watch

- An invoice without useful lines is not actionable: check both description and amounts.
- If you want to send the invoice by e-mail, make sure the contact has a usable e-mail address.
- The invoice status evolves according to linked payments.

## 5. Review and follow client payments

### Goal

Review payments already recorded, follow settlements by invoice or by contact, and monitor what still has to be deposited to the bank.

### Record a client payment

The standard workflow is to record `Espèces` and `Chèque` payments from the client invoice.

1. Open `Factures clients`.
2. Find the invoice to settle.
3. Click `Enregistrer un règlement` from the row or from the invoice history.
4. Check the proposed date and adjust it if needed.
5. Enter the amount received.
6. Choose the payment mode: `Espèces` or `Chèque`.
7. If you record a cheque, enter the cheque number.
8. Add a reference or note if needed.
9. Click `Enregistrer`.

`Virements` follow another entry point: they must be observed from the bank statement and then matched to the correct payment.

### Effect depending on payment mode

- `Espèces`: the payment is recorded and appears immediately in the `Caisse` journal.
- `Chèque`: the payment is recorded but remains pending for a manual bank deposit.

This makes the distinction clear between actual cash collection and the later bank deposit, especially for cheques and cash deposits.

### Review payments for an invoice

1. Open `Factures clients`.
2. On the intended invoice, click the history button.
3. Check the list of linked payments, with date, amount, payment mode, and cheque number when applicable.

### Review payments for a contact

1. Open `Contacts`.
2. Open the contact history.
3. Review the `Paiements` section to see payments linked to that contact.

### Review all payments

1. Open `Paiements` in the main menu.
2. Use the `À remettre en banque` filter if you want to focus on payments that have not yet been deposited.

The payments list is useful to:

- review all recent settlements;
- confirm whether a cheque is still pending deposit;
- find a payment using its reference or note.

### Expected result

You can see which payments were already recorded, how they are linked to invoices, and which ones still require a bank deposit.

### Points to watch

- Do not try to enter a bank transfer manually from the invoice if the intended workflow is bank-based reconciliation.
- For cash payments, also check the `Caisse` journal if you want to verify the treasury impact.

## 6. Manage supplier invoices

### Goal

Record supplier invoices and keep supporting files linked to the right expense.

### Create a supplier invoice

1. Open `Factures fournisseurs`.
2. Click `Nouvelle facture`.
3. Select the supplier contact.
4. Enter the invoice date.
5. Enter the supplier reference if you have one.
6. Enter the amount.
7. Add a description if needed.
8. Save the invoice.

### Attach a supplier file

1. From the supplier invoices list, locate the invoice.
2. Use the attachment action.
3. Select the PDF or image file.
4. Confirm the upload.

### Expected result

The supplier invoice appears in the list and the supporting file is linked to it when uploaded.

### Points to watch

- Check that the supplier contact exists before entering the invoice.
- Use a meaningful description to make later review easier.

## 7. Manage cash

### Goal

Review cash movements, current cash balance, and physical counts.

### Useful screens

The `Caisse` screen gives access to:

- the cash journal;
- physical cash counts;
- the current running balance.

### Review the cash journal

1. Open `Caisse`.
2. Review incoming and outgoing entries.
3. Check references, descriptions, and running balance.

Cash payments recorded from client invoices appear here automatically.

### Perform a physical count

1. Open the count tab or section.
2. Enter the number of notes and coins by denomination.
3. Save the count.
4. Compare the physical total with the theoretical balance shown by Solde.

### Expected result

You can compare actual cash on hand with the system balance and investigate discrepancies.

## 8. Manage bank workflows and deposits

### Goal

Review bank transactions, follow deposits, and process bank-originated settlement flows.

### Bank screen

The `Banque` screen lets you:

- review imported or recorded bank transactions;
- create or confirm deposits;
- process bank-driven reconciliation workflows.

### Review pending deposits

1. Open `Banque`.
2. Review the transactions and deposit-related areas.
3. Use filters if needed to focus on unprocessed items.

### Confirm a deposit

When cheques or cash must be deposited, Solde keeps the payment and the bank event distinct. Review the deposit workflow carefully before confirming it.

### Expected result

Bank history remains readable and linked to the actual treasury steps.

## 9. Use Excel import

### Goal

Preview, execute, and review historical imports from Excel files.

### Where to start

Open `Import Excel` from the menu.

### Recommended order

1. Choose the right import type.
2. Select the file.
3. Run the preview.
4. Review warnings and blocking lines.
5. Execute the import only if the preview is acceptable.
6. Review the result summary and import history.

### Expected result

You understand what the import will do before execution and can use the import history to review, undo, or redo when applicable.

For more detail, see the dedicated guide: [import-excel-et-reinitialisation.en.md](./import-excel-et-reinitialisation.en.md).

## 10. Review the main accounting screens

### Goal

Understand what the main accounting screens are used for.

### Main screens

- `Journal`: detailed accounting entries
- `Balance`: account-by-account totals
- `Grand livre`: detailed account history
- `Résultat`: current fiscal year income statement
- `Bilan`: simplified balance sheet
- `Règles comptables`: accounting rules used by Solde
- `Exercices`: fiscal years and lifecycle actions

### Expected result

You know where to look depending on whether you need a detailed transaction view, an aggregated balance, or a fiscal-year overview.

## 11. Short FAQ

### I cannot see a screen shown in the manual

Your role may not allow access to that section, or the manual may refer to a screen available only on a larger viewport or a different menu state.

### A payment is visible on the invoice but not yet in bank

This is normal for cheques and cash workflows: the collection step and the bank deposit step are separate.

### An import looks blocked

Do not force the import. Re-read the preview, identify the blocking lines, and verify the database state and the targeted fiscal year.

## 12. Simple glossary

- `Fiscal year`: accounting period used to group accounting activity.
- `Deposit`: bank operation that moves previously collected payments into the bank account.
- `Remaining due`: amount still to be collected on an invoice.
- `Preview`: pre-execution analysis of an import.
- `Selective reset`: targeted cleanup used to replay a specific import perimeter.