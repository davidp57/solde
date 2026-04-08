# Roadmap — Solde ⚖️

## Vue d'ensemble

```
Phase 1          Phase 2        Phase 3          Phase 4              Phase 5           Phase 6
Fondations  ──►  Gestion   ──►  Facturation ──►  Paiements &     ──►  Comptabilité ──►  Avancé
                 de base                         Trésorerie
├─ Docker        ├─ Contacts    ├─ Fact. clients  ├─ Paiements         ├─ Moteur règles   ├─ Clôture
├─ FastAPI       └─ Plan        ├─ Fact. fourn.   ├─ Caisse            ├─ Journal         ├─ Salaires
├─ SQLite          comptable    ├─ PDF            ├─ Comptage caisse   ├─ Balance         ├─ Import Excel
├─ Auth JWT                     └─ Email          ├─ Banque            ├─ Grand livre     └─ Dashboard
└─ Vue.js                                         ├─ Bordereaux        └─ Saisie manuelle
                                                  ├─ Import CSV/OFX
                                                  └─ Rapprochement
```

---

## Phase 1 — Fondations

> **Objectif** : infrastructure fonctionnelle de bout en bout (Docker → login → page de config)

| # | Tâche | Détails |
|---|---|---|
| 1.1 | Setup projet | Structure de dossiers, `.gitignore`, `pyproject.toml`, `.env.example` |
| 1.2 | Docker | `Dockerfile` multi-stage (build Vue.js + Python runtime), `docker-compose.yml` (1 service, 1 volume `./data`) |
| 1.3 | Backend FastAPI | `main.py`, `config.py` (Settings Pydantic), `database.py` (SQLite WAL, AsyncSession) |
| 1.4 | Alembic | Init, première migration avec modèle `User` |
| 1.5 | Auth JWT | Login/logout, refresh token, middleware de vérification, modèle User + rôles (admin, trésorier, secrétaire, readonly) |
| 1.6 | Frontend scaffold | Vue.js 3 + Vite + PrimeVue + Pinia + Vue Router, layout responsive (sidebar + topbar), page de login |
| 1.7 | Page de configuration | Infos asso (nom, SIRET, adresse, logo), année comptable (défaut août→juillet), paramètres SMTP |
| 1.8 | Servir le frontend | FastAPI `StaticFiles` pour servir le build Vue.js |

**Critère de validation** : `docker-compose up` → navigateur → login → page de configuration fonctionnelle

### Dépendances
- Aucune (point de départ)

---

## Phase 2 — Gestion de base

> **Objectif** : pouvoir gérer les contacts et le plan comptable

| # | Tâche | Détails |
|---|---|---|
| 2.1 | Modèle Contact | SQLAlchemy : type (client\|fournisseur\|les_deux), nom, prénom, email, téléphone, adresse, notes |
| 2.2 | API Contacts | CRUD REST, recherche, filtres par type |
| 2.3 | Vue Contacts | Liste (DataTable PrimeVue), création/édition (Dialog), fiche contact avec historique |
| 2.4 | Modèle AccountingAccount | SQLAlchemy : numéro, label, type (actif\|passif\|charge\|produit), parent |
| 2.5 | Plan comptable par défaut | Seed des 24 comptes identifiés dans les Excel |
| 2.6 | API Plan comptable | CRUD REST, import du plan par défaut |
| 2.7 | Vue Plan comptable | Liste arborescente, ajout/modification de comptes |

**Critère de validation** : créer, modifier, rechercher, supprimer des contacts et des comptes comptables

### Dépendances
- Phase 1 (auth + DB)

---

## Phase 3 — Facturation

> **Objectif** : créer des factures, générer des PDF, envoyer par email

| # | Tâche | Détails |
|---|---|---|
| 3.1 | Modèle Invoice + InvoiceLine | Numéro YYYY-NNNN, type client/fournisseur, label (cs\|a\|cs+a\|general), lignes multi, statuts |
| 3.2 | API Factures clients | CRUD, numérotation auto séquentielle, changement de statut, duplication |
| 3.3 | Vue Factures clients | Liste filtrable (statut, date, contact), formulaire de création/édition avec lignes dynamiques |
| 3.4 | API Factures fournisseurs | CRUD, upload fichier PDF/image |
| 3.5 | Vue Factures fournisseurs | Liste, formulaire avec upload, prévisualisation du fichier |
| 3.6 | Génération PDF | WeasyPrint + template Jinja2 : logo asso, coordonnées, détail lignes, mention « Loi 1901, non assujettie à la TVA » |
| 3.7 | Envoi email | Configuration SMTP, envoi facture PDF en pièce jointe |

