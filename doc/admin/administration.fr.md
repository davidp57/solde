# Administration système — Solde ⚖️

---

### Montée de version

#### Procédure standard (Docker Compose)

1. **Sauvegarder** avant toute mise à jour (voir section Sauvegardes ci-dessous).
2. **Télécharger la nouvelle image :**
   ```bash
   docker compose pull
   ```
3. **Redémarrer le service :**
   ```bash
   docker compose up -d
   ```
4. **Vérifier les logs de démarrage :**
   ```bash
   docker compose logs solde --tail=30
   ```
5. **Vérifier le health check :**
   ```bash
   curl http://localhost:8000/api/health
   # → {"status": "ok", "version": "x.y.z"}
   ```

Les migrations de base de données s'exécutent automatiquement au démarrage. Aucune action manuelle n'est nécessaire.

#### Montée de version sur Synology NAS (Portainer)

1. Dans Portainer → **Stacks → solde**.
2. Cliquer sur **Pull and redeploy** (ou modifier le tag de l'image et redéployer).
3. Attendre la fin du redéploiement et vérifier l'accès à l'application.

#### En cas d'échec au démarrage

1. Consulter les logs : `docker compose logs solde --tail=50`
2. Si une erreur de migration apparaît :
   - Ne pas supprimer le dossier `data/`.
   - Restaurer la sauvegarde (voir ci-dessous).
   - Signaler l'erreur.

---

### Sauvegardes

#### Depuis l'interface d'administration (recommandé)

1. Aller dans **Administration → Supervision système → Sauvegardes**.
2. Optionnel : saisir un libellé pour identifier la sauvegarde.
3. Cliquer sur **Créer une sauvegarde**.
4. Télécharger le fichier `.db` généré.

Les sauvegardes créées via l'interface sont stockées dans `data/backups/`.

#### Sauvegarde manuelle (conteneur arrêté — recommandé pour les sauvegardes critiques)

```bash
docker compose stop
# Copier tout le dossier data/
cp -r ./data /chemin/vers/sauvegarde/data-$(date +%Y%m%d)
docker compose up -d
```

> **Important :** toujours sauvegarder `solde.db`, `solde.db-wal` et `solde.db-shm` ensemble. Copier uniquement `solde.db` peut produire une base incohérente si le journal WAL n'est pas pris en compte.

#### Sauvegarde à chaud (sans arrêter le conteneur)

```bash
cp -r ./data/solde.db ./data/solde.db-wal ./data/solde.db-shm /chemin/vers/sauvegarde/
cp ./data/pdfs /chemin/vers/sauvegarde/ -r
cp ./.env /chemin/vers/sauvegarde/
```

Le fichier `.env` doit aussi être sauvegardé séparément — il n'est pas inclus dans `data/`.

#### Automatisation sur Synology

Utiliser **Hyper Backup** ou une tâche planifiée DSM pour sauvegarder automatiquement `/volume1/docker/solde/data` vers un emplacement externe (disque USB, NAS distant, cloud).

---

### Restauration

#### Depuis l'interface d'administration

1. Aller dans **Administration → Supervision système → Sauvegardes**.
2. Sélectionner la sauvegarde dans la liste.
3. Cliquer sur **Restaurer**.
4. Saisir `RESTAURER` dans le champ de confirmation.
5. Confirmer. L'application redémarre automatiquement après restauration.

#### Restauration manuelle

```bash
docker compose stop

# Supprimer les fichiers SQLite actuels (évite les conflits WAL)
rm -f ./data/solde.db ./data/solde.db-wal ./data/solde.db-shm

# Copier la sauvegarde
cp /chemin/vers/sauvegarde/solde.db ./data/solde.db
# Si des fichiers WAL ont été sauvegardés, les restaurer aussi
# cp /chemin/vers/sauvegarde/solde.db-wal ./data/solde.db-wal

# Restaurer les PDFs et uploads si nécessaire
cp -r /chemin/vers/sauvegarde/pdfs ./data/
cp -r /chemin/vers/sauvegarde/uploads ./data/

# Restaurer le .env si nécessaire
cp /chemin/vers/sauvegarde/.env ./.env

docker compose up -d
docker compose logs solde --tail=20
```

---

### Gestion des utilisateurs

Accès : **Paramètres → Gestion des utilisateurs** (compte administrateur uniquement).

#### Rôles disponibles

| Rôle technique | Libellé produit | Accès |
|---|---|---|
| `secretaire` | Gestionnaire | Zone Gestion complète (contacts, factures, paiements, banque, caisse, salaires) |
| `tresorier` | Comptable | Zone Gestion + Zone Comptabilité |
| `admin` | Administrateur | Tout + utilisateurs + paramètres + supervision système + import Excel |
| `readonly` | Lecture seule | Rôle transitoire — consultation uniquement |

#### Créer un utilisateur

1. Aller dans **Paramètres → Utilisateurs**.
2. Cliquer sur **Nouvel utilisateur**.
3. Renseigner l'identifiant, l'e-mail et le rôle.
4. Un mot de passe temporaire est généré — l'utilisateur devra le changer à la première connexion.

#### Modifier le rôle d'un utilisateur

1. Aller dans **Paramètres → Utilisateurs**.
2. Cliquer sur l'utilisateur.
3. Modifier le rôle et sauvegarder.

#### Réinitialiser un mot de passe

1. Aller dans **Paramètres → Utilisateurs**.
2. Sélectionner l'utilisateur.
3. Cliquer sur **Réinitialiser le mot de passe**.
4. Communiquer le mot de passe temporaire à l'utilisateur.
5. L'utilisateur sera invité à le changer à la prochaine connexion.

#### Désactiver un compte

Un compte désactivé ne peut plus se connecter mais ses données restent intactes.

1. Aller dans **Paramètres → Utilisateurs**.
2. Sélectionner l'utilisateur.
3. Désactiver le compte.

---

### Politique de mots de passe

Tous les mots de passe doivent respecter :
- Minimum 8 caractères
- Au moins une lettre majuscule ASCII
- Au moins un chiffre ASCII

---

### Supervision système

Accès : **Administration → Supervision système** (compte administrateur uniquement).

#### Tableau de bord système

L'écran de supervision affiche :
- Version de l'application
- Taille de la base de données
- Temps de fonctionnement (uptime)
- Statut de l'application

#### Journaux applicatifs

Les logs sont filtrables par niveau (`DEBUG`, `INFO`, `WARNING`, `ERROR`) et par texte libre.

Pour consulter les logs directement depuis Docker :
```bash
docker compose logs -f solde
```

Logs rotatifs dans `data/logs/solde.log`.

#### Journal d'audit

Le journal d'audit enregistre toutes les actions importantes (connexions, modifications, imports, sauvegardes, restaurations).

Il est consultable dans **Administration → Supervision système → Journal d'audit**.

---

### Opérations Docker courantes

```bash
# Démarrer
docker compose up -d

# Arrêter
docker compose stop

# Redémarrer
docker compose restart solde

# Arrêter et supprimer le conteneur (données conservées dans data/)
docker compose down

# Logs en temps réel
docker compose logs -f solde

# Ouvrir un shell dans le conteneur
docker compose exec solde sh

# Exécuter les migrations manuellement (normalement automatique)
docker compose exec solde python -m alembic upgrade head
```

---

### Exposer Solde derrière un reverse proxy (HTTPS)

Si vous souhaitez accéder à Solde via HTTPS depuis internet, configurez un reverse proxy (nginx, Traefik, ou DSM Application Portal sur Synology) qui pointe vers `http://localhost:8000`.

Exemple de configuration nginx :

```nginx
server {
    listen 443 ssl;
    server_name solde.votre-association.fr;

    ssl_certificate /etc/letsencrypt/live/solde.votre-association.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/solde.votre-association.fr/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
