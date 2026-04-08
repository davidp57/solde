# Plan : Solde ⚖️ — Application de gestion comptable associative

## TL;DR

Application web monolithique modulaire en Python (FastAPI + SQLite) pour gérer la comptabilité d'une association loi 1901 de soutien scolaire. Remplace deux fichiers Excel par une solution intégrée : facturation clients/fournisseurs, suivi des paiements multi-modes, gestion de caisse, rapprochement bancaire, et comptabilité en partie double avec génération automatique des écritures via un moteur de règles configurable. Déployée en Docker sur Synology (~384 Mo RAM max). Interface moderne responsive en Vue.js 3.

---

## Architecture technique

### Stack

| Composant | Choix | Justification RAM |
|---|---|---|
| Backend | **FastAPI** + Uvicorn (1 worker) | ~50-80 Mo idle |
| Base de données | **SQLite** (WAL mode) | ~0 Mo (fichier) |
| Frontend | **Vue.js 3** + PrimeVue + Vite | 0 Mo serveur (fichiers statiques) |
| ORM | **SQLAlchemy 2** (async) | Inclus dans le process Python |
| Migrations | **Alembic** | CLI, pas de RAM runtime |
| PDF | **WeasyPrint** | ~30-50 Mo pic pendant génération |
| Email | **smtplib** (stdlib Python) | 0 Mo additionnel |
| Auth | **JWT** (python-jose + passlib) | Inclus dans le process |
| Conteneur | **Docker** mono-container | 1 seul process |

**Estimation RAM totale : ~80-130 Mo idle, ~180 Mo pic (génération PDF) — bien sous les 384 Mo.**

### Structure du projet

```
comptasso/
├── docker-compose.yml
├── Dockerfile
├── backend/
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── config.py                  # Configuration (année comptable, SMTP, etc.)
│   ├── database.py                # Session SQLite + engine
│   ├── models/                    # Modèles SQLAlchemy
│   │   ├── contact.py             # Contacts (adhérents, fournisseurs)
│   │   ├── invoice.py             # Factures (clients + fournisseurs)
│   │   ├── payment.py             # Paiements
│   │   ├── cash_register.py       # Caisse
│   │   ├── bank.py                # Banque
│   │   ├── accounting.py          # Écritures, comptes, exercices
│   │   ├── accounting_rule.py     # Règles comptables configurables
│   │   ├── salary.py              # Salaires
│   │   └── user.py                # Utilisateurs + rôles
│   ├── routers/                   # Routes API par module
│   ├── services/                  # Logique métier par module
│   ├── schemas/                   # Pydantic schemas (validation)
│   ├── templates/                 # Templates HTML pour PDF (Jinja2)
│   └── alembic/                   # Migrations DB
├── frontend/
│   ├── src/
│   │   ├── views/                 # Pages Vue.js
│   │   ├── components/            # Composants réutilisables
│   │   ├── composables/           # Logique partagée
│   │   ├── stores/                # Pinia stores
│   │   └── api/                   # Client API (axios)
│   └── package.json
├── data/                          # Volume Docker : SQLite + fichiers uploadés
└── tests/
```

### Docker mono-container

- **1 seul Dockerfile** : build Vue.js → fichiers statiques servis par FastAPI (StaticFiles)
- **1 volume** : `./data:/app/data` (DB SQLite + factures fournisseurs uploadées + PDFs générés)
- **Portainer-compatible** : docker-compose.yml standard

---

## Modèle de données

### contacts
`id, type (client|fournisseur|les_deux), nom, prenom, email, telephone, adresse, notes, created_at`
- Un adhérent est un contact de type "client"
- Un sous-traitant/fournisseur est de type "fournisseur"

### invoices (factures)
`id, number (YYYY-NNNN), type (client|fournisseur), contact_id, date, due_date, label (cs|a|cs+a|general), description, total_amount, paid_amount (calculé), status (draft|sent|paid|partial|overdue|disputed), pdf_path, created_at`

### invoice_lines (lignes de facture)
`id, invoice_id, description, quantity, unit_price, amount`
- Permet des factures multi-lignes (ex: cours + adhésion sur même facture)

### payments
`id, invoice_id, contact_id, amount, date, method (especes|cheque|virement), cheque_number, reference, deposited (bool), deposit_date, notes, created_at`
- `deposited` : pour les chèques/espèces, indique si remis en banque

### cash_register (caisse)
`id, date, amount, type (in|out), contact_id, payment_id, reference, description, balance_after, created_at`