**Critère de validation** : créer une facture client cs+a → générer le PDF → l'envoyer par email → la retrouver dans la liste ; enregistrer une facture fournisseur avec un fichier joint

### Dépendances
- Phase 2 (contacts pour `contact_id`)

---

## Phase 4 — Paiements & Trésorerie

> **Objectif** : gérer le cycle de vie complet des paiements (réception → dépôt → banque)

| # | Tâche | Détails |
|---|---|---|
| 4.1 | Modèle Payment | Montant, mode (espèces\|chèque\|virement), N° chèque, dates, statut de dépôt |
| 4.2 | API Paiements | Enregistrement sur facture, paiement partiel, mise à jour auto du statut facture |
| 4.3 | Vue Paiements | Liste par facture et globale, formulaire, vue "à encaisser" |
| 4.4 | Modèle CashRegister + CashCount | Mouvements caisse (in/out), comptages physiques par coupure |
| 4.5 | API Caisse | Journal auto-alimenté par paiements espèces, saisie manuelle de sorties, comptage + rapprochement |
| 4.6 | Vue Caisse | Journal avec solde glissant, interface de comptage par coupure (100€→centimes), affichage différence |
| 4.7 | Modèle BankTransaction | Date, montant, référence, libellé, solde, source (manual\|import), rapprochement |
| 4.8 | API Banque | Journal, saisie manuelle, solde glissant |
| 4.9 | Modèle Deposit | Bordereaux de remise (chèques/espèces), liaison avec paiements |
| 4.10 | API Bordereaux | Création (sélection de paiements non déposés), marquage des paiements comme déposés |
| 4.11 | Vue Bordereaux | Sélection interactive des paiements, récapitulatif chèques + décomposition billets |
| 4.12 | Import relevés bancaires | Parser CSV format Crédit Mutuel + OFX/QIF |
| 4.13 | Vue Import bancaire | Upload fichier, prévisualisation, import |
| 4.14 | Rapprochement bancaire | API + vue pour associer transactions importées ↔ paiements/factures existants |

**Critère de validation** :
1. Enregistrer un paiement espèces → visible en caisse → faire un comptage physique → rapprochement OK
2. Créer un bordereau d'espèces → remettre en banque → visible au compte bancaire
3. Importer un CSV Crédit Mutuel → rapprocher les transactions

### Dépendances
- Phase 3 (factures pour `invoice_id`)

---

## Phase 5 — Comptabilité

> **Objectif** : génération automatique des écritures comptables et vues comptables

