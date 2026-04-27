# Configuration — Solde ⚖️

---

Configuration is split across two levels:

1. **Environment variables** (`.env` file) — technical startup parameters.
2. **Association settings** (web interface) — business data stored in the database.

---

### Environment variables

#### Required

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | JWT signing key. Random string of at least 32 characters. Never use the default value in production. |
| `DATABASE_URL` | SQLite connection string. In a standard Docker deployment, keep `sqlite+aiosqlite:///app/data/solde.db` (path inside the volume mounted at `/app/data`). |

#### Bootstrap administrator

These variables apply only on the very first startup, only when the database contains no users.

| Variable | Default | Description |
|---|---|---|
| `ADMIN_USERNAME` | `admin` | Bootstrap admin username. |
| `ADMIN_PASSWORD` | `changeme` | Initial password. Change immediately. Min 8 chars, at least one uppercase letter and one ASCII digit. |
| `ADMIN_EMAIL` | `admin@exemple.fr` | Bootstrap admin email. |

#### Runtime mode

| Variable | Default | Description |
|---|---|---|
| `DEBUG` | `false` | Enables detailed error messages and exposes Swagger UI. Never enable in production. |
| `SWAGGER_ENABLED` | `false` | Exposes Swagger UI (`/api/docs`) and ReDoc (`/api/redoc`) independently of `DEBUG`. |
| `FISCAL_YEAR_START_MONTH` | `8` | First month of the fiscal year (1 = January, 8 = August). |

---

### Association settings (web interface)

Location: **Settings** menu (admin account required).

Settings are stored in the database and take effect immediately without restarting the container.

#### Association information

| Setting | Description |
|---|---|
| Association name | Displayed in invoice headers, emails, and PDFs. |
| Address | Full postal address (multi-line). |
| SIRET | French business ID displayed on invoices. |
| Logo | Uploaded image, shown in invoice PDFs. Accepted formats: PNG, JPEG, WebP. |
| Social purpose | Short description of the association's activity. |

#### Invoice numbering

| Setting | Description | Example |
|---|---|---|
| Client invoice template | Uses `{year}` and `{seq}` | `{year}-{seq}` → `2026-001` |
| Sequence digit count | Number of digits for `{seq}` | `3` → `001` |
| Supplier invoice template | Python `strftime` format | `FF-%Y%m%d` → `FF-20260427` |

#### Default due date

| Setting | Description |
|---|---|
| Invoice due date delay (days) | Days added to the invoice date to auto-compute the due date (0–365). |

#### SMTP configuration

| Setting | Description |
|---|---|
| SMTP server | Server address (e.g., `smtp.gmail.com`) |
| Port | SMTP port (e.g., `587` for STARTTLS, `465` for SSL) |
| Use SSL/TLS | Enable direct SSL (typically port 465) |
| SMTP username | Email address or account identifier |
| SMTP password | Password or app-specific password |
| Sender email | Address shown as sender |
| BCC | Hidden copy address for all sent invoices (optional) |

---

### Initial setup sequence

After the first login:

1. **Change the bootstrap admin password**.
2. **Fill in association settings** (name, address, SIRET, logo).
3. **Configure SMTP** if email sending is needed.
4. **Create fiscal years** covering the periods to manage.
5. **Set up the chart of accounts** (import or create manually).
6. **Create accounting rules** to automate journal generation.
7. **Create user accounts** for other team members.
8. **Import historical data** if needed (see [excel-import.en.md](./excel-import.en.md)).