### cash_counts (comptages caisse)
`id, date, count_100, count_50, count_20, count_10, count_5, count_2, count_1, count_cents, total_counted, balance_expected, difference, notes`

### bank_transactions
`id, date, amount, reference, description, balance_after, reconciled (bool), reconciled_with, source (manual|import), created_at`

### deposits (bordereaux de remise)
`id, date, type (cheques|especes), total_amount, bank_reference, notes`
- Lié aux paiements via une table de liaison `deposit_payments`

### accounting_accounts (plan comptable)
`id, number (ex: 411100), label, type (actif|passif|charge|produit), parent_number, is_default (bool)`
- Pré-rempli avec le plan comptable associatif simplifié
- Extensible par l'utilisateur

### accounting_entries (écritures comptables)
`id, entry_number, date, account_id, label, debit, credit, fiscal_year_id, source_type (facture|paiement|salaire|banque|manuel|cloture), source_id, created_at`
- `source_type` + `source_id` : traçabilité vers l'opération d'origine
- Immuable une fois l'exercice clôturé

### accounting_rules (règles comptables configurables)
`id, name, trigger_type (invoice_client_cs|invoice_client_a|payment_especes|payment_cheque|payment_virement|deposit_especes|deposit_cheques|salary|subcontracting|bank_fees|manual), is_active (bool), priority, description`

### accounting_rule_entries (détail des règles)
`id, rule_id, account_number, side (debit|credit), amount_field (amount|gross_salary|net_salary|employer_charges|employee_charges), description_template`
- Chaque règle a N entrées qui définissent les écritures à générer
- `description_template` : template Jinja2 (ex: `{{invoice.number}} {{contact.nom}}`)

### fiscal_years (exercices comptables)
`id, name, start_date, end_date, status (open|closing|closed), opening_balance_entry_id`
- Défaut : août N → juillet N+1, configurable

### users
`id, username, email, password_hash, role (admin|tresorier|secretaire|readonly), is_active, created_at`

### salaries (suivi des salaires)
`id, employee_id (→ contacts), month (YYYY-MM), hours, gross, employee_charges, employer_charges, tax, net_pay, created_at`
- Données saisies manuellement depuis la plateforme CEA
- Coût total calculé (gross + employer_charges)

---

## Fonctionnalités détaillées

### Module 1 — Authentification & Configuration
- Login JWT avec refresh token
- Rôles : admin (tout), trésorier (gestion + compta), secrétaire (factures + paiements), readonly (consultation)
- Page de configuration : année comptable (défaut août→juillet), infos asso (nom, SIRET, adresse pour en-tête factures), paramètres SMTP, logo
- Configuration du plan comptable (ajouter/modifier des comptes)

### Module 2 — Contacts
- CRUD contacts avec type (client, fournisseur, les deux)
- Fiche contact : historique factures, paiements, solde dû
- Recherche et filtres
- Gestion des créances douteuses (marquage + transfert compte 416xxx)

### Module 3 — Factures clients
- Création de facture : sélection contact, type (cs/a/cs+a/général), lignes de facture, calcul automatique du total
- Numérotation automatique séquentielle YYYY-NNNN (configurable)
- États : Brouillon → Émise → Payée partiellement → Payée / En litige
- Génération PDF à partir d'un template HTML (logo, coordonnées asso, détail lignes, mentions légales « Association loi 1901, non assujettie à la TVA »)
- Envoi par email (SMTP) avec PDF en pièce jointe
- Duplication de facture (pour facturation récurrente)
- **Déclenchement automatique** des écritures comptables via le moteur de règles

### Module 4 — Factures fournisseurs
- Enregistrement : date, fournisseur, montant, description, référence
- Upload du fichier PDF/image de la facture
- Suivi de l'état de paiement
- Types : sous-traitance cours, fournitures, assurance, téléphone, frais divers
- **Déclenchement automatique** des écritures comptables

### Module 5 — Paiements
- Enregistrement d'un paiement sur une facture : montant, mode, date, N° chèque si applicable
- Paiement partiel possible (plusieurs paiements pour une facture)
- Mise à jour automatique du statut de la facture
- Vue "paiements à encaisser" : chèques et espèces non encore déposés en banque
- **Déclenchement automatique** des écritures comptables (selon le mode de paiement)

