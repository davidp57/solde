# User and Permission Management

## Purpose

BL-022 lots 1 and 2 introduced account administration. BL-023 then clarified the target product model for roles and the visible split between `Management` and `Accounting`, without immediately renaming the technical role values already used in the API and backend authorization rules.

The objective is twofold:

1. make roles understandable for a functional administrator;
2. introduce account administration that remains consistent with the permissions already implemented.

## Chosen principle

The existing technical values remain unchanged in this delivery:

- `readonly`
- `secretaire`
- `tresorier`
- `admin`

However, they are interpreted in the product using more readable business labels. The active product target now relies primarily on three business-facing roles: `Manager`, `Accountant`, and `Administrator`.

## Mapping technical roles to product roles

| Technical value | Product label | Main usage |
|---|---|---|
| `readonly` | Read-only | Legacy or transitional role, with no strong product value at this stage |
| `secretaire` | Manager | Handles the whole management area |
| `tresorier` | Accountant | Handles accounting and the full management area |
| `admin` | Administrator | Manages users, settings, and the whole application |

## Target UI sections

Navigation should visibly separate at least two sections:

### Management

- Dashboard
- Contacts
- Client invoices
- Supplier invoices
- Payments
- Bank
- Cash

### Accounting

- Fiscal years
- Chart of accounts
- Accounting rules
- Balance sheet
- Income statement
- Journal
- Trial balance
- General ledger

## Simplified permission matrix

| Area / action | Manager | Accountant | Administrator |
|---|---|---|---|
| Management area | Read + write | Read + write | Read + write |
| Accounting area | No | Read + write or read-only depending on the screen | Read + write or read-only depending on the screen |
| Users | No | No | Read + write |
| Application settings | No | No | Read + write |

In practice:

- `Manager` can view and edit the full `Management` area.
- `Accountant` can view and edit the full `Management` area and can view or edit the `Accounting` area depending on the screen.
- `Administrator` can view everything, edit everything, and manage the application itself.
- `readonly` is no longer a target role that should be emphasized in the product UI.

Useful implementation notes:

- the dashboard remains available through a dedicated `Home` section separate from `Management`, including for the legacy `readonly` technical role;
- the global fiscal year selector remains visible to the active business roles `Manager`, `Accountant`, and `Administrator`, because several management screens are filtered by fiscal year even outside the `Accounting` section;
- fiscal year administration remains restricted to `Accountant` and `Administrator`;
- the `Current fiscal year` card on the dashboard follows the same logic as the global selector: first prefer an open fiscal year covering today, otherwise use the most recent open year.

## Scope of BL-022 lots

Lot 2 adds account administration with the following capabilities:

- list existing accounts;
- create an account;
- change an account role;
- activate or deactivate an account.

Lot 3 adds the `My profile` area with the following capabilities:

- display the username, effective business role, and account creation date;
- allow controlled updates to the contact e-mail;
- keep the login identifier stable and non-editable through the UI.

Lot 4 completes account security with the following capabilities:

- change the password by providing the current password;
- invalidate existing JWT access and refresh tokens after a password change or reset;
- allow an administrator to define a temporary password for another user in order to support access recovery in a self-hosted association context.

At this stage, BL-022 still does not cover a full backend/frontend alignment with the newer BL-023 matrix.

## Chosen access recovery procedure

The ticket does not implement a self-service `forgot password` e-mail workflow. The chosen procedure is intentionally simpler and more robust for the target context:

1. the user who can no longer sign in contacts an administrator;
2. the administrator opens `Users` and sets a temporary password;
3. the user signs in again with that temporary password;
4. the user changes it immediately from `My profile`.

This approach avoids making account recovery dependent on a correctly configured SMTP setup, while keeping the process explicit and safe.

## Safeguards retained

To avoid administrative lockout or unintended session persistence in this delivery:

- an administrator cannot deactivate their own account;
- an administrator cannot remove their own administration role;
- the last active administrator cannot be deactivated or downgraded;
- a password change or reset invalidates previous access and refresh tokens;
- administrator-triggered reset remains separate from user-driven password change so that support and autonomy do not get mixed together.