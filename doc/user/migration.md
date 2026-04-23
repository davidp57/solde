# Guide de migration / Montée de version

## Objectif

Ce guide explique comment mettre à jour Solde vers une nouvelle version sur un déploiement Docker (Synology NAS ou serveur classique). Il couvre la préparation, la mise à jour, la vérification et le rollback en cas de problème.

**Public visé** : administrateur de l'association, sans expertise technique poussée.

---

## Avant de commencer

- **Sauvegardez votre base de données** avant toute mise à jour.
  - Depuis l'interface : **Paramètres → Sauvegarder la base** (télécharge un fichier `.db`).
  - Depuis le NAS : copiez le dossier `data/` entier vers un emplacement sûr.
- **Notez la version actuelle** affichée dans l'en-tête ou via `GET /api/health`.
- **Consultez les notes de version** dans `doc/releases/` pour identifier d'éventuels changements importants (breaking changes).

---

## Procédure de mise à jour

### 1. Télécharger la nouvelle version

```bash
cd /chemin/vers/solde
git pull origin main
```

Ou, sur Synology sans git :

1. Téléchargez l'archive ZIP depuis GitHub (onglet _Releases_).
2. Décompressez-la dans le dossier de l'application en écrasant les fichiers existants (sauf `data/` et `.env`).

### 2. Arrêter l'application

```bash
docker compose down
```

Sur Synology (Container Manager) : sélectionnez le conteneur `solde` → **Arrêter**.

### 3. Reconstruire et redémarrer

```bash
docker compose up -d --build
```

Sur Synology (Container Manager) : **Projet** → **Reconstruire** → **Démarrer**.

Les migrations de base de données (Alembic) s'exécutent automatiquement au démarrage. Vous n'avez rien à faire manuellement.

### 4. Vérifier

- Accédez à `http://<votre-nas>:8000` — l'application doit se charger normalement.
- Vérifiez le health check : `http://<votre-nas>:8000/api/health` doit renvoyer `{"status": "ok"}`.
- Connectez-vous et vérifiez que vos données sont intactes (contacts, factures, exercice en cours).

---

## En cas de problème

### L'application ne démarre pas

1. Consultez les logs : `docker compose logs solde --tail=50`
2. Si une erreur de migration apparaît :
   - **Ne supprimez pas** le dossier `data/`.
   - Restaurez le backup (voir ci-dessous) et signalez l'erreur.

### Restaurer un backup

1. Arrêtez l'application : `docker compose down`
2. Remplacez le fichier `data/solde.db` par votre backup :
   ```bash
   cp /chemin/vers/backup/solde_backup_XXXXXXXX_XXXXXX.db data/solde.db
   ```
3. Pour revenir à la version précédente de l'application :
   ```bash
   git checkout v<version-précédente>
   docker compose up -d --build
   ```
4. Redémarrez : `docker compose up -d`

### Restaurer depuis Synology sans SSH

1. Dans **File Station**, naviguez vers le dossier Docker du projet (`docker/solde/data/`).
2. Supprimez (ou renommez) `solde.db`.
3. Copiez votre fichier de backup et renommez-le en `solde.db`.
4. Redémarrez le conteneur dans **Container Manager**.

---

## Bonnes pratiques

- **Sauvegardez systématiquement** avant chaque mise à jour — depuis l'interface ou en copiant `data/`.
- **Lisez les notes de version** (`doc/releases/vX.Y.Z.md`) pour connaître les changements.
- **Testez rapidement** après la mise à jour : connexion, tableau de bord, liste des factures.
- **Ne modifiez jamais** les fichiers dans `data/` directement — utilisez l'interface ou l'API.
- **Conservez plusieurs backups** (le système en garde 5 automatiquement dans `data/backups/`).

---

## Versionnage sémantique

Solde suit le [versionnage sémantique](https://semver.org/lang/fr/) :

| Type | Format | Signification |
|---|---|---|
| **Patch** | `0.1.1` → `0.1.2` | Corrections de bugs, aucun changement fonctionnel |
| **Mineur** | `0.1.x` → `0.2.0` | Nouvelles fonctionnalités, rétro-compatible |
| **Majeur** | `0.x.x` → `1.0.0` | Changements incompatibles (nécessite attention particulière) |

Pour les versions mineures et patch, la mise à jour est normalement transparente. Pour une version majeure, lisez attentivement les notes de migration dans les release notes.
