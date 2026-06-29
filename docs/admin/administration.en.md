# System Administration — Solde ⚖️

---

### Upgrading

#### Standard procedure (Docker Compose)

1. **Back up** before any update (see Backups section below).
2. **Pull the new image:**
   ```bash
   docker compose pull
   ```
3. **Restart the service:**
   ```bash
   docker compose up -d
   ```
4. **Check startup logs:**
   ```bash
   docker compose logs solde --tail=30
   ```
5. **Verify the health check:**
   ```bash
   curl http://localhost:8000/api/health
   # → {"status": "ok", "version": "x.y.z"}
   ```

Database migrations run automatically on startup. No manual action is needed.

#### Upgrading on Synology NAS (Portainer)

1. In Portainer → **Stacks → solde**.
2. Click **Pull and redeploy**.
3. Wait for the redeployment and verify access to the application.

#### If startup fails after an upgrade

1. Check logs: `docker compose logs solde --tail=50`
2. If a migration error appears: do not delete `data/`. Restore your backup and report the error.

---

### Automatic backup (scheduled)

Automatic backups are configured under **Settings → Automatic backup** (admin account only).

**Schedule modes:**

| Mode | Description |
|---|---|
| **Daily (fixed time)** | Triggers a backup every day at the specified HH:MM (server local time). Recommended for most use cases. |
| **Every N hours** | Repeats on a fixed interval. |
| **Cron expression** | Advanced 5-field schedule (e.g. `0 2 * * *`). |

**Content options:**
- **Include uploaded attachments**: also sends `data/uploads/` to the destination.
- **Include all previous backup files**: sends the full `data/backups/` directory. When disabled (default), only the latest `.db` snapshot file is transferred — significantly reducing transfer volume.

**Real-time progress:** the panel displays a spinner and a progress percentage as soon as a backup starts, including scheduler-triggered ones (detected within 10 seconds if the settings page is already open).

**Destinations:**

| Type | Description |
|---|---|
| **Local** | Absolute path on the server hosting the application. |
| **SMB (network)** | NAS/file server SMB share — provide host, share, username, password. |
| **OneDrive** | Microsoft OneDrive account — click **Authorize OneDrive** and follow the device authentication flow. |

Each destination can be enabled/disabled independently and tested without running a backup (**Test connection**).

**Failure notification:** enable the option and configure SMTP (Settings → Email) to receive an email if a scheduled backup fails.

### Backups (on-demand)

1. Go to **Administration → System supervision → Backups**.
2. Optionally add a label.
3. Click **Create backup**.
4. Download the generated `.db` file.

In-app backups are stored in `data/backups/`.

#### Manual backup (container stopped — recommended for critical backups)

```bash
docker compose stop
cp -r ./data /path/to/backup/data-$(date +%Y%m%d)
cp ./.env /path/to/backup/.env
docker compose up -d
```

> **Important:** always back up `solde.db`, `solde.db-wal`, and `solde.db-shm` together. Copying only `solde.db` may produce an inconsistent restore if WAL files from a different state remain.

---

### Restore

#### From the admin UI

1. Go to **Administration → System supervision → Backups**.
2. Select the backup from the list.
3. Click **Restore**.
4. Type `RESTAURER` in the confirmation field.
5. Confirm. The application restarts automatically.

#### Manual restore

```bash
docker compose stop
rm -f ./data/solde.db ./data/solde.db-wal ./data/solde.db-shm
cp /path/to/backup/solde.db ./data/solde.db
docker compose up -d
docker compose logs solde --tail=20
```

---

### User management

Location: **Settings → User management** (admin account required).

#### Roles

| Technical role | Product label | Access |
|---|---|---|
| `secretaire` | Manager | Full Management area |
| `tresorier` | Accountant | Management + Accounting areas |
| `admin` | Administrator | Everything + users + settings + system supervision + Excel import |
| `readonly` | Read-only | Transitional role — view only |

#### Password policy

All passwords must meet:
- Minimum 8 characters
- At least one uppercase ASCII letter
- At least one ASCII digit

---

### Routine Docker operations

```bash
docker compose up -d              # Start
docker compose stop               # Stop
docker compose restart solde      # Restart
docker compose down               # Stop and remove container (data preserved)
docker compose logs -f solde      # Live logs
docker compose exec solde sh      # Shell in container
```
