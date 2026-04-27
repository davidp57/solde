# Configuration — Solde ⚖️

---

La configuration de Solde se fait à deux niveaux :

1. **Variables d'environnement** (fichier `.env`) — paramètres techniques de démarrage.
2. **Paramètres de l'association** (interface web) — informations métier stockées en base.

---

### Variables d'environnement

#### Obligatoires

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Clé de signature JWT. Chaîne aléatoire d'au moins 32 caractères. Ne jamais utiliser la valeur par défaut en production. |
| `DATABASE_URL` | URL SQLite. En déploiement Docker standard, garder `sqlite+aiosqlite:///app/data/solde.db` (chemin dans le volume monté sur `/app/data`). |

#### Administrateur bootstrap

Ces variables ne s'appliquent qu'au tout premier démarrage, uniquement si la base ne contient encore aucun utilisateur.

| Variable | Défaut | Description |
|---|---|---|
| `ADMIN_USERNAME` | `admin` | Identifiant du compte administrateur créé au démarrage. |
| `ADMIN_PASSWORD` | `changeme` | Mot de passe initial. À changer immédiatement. Minimum 8 caractères, au moins une majuscule et un chiffre ASCII. |
| `ADMIN_EMAIL` | `admin@exemple.fr` | E-mail du compte administrateur. |

#### Mode de fonctionnement

| Variable | Défaut | Description |
|---|---|---|
| `DEBUG` | `false` | Active les messages d'erreur détaillés et expose Swagger UI. Ne jamais activer en production. |
| `SWAGGER_ENABLED` | `false` | Expose Swagger UI (`/api/docs`) et ReDoc (`/api/redoc`) indépendamment de `DEBUG`. Utile pour des sessions d'intégration temporaires. |
| `FISCAL_YEAR_START_MONTH` | `8` | Premier mois de l'exercice comptable (1 = janvier, 8 = août). |

#### Développement uniquement

| Variable | Description |
|---|---|
| `ENABLE_TEST_IMPORT_SHORTCUTS` | Active des raccourcis d'import pour les tests automatisés. Ne jamais activer en production. |
| `TEST_IMPORT_*` | Variables associées aux raccourcis de test. |

---

### Paramètres de l'association (interface web)

Accès : menu **Paramètres** (compte administrateur uniquement).

Ces paramètres sont stockés en base de données et prennent effet immédiatement, sans redémarrer le conteneur.

#### Informations de l'association

| Paramètre | Description |
|---|---|
| Nom de l'association | Affiché dans les en-têtes de factures, e-mails et PDF. |
| Adresse | Adresse postale complète (multi-lignes). |
| SIRET | Numéro SIRET affiché sur les factures. |
| Logo | Image uploadée, affichée sur les PDF de factures. Format accepté : PNG, JPEG, WebP. |
| Objet social | Description courte de l'activité de l'association. |

#### Numérotation des factures

| Paramètre | Description | Exemple |
|---|---|---|
| Template factures clients | Format `{year}` et `{seq}` | `{year}-{seq}` → `2026-001` |
| Longueur du numéro de séquence | Nombre de chiffres pour `{seq}` | `3` → `001`, `4` → `0001` |
| Template factures fournisseurs | Format `strftime` Python | `FF-%Y%m%d%H.%M.%S` → `FF-20260427` |

#### Délai d'échéance par défaut

| Paramètre | Description |
|---|---|
| Délai d'échéance factures (jours) | Nombre de jours ajoutés à la date de facture pour calculer l'échéance automatiquement (0–365). |

#### Prix unitaires par défaut

Ces prix sont pré-remplis automatiquement dans les formulaires de facture selon le type de ligne.

| Paramètre | Type de ligne |
|---|---|
| Prix par défaut — cours | Ligne de type "cours" |
| Prix par défaut — adhésion | Ligne de type "adhésion" |
| Prix par défaut — autres | Ligne de type "autres" |

#### Configuration SMTP

Paramètres pour l'envoi d'e-mails (factures, notifications).

| Paramètre | Description |
|---|---|
| Serveur SMTP | Adresse du serveur (ex. `smtp.gmail.com`) |
| Port | Port SMTP (ex. `587` pour STARTTLS, `465` pour SSL) |
| Utiliser SSL/TLS | Activer SSL direct (port 465 typiquement) |
| Identifiant SMTP | Adresse e-mail ou identifiant du compte |
| Mot de passe SMTP | Mot de passe ou mot de passe d'application |
| E-mail expéditeur | Adresse affichée comme expéditeur |
| BCC | Adresse en copie cachée pour toutes les factures envoyées (optionnel) |

---

### Initialisation de l'application

Après la première connexion, voici les étapes de configuration recommandées dans l'ordre :

1. **Changer le mot de passe** du compte administrateur bootstrap.
2. **Renseigner les paramètres de l'association** (nom, adresse, SIRET, logo).
3. **Configurer le SMTP** si vous souhaitez envoyer des factures par e-mail.
4. **Créer les exercices comptables** couvrant les périodes à gérer.
5. **Importer le plan comptable** ou créer les comptes nécessaires.
6. **Créer les règles comptables** pour l'automatisation des écritures.
7. **Créer les comptes utilisateurs** pour les autres membres de l'équipe.
8. **Importer les données historiques** si nécessaire (voir [excel-import.fr.md](./excel-import.fr.md)).

---

### Exercice comptable

L'exercice comptable détermine la période de référence pour les écrans de comptabilité.

- Créez au moins un exercice avant de saisir des données.
- Plusieurs exercices peuvent coexister (passés, en cours, futurs).
- Un seul exercice peut être "en cours" à un moment donné.
- La clôture d'un exercice est irréversible : effectuez-la uniquement lorsque toutes les opérations de la période sont enregistrées.
