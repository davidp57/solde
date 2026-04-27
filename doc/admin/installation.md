# Installation — Solde ⚖️

---

## Français

### Prérequis

- Docker et Docker Compose installés sur l'hôte.
- Accès internet depuis l'hôte pour télécharger l'image depuis `ghcr.io`.
- Un répertoire persistant pour les données (par exemple `/volume1/docker/solde/data` sur un NAS Synology).

---

### Option A — Déploiement recommandé : image GHCR + Docker Compose

C'est la méthode recommandée pour une installation de production sur NAS ou serveur.
Aucune compilation locale n'est nécessaire.

#### 1. Créer le répertoire de déploiement

```bash
mkdir -p /opt/solde
cd /opt/solde
```

#### 2. Créer le fichier `docker-compose.yml`

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

#### 3. Créer le fichier `.env`

```bash
# Obligatoire — clé aléatoire d'au moins 32 caractères
JWT_SECRET_KEY=remplacez-par-une-cle-aleatoire-de-32-caracteres-minimum

# Compte administrateur bootstrap (créé automatiquement au premier démarrage)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changez-ce-mot-de-passe
ADMIN_EMAIL=admin@votre-association.fr

# Base de données (ne pas modifier dans un déploiement Docker standard)
DATABASE_URL=sqlite+aiosqlite:///data/solde.db

# Désactivé par défaut en production
DEBUG=false
SWAGGER_ENABLED=false
```

> **Important :** le compte administrateur bootstrap n'est créé qu'au premier démarrage, uniquement si la base de données ne contient encore aucun utilisateur. Changez le mot de passe immédiatement après la première connexion.

#### 4. Démarrer l'application

```bash
docker compose pull
docker compose up -d
```

Solde est accessible à `http://<ip-de-votre-serveur>:8000`.

Au démarrage, Solde :
1. applique automatiquement les migrations de base de données ;
2. crée le compte administrateur bootstrap si la base est vide.

---

### Option B — Déploiement sur NAS Synology avec Portainer

Portainer est disponible via Container Manager sur DSM ou en installation Docker standalone.

#### Prérequis

- Portainer CE accessible (port `9000` ou `9443`).
- Un dossier partagé créé sur le NAS, par exemple `/volume1/docker/solde/data`.
- Accès internet depuis le NAS vers `ghcr.io`.

#### Procédure

1. Dans Portainer → **Stacks → Add stack**.
2. Nommez la stack `solde`.
3. Collez le contenu de `docker-compose.yml` (voir Option A) dans l'éditeur.
   - Adaptez le chemin du volume : `/volume1/docker/solde/data:/app/data`.
4. Sous **Environment variables**, ajoutez au minimum :

| Variable | Valeur |
|---|---|
| `JWT_SECRET_KEY` | Chaîne aléatoire de 32+ caractères |
| `ADMIN_PASSWORD` | Mot de passe fort |

5. Cliquez sur **Deploy the stack**.

---

### Données persistantes

Tout l'état de l'application est stocké dans le volume monté sur `/app/data` :

| Fichier / dossier | Contenu |
|---|---|
| `solde.db` | Base de données SQLite principale |
| `solde.db-wal` | Journal WAL — sauvegarder avec `solde.db` |
| `solde.db-shm` | Fichier de mémoire partagée WAL |
| `pdfs/` | Factures clients PDF générées |
| `uploads/` | Pièces jointes factures fournisseurs |
| `logs/` | Journal applicatif rotatif |
| `backups/` | Sauvegardes créées via l'interface d'administration |

> **Attention :** toujours sauvegarder `solde.db`, `solde.db-wal` et `solde.db-shm` ensemble. Restaurer uniquement `solde.db` sans les fichiers WAL peut produire une base incohérente.

---

### Vérification de l'installation

```bash
# Vérifier que le conteneur tourne
docker compose ps

# Vérifier les logs de démarrage
docker compose logs solde --tail=30

# Health check
curl http://localhost:8000/api/health
# → {"status": "ok", "version": "x.y.z"}
```

---

### Accès initial

1. Ouvrez `http://<adresse>:8000` dans un navigateur.
2. Connectez-vous avec les identifiants définis dans `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).
3. Solde vous demande de changer le mot de passe à la première connexion.
4. Configurez ensuite l'association via **Paramètres** (nom, adresse, SIRET, logo, SMTP).

---

### Démarrage local (développement)

Voir [../dev/contributing.md](../dev/contributing.md) pour le setup de développement complet.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
./dev.ps1
```

---

---

## English

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
DATABASE_URL=sqlite+aiosqlite:///data/solde.db

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