### Module 6 — Caisse (espèces)
- Journal de caisse : liste chronologique des mouvements (entrées paiements espèces, sorties remises banque + achats)
- Solde en temps réel
- **Comptage physique** : interface de saisie par coupure (100€, 50€, 20€, 10€, 5€, 2€, 1€, centimes) avec calcul automatique du total
- **Rapprochement** : comparaison solde comptable vs solde compté, affichage de la différence
- Historique des comptages

### Module 7 — Banque
- Journal du compte bancaire : mouvements avec solde glissant
- **Import de relevés** : CSV (format Crédit Mutuel), OFX/QIF
- Parsing intelligent des libellés importés
- Rapprochement bancaire : associer des transactions bancaires à des paiements/factures existants
- Création de **bordereaux de remise** (chèques / espèces) : sélection des paiements à remettre, calcul du total, marquage comme déposé (suivi interne uniquement)

### Module 8 — Moteur de règles comptables
- **Règles par défaut** pré-configurées (toutes celles identifiées dans les Excel)
- Interface d'édition : pour chaque type d'événement (facture cs, paiement espèces, etc.), définir les N écritures à générer
- Chaque écriture : compte source, sens (débit/crédit), champ montant source, template de libellé
- Possibilité de **désactiver/activer** une règle
- Possibilité d'**ajouter de nouveaux types** d'événements
- **Prévisualisation** : avant d'appliquer, montrer les écritures qui seraient générées
- Les règles sont appliquées automatiquement à chaque action de gestion (création facture, enregistrement paiement, remise en banque, etc.)

### Module 9 — Comptabilité
- **Journal général** : toutes les écritures, filtrable par date, compte, source
- **Balance des comptes** : synthèse débit/crédit/solde par compte
- **Grand livre** par compte (équivalent des extraits Clients, Caisse, Compte Courant actuels)
- **État des factures** : vue pivot montrant le solde de chaque facture
- Saisie manuelle d'écritures (pour les cas non couverts par les règles)
- Vérification de cohérence : total débits = total crédits
- Export des données (CSV, PDF)

### Module 10 — Clôture comptable
- Vérification pré-clôture : balance équilibrée, toutes les factures rapprochées
- Calcul du résultat (produits - charges) → écriture 120000 ou 129000
- Génération du bilan simplifié (actif/passif)
- Génération du compte de résultat (charges/produits)
- Report à nouveau → écriture 110000
- Verrouillage de l'exercice (plus de modifications possibles)
- Ouverture du nouvel exercice avec écritures d'à-nouveau
- Consultation des exercices clôturés en lecture seule

### Module 11 — Salaires
- Saisie mensuelle par employé des données issues de la plateforme CEA : heures, brut, charges patronales, charges salariales, impôts, net
- Calcul automatique du coût total (brut + charges patronales)
- Pas de calcul automatique des charges (fait par le CEA)
- Historique mensuel
- Sous-traitance : lien avec les factures fournisseurs des auto-entrepreneurs
- **Déclenchement automatique** des écritures comptables (641000, 645100, 421000, 431100, etc.)

### Module 12 — Import des données existantes
- Import des fichiers Excel actuels (Gestion 2025 + Comptabilité 2025)
- Mapping automatique des colonnes connues
- Validation et rapport d'erreurs avant import
- Import des contacts, factures, paiements, écritures comptables

### Module 13 — Dashboard
- Vue d'ensemble : solde banque, solde caisse, factures impayées, résultat en cours
- Graphiques simples : évolution des recettes/dépenses par mois
- Alertes : factures en retard, caisse non rapprochée depuis X jours

---

## Règles comptables par défaut (pré-configurées)

| Événement | Débit | Crédit |
|---|---|---|
| Facture client - cours (cs) | 411100 Adhérents | 706110 Cours de soutien |
| Facture client - adhésion (a) | 411100 Adhérents | 756000 Cotisations |
| Paiement reçu - espèces | 531000 Caisse | 411100 Adhérents |
| Paiement reçu - chèque | 511200 Chèques à encaisser | 411100 Adhérents |
| Paiement reçu - virement | 512100 Compte courant | 411100 Adhérents |
| Remise espèces en banque | 512100 Compte courant | 531000 Caisse |
| Remise chèques en banque | 512100 Compte courant | 511200 Chèques à encaisser |
| Facture fournisseur - sous-traitance | 611100 Sous-traitance | 401xxx Fournisseur |
| Paiement fournisseur - virement | 401xxx Fournisseur | 512100 Compte courant |
| Facture fournisseur - fournitures | 602250 Fournitures | 401xxx ou 531000 |
| Frais bancaires | 627000 Services bancaires | 512100 Compte courant |
| Salaire brut | 641000 Rémunérations | 421000 Rémunérations dues |
| Charges patronales | 645100 Cotisations URSSAF | 431100 URSSAF |
| Paiement salaire | 421000 Rémunérations dues | 512100 Compte courant |
| Paiement URSSAF | 431100 URSSAF | 512100 Compte courant |

