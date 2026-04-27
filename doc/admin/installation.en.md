# Installation — Solde ⚖️

---

### Prerequisites

- Docker and Docker Compose installed on the host.
- Internet access from the host to pull the image from `ghcr.io`.
- A persistent directory for application data (e.g., `/volume1/docker/solde/data` on Synology NAS).

---

### Option A — Recommended: GHCR image + Docker Compose

No local build required.

#### 1. Create the deployment directory

```bash
mkdir -p /opt/solde
cd /opt/solde
```

#### 2. Create `docker-compose.yml`

```yaml
services:
  solde:
    image: ghcr.io/davidp57/solde:latest
    container_name: solde
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    env_file:
      - .env
```

#### 3. Create `.env`

```bash
# Required — random string of at least 32 characters
JWT_SECRET_KEY=replace-with-a-random-string-of-at-least-32-characters

# Bootstrap administrator account (created on first startup if no users exist)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
ADMIN_EMAIL=admin@your-association.org

# Database (do not change in a standard Docker deployment)
DATABASE_URL=sqlite+aiosqlite:///app/data/solde.db

# Disabled by default in production
DEBUG=false
SWAGGER_ENABLED=false
```

> **Important:** the bootstrap admin account is created only on the first startup and only when the database contains no users yet. Change the password immediately after the first login.

#### 4. Start the application

```bash
docker compose pull
docker compose up -d
```

Solde is available at `http://<your-server-ip>:8000`.

On startup, Solde:
1. automatically applies database migrations;
2. creates the bootstrap admin account if the database is empty.

---

### Option B — Synology NAS with Portainer

#### Prerequisites

- Portainer CE accessible (port `9000` or `9443`).
- A shared folder on the NAS, e.g., `/volume1/docker/solde/data`.
- Outbound internet access from the NAS to `ghcr.io`.

#### Procedure

1. In Portainer → **Stacks → Add stack**.
2. Name the stack `solde`.
3. Paste the `docker-compose.yml` contents from Option A (adapt the volume path).
4. Under **Environment variables**, add at minimum:

| Variable | Value |
|---|---|
| `JWT_SECRET_KEY` | Random string, 32+ characters |
| `ADMIN_PASSWORD` | Strong password |

5. Click **Deploy the stack**.

---

### Persistent data

All application state lives in the volume mounted at `/app/data`:

| Path | Contents |
|---|---|
| `solde.db` | Primary SQLite database |
| `solde.db-wal` | WAL journal — always back up with `solde.db` |
| `solde.db-shm` | WAL shared memory file |
| `pdfs/` | Generated client invoice PDFs |
| `uploads/` | Supplier invoice attachments |
| `logs/` | Rotating application log |
| `backups/` | Database snapshots created via the admin UI |

> **Warning:** always back up `solde.db`, `solde.db-wal`, and `solde.db-shm` together. Restoring only `solde.db` while WAL files from a different state remain can produce an inconsistent database.

---

### Verifying the installation

```bash
docker compose ps
docker compose logs solde --tail=30
curl http://localhost:8000/api/health
# → {"status": "ok", "version": "x.y.z"}
```

---

### Initial access

1. Open `http://<address>:8000` in a browser.
2. Sign in with the credentials defined in `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).
3. Solde will prompt you to change the password on the first login.
4. Then configure the association via **Settings** (name, address, SIRET, logo, SMTP).