| # | Tâche | Détails |
|---|---|---|
| 5.1 | Modèle AccountingRule + AccountingRuleEntry | Règle : trigger_type, priorité, actif ; Entrée : compte, sens, champ montant, template libellé |
| 5.2 | Modèle AccountingEntry + FiscalYear | Écritures (double entrée, traçabilité source), exercices comptables |
| 5.3 | Moteur de règles | Service `accounting_engine.py` : prend un événement → applique les règles → génère les écritures |
| 5.4 | Seed règles par défaut | 15 règles pré-configurées (facture cs, paiement espèces, etc.) |
| 5.5 | Intégration automatique | Hook dans les services factures/paiements/dépôts → appel moteur de règles |
| 5.6 | API Règles comptables | CRUD, activation/désactivation, prévisualisation |
| 5.7 | Vue Règles comptables | Liste des règles, éditeur visuel (drag-and-drop lignes d'écriture), prévisualisation |
| 5.8 | API Journal général | Liste écritures, filtres (date, compte, source, exercice) |
| 5.9 | Vue Journal | DataTable avec filtres avancés, lien vers la source (facture, paiement...) |
| 5.10 | API Balance des comptes | Calcul agrégé débit/crédit/solde par compte |
| 5.11 | Vue Balance | Tableau synthétique avec totaux, drill-down vers grand livre |
| 5.12 | API Grand livre | Extrait par compte avec solde glissant |
| 5.13 | Vue Grand livre | Similaire aux feuilles "Extrait Clients", "Extrait Caisse", "Extrait Compte Courant" actuelles |
| 5.14 | État des factures | Vue pivot : solde de chaque facture (débit, crédit, reste dû) |
| 5.15 | Saisie manuelle | API + formulaire pour écritures manuelles (cas exceptionnels) |
| 5.16 | Export | CSV et PDF des vues comptables |

**Critère de validation** :
1. Créer une facture cs → 2 écritures auto générées (411100/706110) → visibles dans le journal → balance impactée
2. Enregistrer un paiement espèces → 2 écritures auto (531000/411100) → facture soldée dans l'état des factures
3. Modifier une règle → vérifier que les nouvelles écritures suivent la nouvelle règle

### Dépendances
- Phase 4 (tous les événements de gestion qui déclenchent les écritures)

---

## Phase 6 — Fonctions avancées

> **Objectif** : clôture comptable, salaires, import des données existantes, dashboard

| # | Tâche | Détails |
|---|---|---|
| 6.1 | Modèle FiscalYear (compléments) | Statuts open→closing→closed, écritures de clôture et report |
| 6.2 | API Clôture | Vérifications pré-clôture, calcul résultat, génération bilan + compte de résultat, verrouillage |
| 6.3 | Vue Clôture | Wizard étape par étape : vérifications → résultat → bilan → verrouillage → ouverture nouvel exercice |
| 6.4 | Report à nouveau | Écritures d'à-nouveau automatiques pour le nouvel exercice |
| 6.5 | Consultation exercices clôturés | Filtrage par exercice dans toutes les vues comptables, lecture seule |
| 6.6 | Modèle Salary | Mois, heures, brut, charges patronales, charges salariales, impôts, net (données CEA) |
| 6.7 | API Salaires | CRUD mensuel, lien sous-traitance → factures fournisseurs |
| 6.8 | Vue Salaires | Tableau mensuel par employé, historique, coût total, lien sous-traitants |
| 6.9 | Écritures salaires | Intégration moteur de règles pour les salaires (641000, 645100, 421000, 431100) |
| 6.10 | Import Excel | Parser Gestion 2025.xlsx + Comptabilité 2025.xlsx, mapping colonnes, validation |
| 6.11 | Vue Import Excel | Upload, prévisualisation, rapport de validation, confirmation import |
| 6.12 | Dashboard | Indicateurs clés (solde banque, solde caisse, impayés, résultat en cours) |
| 6.13 | Dashboard — graphiques | Évolution recettes/dépenses par mois (Chart.js ou vue-chartjs) |
| 6.14 | Dashboard — alertes | Factures en retard, caisse non rapprochée, échéances |

**Critère de validation** :
1. Clôturer l'exercice → bilan + compte de résultat cohérents → report à nouveau → nouvel exercice ouvert
2. Saisir un salaire mensuel → écritures comptables auto générées
3. Importer les 2 fichiers Excel réels → vérifier que les données importées correspondent aux originaux
4. Dashboard affiche les bons indicateurs et alertes

### Dépendances
- Phase 5 (comptabilité complète nécessaire pour la clôture)

---

## Résumé des livrables par phase

| Phase | Modules | Tâches |
|---|---|---|
| **1. Fondations** | Auth, Config | 8 tâches |
| **2. Gestion de base** | Contacts, Plan comptable | 7 tâches |
| **3. Facturation** | Factures clients, Factures fournisseurs, PDF, Email | 7 tâches |
| **4. Paiements & Trésorerie** | Paiements, Caisse, Banque, Bordereaux, Import bancaire, Rapprochement | 14 tâches |
| **5. Comptabilité** | Moteur de règles, Journal, Balance, Grand livre, État factures | 16 tâches |
| **6. Avancé** | Clôture, Salaires, Import Excel, Dashboard | 14 tâches |
| **Total** | **13 modules** | **66 tâches** |

---

## Diagramme de dépendances

```
Phase 1 (Fondations)
    │
    ▼
Phase 2 (Contacts + Plan comptable)
    │
    ▼
Phase 3 (Facturation)
    │
    ▼
Phase 4 (Paiements & Trésorerie)
    │
    ▼
Phase 5 (Comptabilité + Moteur de règles)
    │
    ▼
Phase 6 (Clôture + Salaires + Import + Dashboard)
```

> Chaque phase dépend de la précédente. Au sein d'une phase, certaines tâches sont parallélisables (ex: 2.1-2.3 Contacts et 2.4-2.7 Plan comptable).