---

## Fichiers clés à créer

### Backend
- `backend/main.py` — Point d'entrée, montage des routers + StaticFiles
- `backend/config.py` — Settings Pydantic (DB path, JWT secret, SMTP, année comptable)
- `backend/database.py` — AsyncSession SQLite WAL
- `backend/models/*.py` — 12 fichiers de modèles SQLAlchemy
- `backend/routers/*.py` — 12 fichiers de routes (1 par module)
- `backend/services/*.py` — 12 fichiers de logique métier
- `backend/services/accounting_engine.py` — Moteur de règles comptables (le cœur)
- `backend/services/pdf_generator.py` — Génération PDF via WeasyPrint
- `backend/services/bank_import.py` — Parser CSV/OFX pour import relevés
- `backend/services/excel_import.py` — Import des fichiers Excel existants
- `backend/schemas/*.py` — Validation Pydantic
- `backend/templates/invoice.html` — Template Jinja2 pour factures PDF

### Frontend
- `frontend/src/views/Login.vue`
- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/Contacts.vue` + `ContactDetail.vue`
- `frontend/src/views/Invoices.vue` + `InvoiceForm.vue` + `InvoiceDetail.vue`
- `frontend/src/views/Payments.vue` + `PaymentForm.vue`
- `frontend/src/views/CashRegister.vue` + `CashCount.vue`
- `frontend/src/views/Bank.vue` + `BankImport.vue` + `BankReconciliation.vue`
- `frontend/src/views/Deposits.vue` + `DepositForm.vue`
- `frontend/src/views/Accounting.vue` + `Journal.vue` + `Balance.vue` + `Ledger.vue`
- `frontend/src/views/AccountingRules.vue` + `RuleEditor.vue`
- `frontend/src/views/FiscalYearClose.vue`
- `frontend/src/views/Salaries.vue`
- `frontend/src/views/Settings.vue`
- `frontend/src/views/ImportExcel.vue`

### Infra
- `Dockerfile` — Multi-stage : build Vue.js + Python runtime
- `docker-compose.yml` — 1 service, 1 volume, port mapping
- `.env.example` — Variables d'environnement

---

## Vérification globale

1. **Tests unitaires** (pytest) : logique métier critique — moteur de règles, calculs salaires, numérotation factures, clôture comptable
2. **Tests d'intégration** : workflows complets (facture → paiement → écriture → balance)
3. **Test Docker** : `docker-compose up` depuis zéro → app fonctionnelle
4. **Test RAM** : `docker stats` en charge → vérifier < 384 Mo
5. **Test responsive** : vérifier toutes les vues sur mobile (Chrome DevTools)
6. **Test import Excel** : importer les fichiers réels → vérifier cohérence
7. **Test de clôture** : clôturer un exercice complet → vérifier bilan et compte de résultat
8. **Test SMTP** : envoyer une facture par email

---

## Décisions prises

- **Monolithe modulaire** plutôt que microservices (priorité RAM)
- **SQLite** plutôt que PostgreSQL (0 Mo RAM additionnel, suffisant pour le volume)
- **Vue.js 3 + PrimeVue** pour le frontend (composants riches : DataTable, Calendar, Dialog — look SaaS moderne)
- **Plan comptable associatif simplifié** (extensible)
- **Import fichiers CSV/OFX** pour la banque (pas de connexion API DSP2 pour le MVP)
- **Non assujetti TVA** : pas de gestion TVA
- **Euros uniquement**
- **Format YYYY-NNNN** pour la numérotation des factures
- **Salaires** : saisie manuelle des données CEA (heures, brut, charges, impôts, net)
- **Bordereaux de remise** : suivi interne uniquement, pas de PDF
- **Exercices clôturés** : consultables en lecture seule

## Scope explicitement exclu

- Connexion API bancaire (DSP2/Open Banking)
- Gestion de la TVA
- Multi-devises
- Export FEC (Fichier des Écritures Comptables) — pourra être ajouté facilement
- Gestion des subventions (module dédié)
- Budget prévisionnel automatisé
- Application mobile native
