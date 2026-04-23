# Migration / Upgrade guide

## Purpose

This guide explains how to upgrade Solde to a new version on a Docker deployment (Synology NAS or standard server). It covers preparation, the upgrade itself, verification, and rollback if something goes wrong.

**Intended audience**: association administrator, no deep technical expertise required.

---

## Before you start

- **Back up your database** before any upgrade.
  - From the UI: **Settings → Back up database** (downloads a `.db` file).
  - From the NAS: copy the entire `data/` directory to a safe location.
- **Note the current version** shown in the header or via `GET /api/health`.
- **Read the release notes** in `doc/releases/` to check for breaking changes.

---

## Upgrade procedure

### 1. Download the new version

```bash
cd /path/to/solde
git pull origin main
```

Or, on Synology without git:

1. Download the ZIP archive from GitHub (_Releases_ tab).
2. Extract it into the application directory, overwriting existing files (except `data/` and `.env`).

### 2. Stop the application

```bash
docker compose down
```

On Synology (Container Manager): select the `solde` container → **Stop**.

### 3. Rebuild and restart

```bash
docker compose up -d --build
```

On Synology (Container Manager): **Project** → **Rebuild** → **Start**.

Database migrations (Alembic) run automatically on startup. No manual action needed.

### 4. Verify

- Access `http://<your-nas>:8000` — the application should load normally.
- Check the health endpoint: `http://<your-nas>:8000/api/health` should return `{"status": "ok"}`.
- Log in and verify your data is intact (contacts, invoices, current fiscal year).

---

## Troubleshooting

### Application does not start

1. Check the logs: `docker compose logs solde --tail=50`
2. If a migration error appears:
   - **Do not delete** the `data/` directory.
   - Restore the backup (see below) and report the error.

### Restoring a backup

1. Stop the application: `docker compose down`
2. Replace `data/solde.db` with your backup:
   ```bash
   cp /path/to/backup/solde_backup_XXXXXXXX_XXXXXX.db data/solde.db
   ```
3. To revert to the previous application version:
   ```bash
   git checkout v<previous-version>
   docker compose up -d --build
   ```
4. Restart: `docker compose up -d`

### Restoring from Synology without SSH

1. In **File Station**, navigate to the Docker project folder (`docker/solde/data/`).
2. Delete (or rename) `solde.db`.
3. Copy your backup file and rename it to `solde.db`.
4. Restart the container in **Container Manager**.

---

## Best practices

- **Always back up** before each upgrade — from the UI or by copying `data/`.
- **Read the release notes** (`doc/releases/vX.Y.Z.md`) to learn about changes.
- **Test quickly** after upgrading: login, dashboard, invoice list.
- **Never modify** files in `data/` directly — use the UI or the API.
- **Keep multiple backups** (the system automatically keeps the last 5 in `data/backups/`).

---

## Semantic versioning

Solde follows [semantic versioning](https://semver.org/):

| Type | Format | Meaning |
|---|---|---|
| **Patch** | `0.1.1` → `0.1.2` | Bug fixes, no functional changes |
| **Minor** | `0.1.x` → `0.2.0` | New features, backward-compatible |
| **Major** | `0.x.x` → `1.0.0` | Breaking changes (requires special attention) |

For minor and patch versions, the upgrade is normally transparent. For a major version, read the migration notes in the release notes carefully.
