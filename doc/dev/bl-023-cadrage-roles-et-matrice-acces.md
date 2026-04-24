# BL-023 — Role and Access Matrix Framing

## Objective

Before changing permissions, the product target for roles must be clarified and three things that are currently mixed together must be separated:

- the matrix documented in `BL-022`;
- the matrix actually enforced by the backend;
- the visibility actually exposed by the frontend.

This document serves as the discussion baseline for deciding the target and then framing a later implementation, instead of fixing symptoms one by one by intuition.

## Product decisions validated on 2026-04-14

The following arbitrations are now validated:

- `admin` sees everything, edits everything, and manages the application, including `utilisateurs`, `paramètres`, and the other transversal capabilities;
- `tresorier` keeps its current technical value but must be presented as `Comptable` in the product;
- `Comptable` can view and edit the whole `Gestion` area and the whole `Comptabilité` area;
- `secretaire` keeps its current technical value but must be presented as `Gestionnaire` in the product;
- `Gestionnaire` can view and edit the whole `Gestion` area;
- `readonly` has no real product value at this stage; it may remain as a legacy or transitional technical value, but it is no longer part of the active functional target to highlight in the UI and the main matrix;
- the UI must visibly separate the `Gestion` and `Comptabilité` areas.

## Validated UI structure

Target navigation must be organized into at least two visually distinct sections.

### `Gestion` section

- `Tableau de bord`
- `Contacts`
- `Factures clients`
- `Factures fournisseurs`
- `Paiements`
- `Banque`
- `Caisse`

### `Comptabilité` section

- `Exercices`
- `Plan comptable`
- `Règles comptables`
- `Bilan`
- `Résultat`
- `Journal`
- `Balance`
- `Grand livre`

## Verified current state

### Existing technical roles

The technical roles currently used in code are:

- `readonly`
- `secretaire`
- `tresorier`
- `admin`

The existing document `doc/dev/user-permissions.md` already presents them on the product side as:

- `readonly` -> `Consultation`
- `secretaire` -> `Gestionnaire`
- `tresorier` -> `Comptable`
- `admin` -> `Administrateur`

### Matrix actually enforced by the backend

The backend currently applies a simple domain-based rule:

| Backend area | Read | Write |
|---|---|---|
| Contacts | every authenticated user | `secretaire`, `tresorier`, `admin` |
| Invoices | every authenticated user | `secretaire`, `tresorier`, `admin` |
| Payments | every authenticated user | `secretaire`, `tresorier`, `admin` |
| Bank | every authenticated user | `tresorier`, `admin` |
| Cash | every authenticated user | `tresorier`, `admin` |
| Accounting (`journal`, `balance`, `grand livre`, accounts, rules, fiscal years) | every authenticated user | `tresorier`, `admin` |
| Excel imports | no dedicated read access today | `tresorier`, `admin` |
| Salaries | every authenticated user | `tresorier`, `admin` |
| Settings | `admin` | `admin` |
| Users | `admin` | `admin` |

Direct consequence: at the API level, a `readonly` user can already read accounting screens, bank, cash, and salaries if the frontend exposes the corresponding views.

### Visibility actually applied by the frontend

The frontend is currently more permissive than the documented product matrix:

- all authenticated users see nearly all main menu entries;
- only `Utilisateurs` and `Paramètres` are hidden from non-admin users;
- only the `settings` and `users` routes are explicitly guarded in the router via `requiresAdmin`;
- the other views therefore remain reachable through direct navigation as long as backend read access is allowed;
- the user area in the shell relies on `auth.user` and shows an intermittent symptom where the username and logout button disappear.

Direct consequence: the permission matrix perceived by users currently depends more on the menu and implicit backend reads than on an explicitly decided permissions matrix.

## Main gap to address

Document `BL-022` describes an intuitive product split:

- `Consultation` reads without modifying;
- `Gestionnaire` manages business flows around `contacts`, `factures`, and `paiements`;
- `Comptable` manages treasury, accounting, imports, and salaries;
- `Administrateur` manages accounts and settings.

But the current application does not yet translate that target cleanly:

- `readonly` currently reads much more than the `Consultation` label suggests;
- `secretaire` currently sees many accounting entries in the shell;
- the exact boundary between allowed accounting read access, allowed treasury read access, and business write access has not been explicitly decided;
- the global shell exposes transversal elements such as the `menu`, the `fiscal year selector`, and the `user area` without any clearly defined visibility matrix.

## Validated product target

### Retained guiding principle

The target model relies on three active product roles:

- `Gestionnaire`
- `Comptable`
- `Administrateur`

The technical `readonly` role is not retained as a useful product role in the current target. It may be kept technically for as long as needed to avoid a brutal migration, but it must no longer shape the main functional design.

### Validated target matrix

| Area / action | Gestionnaire | Comptable | Administrateur |
|---|---|---|---|
| Dashboard | Read + related business write access | Read + related business write access | Read + related business write access |
| Contacts | Read + write | Read + write | Read + write |
| Client / supplier invoices | Read + write | Read + write | Read + write |
| Payments | Read + write | Read + write | Read + write |
| Bank | Read + write | Read + write | Read + write |
| Cash | Read + write | Read + write | Read + write |
| Fiscal years | No | Read + write | Read + write |
| Chart of accounts | No | Read + write | Read + write |
| Accounting rules | No | Read + write | Read + write |
| Balance sheet | No | Read | Read |
| Income statement | No | Read | Read |
| Journal | No | Read | Read |
| Trial balance | No | Read | Read |
| Ledger | No | Read | Read |
| Excel imports | No | Read + write | Read + write |
| Salaries | No | Read + write | Read + write |
| Users | No | No | Read + write |
| Settings | No | No | Read + write |

### Explicit consequences of this decision

- `Gestionnaire` covers the whole `Gestion` area, including `banque` and `caisse`;
- `Comptable` is a functional superset of `Gestionnaire`, with full access to the `Comptabilité` area;
- `Administrateur` is a superset of `Comptable` and additionally owns application management;
- the `Gestion` / `Comptabilité` UI split becomes a product requirement, not only an ergonomics preference;
- any future presence of `readonly` must be treated as a compatibility or advanced administration case, not as a central role of the business target.

## Remaining questions before implementation

The main product arbitrations are now done, so the remaining points are mostly implementation details:

1. should `readonly` be completely hidden in the admin UI until its product utility is redefined;
2. how should navigation be structured visually to materialize `Gestion` and `Comptabilité` without making daily use heavier;
3. how should the shell user area and the global fiscal year selector behave depending on the role and the current section.

## Implementation principles to enforce afterwards

Once the matrix is validated, implementation must respect these rules:

1. the backend remains the source of truth for permissions;
2. the frontend hides unauthorized menus and routes, but does not replace backend controls;
3. frontend helpers must expose an explicit capability-based matrix, not only `isAdmin` and `isTresorier`;
4. backend tests must cover `403` refusals by role on sensitive areas;
5. frontend tests must cover menu visibility, guarded routes, fiscal year selector visibility, and stable rendering of the shell user area.

## Recommended breakdown for next steps

### Step 1 — backend

Align `require_role(...)` dependencies and complete authorization tests by domain.

### Step 2 — frontend

Align the menu, guards, authorization helpers, fiscal year selector visibility, and stable rendering of the user area.

### Step 3 — documentation

Update `doc/dev/user-permissions.md` so that it reflects the final matrix actually implemented.