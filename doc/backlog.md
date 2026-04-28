<!-- markdownlint-disable MD033 -->
# Backlog — Solde ⚖️

Backlog produit pour Solde ⚖️ — gestion comptable associative.
Quand le travail démarre sur un sujet, créer une branche `feature/` depuis `develop`.
Quand un sujet est livré, mettre à jour `CHANGELOG.md` et passer le ticket en ✅ Fait ici.

---

## Lots actifs

### Lot H — Architecture multi-compte (~45 min) — v0.9

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| BIZ-034 | Support multi-compte banque | P3 | ~45 min | 2026-04-21 | | |

## Hors lots

| ID | Titre | Prio | Est. | Créé | Terminé |
| --- | --- | --- | --- | --- | --- |
| CHR-078 | Squelette i18n anglais | P3 | ~5 min | 2026-04-23 | — |
| BIZ-128 | Modèles d'e-mail configurables dans les paramètres | P2 | ~30 min | 2026-05-02 | 2026-05-02 |
| BIZ-129 | Notes de crédit (avoirs) | P2 | ~3 h | 2026-04-27 | — |
| BIZ-130 | Confirmation de dépôt bancaire + métriques espèces/chèques | P2 | ~2 h | 2026-05-02 | 2026-05-02 |

---

## Détails

### BIZ-125 — Chatbot IA + page Aide

Deux fonctionnalités complémentaires autour de la documentation embarquée :

**1. Page Aide (`/aide`)**
- Route dédiée accessible depuis la navigation (tous rôles)
- Affiche `doc/user/manuel.md` rendu en HTML via `marked` côté frontend
- Servi par le backend : `GET /api/help/manual` (lecture du fichier Markdown)
- Table des matières auto-générée depuis les titres

**2. Sidebar chatbot Gemini**
- Panneau latéral ouvrable/fermable depuis un bouton persistant dans la nav
- Provider : Google Gemini Flash (tier gratuit — 15 req/min, 1 M tokens/jour) ; OpenAI en alternative
- System prompt = `doc/llm/reference.md` + `doc/user/manuel.md` injectés au début de chaque session — aucune donnée comptable transmise
- Clé API stockée dans `AppSettings` (colonnes `chat_provider`, `chat_api_key`, `chat_model`) — éditable par l’admin dans les paramètres, jamais renvoyée dans les réponses API (comme `smtp_password`)
- `POST /api/chat` : reçoit `{messages}`, ajoute le system prompt, proxifie vers le LLM, renvoie en streaming SSE
- Historique en mémoire session (non persisté) ; réinitialisé à la fermeture
- Si `CHAT_API_KEY` absent : bouton masqué

**Périmètre backend :**
- `backend/services/chat_service.py` : injection system prompt, appel LLM, streaming
- `backend/routers/chat.py` : `POST /api/chat` (auth requise), `GET /api/help/manual`
- Colonnes `AppSettings` : `chat_provider` (`gemini` | `openai`, défaut `gemini`), `chat_api_key` (nullable), `chat_model` (nullable)
- Migration Alembic 0035 dédiée
- `chat_api_key` exclue du schéma `AppSettingsRead` (même pattern que `smtp_password`)

**Périmètre frontend :**
- `HelpView.vue` + route `/aide`
- `SettingsChatPanel.vue` (nouvelle section dans les paramètres admin)
- `ChatSidebar.vue` (panneau latéral, ouvrable/fermable)
- Store Pinia léger (état ouvert/fermé + historique)
- Dépendance : `marked` (rendu Markdown)
- Clés i18n pour les libellés

**Audit des questions :**
- Chaque question utilisateur est enregistrée dans une table `chat_log` (migration Alembic dédiée)
- Colonnes : `id`, `user_id` (FK → User), `asked_at`, `question` (texte brut), `prompt_tokens`, `completion_tokens`
- Endpoint `GET /api/chat/logs` réservé aux admins (pagination, filtre par utilisateur / période)
- Aucune réponse du LLM ni donnée métier n’est stockée dans le log

**Hors périmètre :** persistance de l’historique complet, multi-utilisateurs, fine-tuning, TTS/STT.

### BIZ-126 — Refactor UX écran Paramètres

L’écran Paramètres contient 4 panels dont deux devenus trop longs (413 et 322 lignes) et
mélangeant des responsabilités distinctes. L’ajout du panel Chatbot (BIZ-125) est le bon
moment pour réorganiser.

**Découpage cible :**
| Composant | Contenu actuel | Action |
|---|---|---|
| `SettingsAssociationSmtpPanel` | Infos assoc. + SMTP + Logo | Scinder en 2 |
| `SettingsAssociationPanel` (nouveau) | Nom, adresse, SIRET, logo | Créer |
| `SettingsSmtpPanel` (nouveau) | SMTP (hôte, port, user, mdp, TLS, BCC) | Extraire |
| `SettingsSystemOpeningPanel` | Banque + Caisse + Année fiscale + Numérotation + Prix | Réorganiser |
| `SettingsChatPanel` (nouveau) | Provider, clé API, modèle (admin only) | Créer (BIZ-125) |
| `SettingsBackupPanel` | Sauvegarde | Inchangé |
| `SettingsDangerZonePanel` | Zone danger | Inchangé |

**Ordre final des panels dans `SettingsView.vue` :**
1. Association — 2. SMTP — 3. Ouverture système — 4. IA / Chatbot — 5. Sauvegarde — 6. Zone danger

**Périmètre :** refactoring pur (pas de changement fonctionnel) + clés i18n à conserver.
Fait sur la même branche que BIZ-125 (`feature/biz-125-chatbot-aide`).

### BIZ-034 — Support multi-compte banque

Distinguer compte courant et compte épargne dans les données, imports et écrans.
Décisions métier nécessaires avant implémentation.

### CHR-078 — Squelette i18n anglais

Créer `en.ts` avec les clés structurelles pour préparer la localisation anglaise.

---

### BIZ-129 — Notes de crédit (avoirs)

Permettre l'émission d'un avoir (note de crédit) pour annuler partiellement ou totalement une facture client.

**Contexte :** un avoir est comptablement un document à total négatif. La contrainte actuelle `total ≥ 0` est correcte pour une facture ordinaire mais invalide pour un avoir. Il faut distinguer les deux types.

**Périmètre backend :**
- Ajouter `invoice_type: Mapped[str]` sur le modèle `Invoice` — valeurs `facture` (défaut) | `avoir`
- Migration Alembic dédiée (`0038_add_invoice_type`)
- Lever la contrainte de total négatif uniquement pour les avoirs (validation dans le service)
- Numérotation séparée : séquence `AV-YYYY-NNN` (nouvelle colonne ou préfixe dans le service de numérotation)
- Nouveau endpoint `POST /api/invoices/{id}/credit-note` : crée un avoir pré-rempli avec les lignes inversées et un lien `credit_note_for_id` vers la facture d'origine (nullable, optionnel dans un premier temps)
- Schémas : exposer `invoice_type` dans `InvoiceRead` / `InvoiceCreate` / `InvoiceUpdate`

**Périmètre frontend :**
- Bouton « Créer un avoir » sur les factures envoyées/payées (pas sur les brouillons)
- Badge / libellé « Avoir » dans les listes et en-tête du formulaire d'édition
- Template PDF avoir : en-tête « NOTE DE CRÉDIT » / « AVOIR » à la place de « FACTURE »
- Validation côté UI : bloquer le total ≥ 0 seulement pour `invoice_type === 'facture'`

**Hors périmètre (V1) :** lien de réconciliation automatique avoir ↔ facture, lettrage comptable, workflow de validation spécifique.



## Lots terminés

| Lot | Nom | Version | Tickets | Terminé |
| --- | --- | --- | --- | --- |
| 1 | Quick wins P3 | v0.2 | CHR-064, CHR-062, TEC-066, TEC-063 | 2026-04-22 |
| 2 | Tests au vert | v0.2 | TEC-048 | 2026-04-22 |
| 3 | Sécurité sans impact structurel | v0.2 | TEC-047, TEC-052, TEC-055, TEC-060, TEC-051 | 2026-04-22 |
| 4 | Qualité backend sans impact API | v0.2 | TEC-065, TEC-057, TEC-059 | 2026-04-22 |
| 5 | Sécurité auth (full-stack) | v0.2 | TEC-045, BIZ-053, TEC-046 | 2026-04-22 |
| 6 | DevOps Docker | v0.2 | CHR-054, CHR-061 | 2026-04-22 |
| 7 | Refactoring structurel | v0.2 | TEC-050, TEC-058 | 2026-04-22 |
| 8 | Chantiers longs | v0.2 | BIZ-056, TEC-049 | 2026-04-22 |
| A | Backend rapide | v0.3 | TEC-085 | 2026-04-23 |
| B | UX quick wins | v0.3 | BIZ-070, BIZ-072, BIZ-074, BIZ-084, BIZ-042 | 2026-04-23 |
| C | Dashboard interactif | v0.3 | BIZ-075, BIZ-073 | 2026-04-23 |
| D | Polish UI | v0.3 | BIZ-071, BIZ-043 | 2026-04-23 |
| F | Tests | v0.4 | TEC-079, TEC-080, TEC-081 | 2026-04-24 |
| G | Refactoring frontend | v0.5 | TEC-077 | 2026-04-24 |
| I | Polish UI & contacts | v0.5 | BIZ-035, BIZ-037, CHR-038, BIZ-040 | 2026-04-24 |
| J | CI GitHub Actions | v0.5 | CHR-086, CHR-087 | 2026-04-24 |
| K | Documentation & Swagger | v0.5 | CHR-019, CHR-082 | 2026-04-24 |
| L | Gestion employés | v0.6 | BIZ-088 | 2026-04-25 |
| M | Sécurité applicative | v0.6 | TEC-091, TEC-092, TEC-093 | 2026-04-25 |
| N | UX & formulaires | v0.7 | BIZ-094, BIZ-095, BIZ-096, BIZ-097 | 2026-04-25 |
| Q | Recette post-merge N | v0.7 | voir doc/recette.md (REC-001..REC-015) | 2026-04-26 |
| R | Supervision système & audit | v0.8 | BIZ-108, BIZ-109 | 2026-04-26 |
| O | Qualité technique backend | v0.7 | TEC-098, TEC-099, TEC-100 | 2026-04-26 |
| P | Qualité technique frontend | v0.7 | TEC-101, TEC-102, TEC-103, TEC-104 | 2026-04-26 |
| S | Documentation & i18n | v0.8 | TEC-106, CHR-021, CHR-020, CHR-079 | 2026-04-27 |
| T | Chatbot IA + refactor Paramètres | v0.8 | BIZ-125, BIZ-126 | 2026-04-27 |

<details>
<summary>Lot S — Documentation & i18n (2026-04-27)</summary>

### TEC-106 — Audit et complétion des clés i18n manquantes

Audit complet des 1 096 clés `t('...')` utilisées dans le frontend (1 358 appels bruts filtrés). Résultat : 2 clés manquantes (`common.active`, `common.inactive`) utilisées dans `EmployeesView.vue` — ajoutées dans `fr.ts`.

### CHR-020 — Documentation de contribution

`doc/dev/contributing.md` : setup local, `dev.ps1`, quality gate backend/frontend, conventions Git et workflow. Validé via PR #54.

### CHR-021 — Manuel utilisateur illustré

Manuel FR `doc/user/manuel.md` + référence LLM `doc/llm/reference.md`. Version textuelle complète, structure par rôle et parcours métier. Illustrations (captures annotées) reportées à une future itération.

### CHR-079 — Restructuration et nettoyage de la documentation

Restructuration complète du répertoire `doc/` : nouvelles arborescences `doc/admin/`, `doc/dev/`, `doc/user/`, `doc/llm/` ; suppression de 25 fichiers obsolètes ; README par section ; split des docs bilingues en fichiers par langue (`*.fr.md` / `*.en.md`). Corrections factuelles : `DATABASE_URL`, Vue Router 5, fixtures de test, durée de session, rôles règles comptables, version sync.

</details>

Tickets fermés hors lots : TEC-067, TEC-068, BIZ-069, BIZ-076, CHR-083, BIZ-036, BIZ-041, BIZ-033, BIZ-088, BIZ-089, BIZ-090, TEC-105, TEC-039, BIZ-106, BIZ-107, TEC-110, BIZ-108, BIZ-109, BIZ-112, BIZ-113, BIZ-114, BIZ-115, BIZ-116, BIZ-118, BIZ-121, BIZ-117, **BIZ-119**, **BIZ-123**, **BIZ-124**, **BIZ-122**, **BIZ-111**, **BIZ-127**, **BIZ-128**, **BIZ-130**.
Tickets fermés pré-audit : CHR-001, CHR-002, BIZ-003 – BIZ-018, BIZ-022 – BIZ-023.

<details>
<summary>Tickets fermés hors lots — détails (BIZ-111, BIZ-117, BIZ-119, BIZ-123, BIZ-124)</summary>

### BIZ-111 — Import one-shot adresses postales depuis factures Word

- **Terminé** : 2026-04-26
- **Livré** : script `scripts/import_addresses_from_docx.py` — extrait les adresses postales depuis les factures Word historiques et enrichit `Contact.adresse` (dry-run par défaut, `--commit` pour appliquer). 48 contacts mis à jour. Dépendance `python-docx` ajoutée dans `pyproject.toml`. Amélioration associée : affichage de l'adresse dans le PDF facture + suppression du SIRET en doublon dans la section Émetteur.

### BIZ-117 — Assistant IA intégré

**Clôturé ❌ Non réalisable** — intégration d'un LLM tiers exclue pour raisons de confidentialité des données comptables ; modèle local incompatible avec la contrainte RAM ≤ 384 MB du NAS.

### BIZ-119 — Tableau de bord avec cartes d'actions rapides

- **Terminé** : 2026-04-26
- **Livré** : panneau « Actions rapides » en haut du dashboard — 3 cartes (facture client, paiement, caisse) ouvrant des wizards de saisie inline ; wizard facture client avec confirmation et bouton « Saisir une autre ».

### BIZ-123 — Prix par défaut par type de ligne de facture

- **Terminé** : 2026-04-26
- **Livré** : colonnes `default_price_cours`, `default_price_adhesion`, `default_price_autres` sur `AppSettings` (migration 0034) ; section « Prix unitaires par défaut » dans les paramètres ; pré-remplissage automatique au `addLine()` et au changement de `line_type` dans `ClientInvoiceForm` ; correction race-condition (`onMounted` async avant `addLine`).

### BIZ-122 — Intégrer description dans l’e-mail de facture

- **Terminé** : 2026-04-26
- **Livré** : paramètre description ajouté à mail_service.send_invoice_email ; si renseigné, l’objet du message devient Facture {numéro} — {description} ; routeur send-email passe invoice.description au service.

### BIZ-124 — Templates de numérotation configurables pour les factures

- **Terminé** : 2026-04-26
- **Livré** : `client_invoice_number_template` (`{year}`, `{seq}`) + `client_invoice_seq_digits` + `supplier_invoice_number_template` (strftime) sur `AppSettings` (migrations 0032, 0033) ; service `_next_number` avec regex ; endpoint `GET /api/invoices/next_number` (aperçu sans side-effect) ; affichage du numéro prévu dans le formulaire de création et dans la confirmation du wizard.

</details>

<details>
<summary>Lot T — Chatbot IA + refactor Paramètres (2026-04-28)</summary>

### BIZ-125 — Chatbot IA + page Aide

- **Terminé** : 2026-04-27
- **Livré** : sidebar chatbot flottante (SSE, Gemini/OpenAI), bouton FAB dans AppLayout, annulation, rendu Markdown via `marked` ; page `/aide` affichant `doc/user/manuel.md` en HTML ; panneau admin `SettingsChatPanel` (provider, clé API, modèle) ; backend : endpoints `/api/chat`, `/api/chat/config`, `/api/chat/logs`, `/api/help/manual` ; migrations 0035 (colonnes chat dans `app_settings`) et 0036 (table `chat_log`).

### BIZ-126 — Refactor UX écran Paramètres

- **Terminé** : 2026-04-27
- **Livré** : `SettingsAssociationSmtpPanel.vue` (413 lignes) scindé en `SettingsAssociationPanel.vue` (infos association + facturation) et `SettingsSmtpPanel.vue` (SMTP) ; chaque panneau sauvegarde indépendamment. Réalisé sur la même branche que BIZ-125.

</details>

<details>
<summary>BIZ-127 — Dialogue confirmation avant envoi e-mail facture (2026-05-02)</summary>

### BIZ-127 — Dialogue de confirmation avant envoi e-mail facture

- **Terminé** : 2026-05-02
- **Livré** : dialog de confirmation avec destinataire (lecture seule), sujet et corps éditables + aperçu PDF ; endpoint `GET /api/invoices/{id}/email-preview` ; `POST /api/invoices/{id}/send-email` accepte payload `{subject, body}` édité par l'utilisateur ; helpers `compose_subject()`/`compose_body()` extraits, `send_invoice_email` accepte `override_subject`/`override_body` ; audit log inclut le sujet ; 8 nouveaux tests unitaires.

</details>

<details>
<summary>BIZ-128 — Modèles d'e-mail configurables (2026-05-02)</summary>

### BIZ-128 — Modèles d'e-mail configurables dans les paramètres

- **Terminé** : 2026-05-02
- **Livré** : colonnes `email_subject_template` et `email_body_template` sur `app_settings` (migration 0037) ; section dédiée dans les paramètres SMTP ; variables `{invoice_number}`, `{description}`, `{association_name}`, `{invoice_ref}` ; `_SafeFormatMap` pour variables inconnues ; 7 nouveaux tests unitaires.

</details>

<details>
<summary>BIZ-130 — Confirmation de dépôt bancaire + métriques espèces/chèques (2026-05-02)</summary>

### BIZ-130 — Confirmation de dépôt bancaire + métriques espèces/chèques

- **Terminé** : 2026-05-02
- **Livré** :
  - Migration Alembic 0038 — colonnes `confirmed` (Boolean, default false) et `confirmed_date` (Date nullable) sur la table `deposits`
  - `bank_service.confirm_deposit()` — marque un dépôt comme confirmé (date = aujourd'hui) ; `list_deposits` accepte filtre `confirmed`
  - Endpoint `POST /api/bank/deposits/{id}/confirm` (write access) + audit log `bank.deposit.confirm`
  - Vue Banque : panneau « Dépôts en attente de confirmation » (visible si ≥ 1 dépôt non confirmé) — résumé nb chèques / nb encaissements + montant + bouton confirmer ; colonne « Statut » dans le tableau des dépôts avec filtre
  - Vue Paiements : deux métriques séparées « Chèques à remettre » et « Espèces à déposer » remplacent le compteur unique « Non remis »
  - 4 nouveaux tests d'intégration (`test_confirm_deposit`, déjà confirmé → 422, non trouvé → 404, filtre confirmed)

</details>

<details>
<summary>Historique des estimations — lots techniques 1-8 (2026-04-22)</summary>

Total estimé initial : ~40h — total révisé : ~55h.
Principaux postes de dérapage : quality gates (~10 min/commit), tests d'intégration, migrations Alembic, refactoring TEC-050.

### Lot 1 — Quick wins P3 — ~45 min

| Ticket | Estimation | Détail |
| --- | --- | --- |
| CHR-064 | 5 min | Supprimer un fichier + vérifier qu'il n'est pas importé |
| CHR-062 | 5 min | Changer une string dans `package.json` |
| TEC-066 | 20 min | Remplacer le pattern `global` par `@lru_cache`, vérifier les tests |
| TEC-063 | 15 min | Remplacer 2 noms dans les fixtures + migration Alembic si nécessaire |

### Lot 2 — Tests au vert (TEC-048) — ~2h

11 échecs dans `excel_import_parsers` / `excel_import_parsing` + 1 erreur API de test. Suite déjà au vert (739/739) après corrections antérieures.

### Lot 3 — Sécurité sans impact structurel — ~4h

| Ticket | Est. initiale | Est. révisée | Temps réel | Détail |
| --- | --- | --- | --- | --- |
| TEC-047 | 30 min | 1h | ~1h15 | Middleware 5 en-têtes + test CSP PrimeVue |
| TEC-052 | 20 min | 30 min | ~40 min | Conditionner endpoint sur `settings.debug` |
| TEC-055 | 20 min | 30 min | ~25 min | Paramètre `cors_allowed_origins` |
| TEC-060 | 30 min | 45 min | ~30 min | Retirer `create_all` de `init_db()` |
| TEC-051 | 50 min | 1h15 | ~50 min | `MAX(entry_number)` + lock + migration |

### Lot 4 — Qualité backend sans impact API — ~6h

| Ticket | Est. initiale | Est. révisée | Temps réel | Détail |
| --- | --- | --- | --- | --- |
| TEC-065 | 1h | 1h30 | ~1h30 | Déplacer attributs transients vers `PaymentRead` |
| TEC-057 | 2h | 2h30 | ~3h30 | `TypeDecorator` Decimal + 63 occurrences |
| TEC-059 | 1h30 | 2h | ~45 min | `limit=100` / `max=1000` sur tous les endpoints |

### Lot 5 — Sécurité auth (full-stack) — ~10h

| Ticket | Est. initiale | Est. révisée | Temps réel | Détail |
| --- | --- | --- | --- | --- |
| TEC-045 | 1h | 1h30 | ~1h | `slowapi` rate limiting sur `/auth/login` |
| BIZ-053 | 2h | 3h | ~1h30 | Migration `must_change_password` + guard |
| TEC-046 | 4h | 5h30 | — | Cookie `HttpOnly` + intercepteur Axios + `/auth/refresh` |

### Lot 6 — DevOps Docker — ~1h30

| Ticket | Est. initiale | Est. révisée | Détail |
| --- | --- | --- | --- |
| CHR-054 | 40 min | 50 min | `entrypoint.sh` avec gestion d'erreur |
| CHR-061 | 20 min | 20 min | `HEALTHCHECK` Docker + docker-compose |

### Lot 7 — Refactoring structurel — ~12h

| Ticket | Est. initiale | Est. révisée | Détail |
| --- | --- | --- | --- |
| TEC-050 | 6h | 9h | Éclater `excel_import.py` (5 038 L) en package |
| TEC-058 | 2h | 1h | Typer les `except Exception` |

### Lot 8 — Chantiers longs

| Ticket | Est. initiale | Est. révisée | Détail |
| --- | --- | --- | --- |
| BIZ-056 | 3-4h | 2h | Table d'audit + middleware + 4 types d'événements |
| TEC-049 | 10-15h | 12-20h | Palier 34 % → 60 % couverture de test |

</details>

<details>
<summary>Détails des sujets fermés — cliquer pour développer</summary>

### CHR-001 — Stabiliser la méthode de triage du backlog

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : backlog utilisé comme support versionné avec statuts, priorités et mises à jour récurrentes.

### CHR-002 — Documentation utilisateur import/reset

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : documentation rédigée dans `doc/user/import-excel-et-reinitialisation.md`.

### BIZ-003 — Campagne de retest métier sur imports réels

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : rejeu réel confirmé sans écart bloquant, procédure ajustée pour exercices/compteurs.

### BIZ-004 — Historique d'import réversible

- **Dates** : `created=2026-04-12`, `started=2026-04-20`, `completed=2026-04-20`
- **Livré** : backend `runs`, `operations`, `effects` réversibles, API cycle `prepare → execute → undo/redo`, UI prévisualisation + historique. Stabilisation rapprochement paiement/facture intra-run.

### BIZ-005 — Politique de coexistence import / écritures existantes

- **Dates** : `created=2026-04-12`, `started=2026-04-19`, `completed=2026-04-19`
- **Livré** : politique explicitée dans `doc/dev/BIZ-005-politique-coexistence-imports.md`, trois diagnostics : `entry-existing`, `entry-covered-by-solde`, `entry-near-manual`.

### CHR-006 — Warnings de dépréciation FastAPI

- **Dates** : `created=2026-04-12`, `started=2026-04-21`, `completed=2026-04-21`
- **Livré** : `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT`, zéro warning.

### CHR-007 — Source de vérité backlog vs issues GitHub

- **Dates** : `created=2026-04-12`, `completed=2026-04-13`
- **Livré** : convention actée — `doc/backlog.md` = source de vérité.

### BIZ-008 — Import Excel comme validation itérative de convergence

- **Dates** : `created=2026-04-12`, `started=2026-04-18`, `completed=2026-04-18`
- **Livré** : modes `convergence globale` et `validation moteur Gestion`, preview bidirectionnelle, script `scripts/run_excel_convergence_preview.py`. Documentation dans `doc/dev/BIZ-008-recette-convergence.md`.
- **Détail** : grille de contrôle par domaine (factures, paiements, banque, caisse, comptes pivots), politique d'écarts résiduels, périmètre asymétrique `Solde ↔ Excel` par exercice.

### BIZ-009 — Enrichir le plan comptable par défaut

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : seed enrichi avec comptes réels, sous-comptes historiques conservés inactifs.

### BIZ-010 — Stratégie de clôture des exercices historiques

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : exercices historiques ouverts pendant reprise, clôture administrative sans écritures de clôture.

### BIZ-011 — Exercice courant global

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : store global d'exercice + sélecteur partagé + filtrage métier par défaut.

### BIZ-012 — Liste des paiements : référence et édition

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : colonne Référence + bouton d'édition par ligne + dialogue `PUT /payments/{id}`.

### BIZ-013 — Journal de caisse : référence, détail et édition

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : référence visible, panneau de détail, édition directe, recalcul soldes après modification.

### BIZ-014 — Journal comptable : lisibilité et navigation

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Livré** : libellés comptes, références métier, tiers, détail, édition manuelles, navigation factures.

### BIZ-015 — Reset sélectif orienté reprise d'import

- **Dates** : `created=2026-04-13`, `started=2026-04-20`, `completed=2026-04-20`
- **Livré** : reset sélectif par type d'import + exercice avec prévisualisation, UI dans Paramètres, suppression des dépendances métier dérivées.

### BIZ-016 — Harmonisation i18n et microcopie UI

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Livré** : clés i18n cohérentes sur Banque, Caisse, Salaires (compteurs, états vides, libellés).

### BIZ-017 — Formats de dates et périodes en français

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Livré** : helper partagé pour mois en français, appliqué sur Salaires et Dashboard mensuel.

### BIZ-018 — Lisibilité des écrans de liste

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Livré** : socle DataTable partagé (filtres texte/dates/intervalles/multi-sélection, compteurs, tri, saisie date FR/ISO).

### BIZ-022 — Gestion des utilisateurs, rôles et sécurité

- **Dates** : `created=2026-04-13`, `started=2026-04-13`, `completed=2026-04-19`
- **Livré** : cycle de vie complet : rôles métier, administration comptes, profil, changement MDP, réinitialisation admin, invalidation jetons.

### BIZ-023 — Matrice d'autorisations par rôle

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Livré** : séparation Gestion/Comptabilité dans la navigation, guards frontend par domaine, renommage Gestionnaire/Comptable, permissions backend alignées.

### BIZ-036 — Carte « restant en retard » cliquable

- **Dates** : `created=2026-04-21`, `completed=2026-04-23`
- **Livré** : absorbé par BIZ-075 (KPI dashboard cliquables).

### BIZ-041 — Carte « non remis » cliquable

- **Dates** : `created=2026-04-21`, `completed=2026-04-23`
- **Livré** : absorbé par BIZ-075 (KPI dashboard cliquables).

### BIZ-042 — Bouton reset filtres tables

- **Dates** : `created=2026-04-21`, `completed=2026-04-23`
- **Livré** : bouton reset sur tous les filtres de toutes les tables.

### BIZ-043 — Combos comptes comptables couleur

- **Dates** : `created=2026-04-21`, `completed=2026-04-23`
- **Livré** : combos affichant numéro, nom et couleur des comptes suivis.

### TEC-045 — Rate limiting `/auth/login`

- **Dates** : `created=2026-04-22`, `completed=2026-04-23`
- **Livré** : middleware `slowapi` 5 req/min par IP, bypass configurable pour tests.

### TEC-046 — Refresh token cookie HttpOnly

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : cookie `HttpOnly`/`Secure`/`SameSite=Strict`, endpoint `POST /auth/logout`, intercepteur Axios `withCredentials: true`, 6 tests dédiés.

### TEC-047 — En-têtes de sécurité HTTP

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : middleware CSP, HSTS, X-Content-Type-Options, X-Frame-Options. `dark-mode-init.js` extrait pour CSP `script-src 'self'`.

### TEC-048 — Corriger les tests en échec

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : suite 739/739 au vert. Test API adapté pour `@lru_cache` (TEC-066).

### TEC-049 — Remonter la couverture de test

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : +44 tests (812 → 856), couverture 29% → 71%. Services critiques ≥ 90% : accounting_engine 92%, invoice 93%, payment 90%, fiscal_year ~95%, salary ~95%.

### TEC-050 — Refactorer `excel_import.py` en package

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : monolith 5 567 lignes éclaté en 16 sous-modules + `__init__.py` re-export. Aucune dépendance circulaire.

### TEC-051 — Numérotation des écritures thread-safe

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `COUNT(*)` → `MAX(entry_number)` + lock, migration, tests de concurrence.

### TEC-052 — Désactiver `reset-db` en production

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : endpoint conditionné à `settings.debug`.

### BIZ-053 — Changement MDP obligatoire au premier login

- **Dates** : `created=2026-04-22`, `completed=2026-04-23`
- **Livré** : champ `must_change_password` (migration 0022), middleware 403, redirection frontend, 11 tests intégration + 2 tests frontend.

### CHR-054 — Séparer migrations du démarrage Uvicorn

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `entrypoint.sh` avec `set -e`, Dockerfile mis à jour avec `ENTRYPOINT`.

### TEC-055 — CORS configurable pour la production

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : paramètre `cors_allowed_origins` dans les settings.

### BIZ-056 — Journal d'audit structuré

- **Dates** : `created=2026-04-22`, `completed=2026-04-23`
- **Livré** : modèle `AuditLog` + service `record_audit` + migration 0023. Événements : auth (login/logout/password), admin (user CRUD, reset_db, selective_reset). 14 tests.

### TEC-057 — TypeDecorator Decimal pour l'ORM

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `DecimalType(TypeDecorator)` sur toutes les colonnes monétaires, ~63 casts `Decimal(str())` retirés.

### TEC-058 — Typer les exceptions de l'import Excel

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `ImportFileOpenError`, `ImportSheetError` dans `_exceptions.py`, mapping typé dans routeur. 10 tests ajoutés.

### TEC-059 — Pagination bornée par défaut

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `limit=100` / `max=1000` sur tous les endpoints de liste. Frontend et tests adaptés.

### TEC-060 — Retirer `create_all` de `init_db()`

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `create_all` conservé uniquement dans `conftest.py`, Alembic seul en prod.

### CHR-061 — Docker HEALTHCHECK

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `GET /api/health` (200), `HEALTHCHECK` dans Dockerfile, `healthcheck:` dans docker-compose.

### CHR-062 — Synchroniser les versions frontend / backend

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `frontend/package.json` aligné sur `0.1.0`.

### TEC-063 — Retirer les noms personnels du plan comptable (RGPD)

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : noms remplacés par `Client litigieux 1/2`. Seed ne touche pas les données existantes.

### CHR-064 — Supprimer `stores/counter.ts`

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : fichier supprimé, aucune référence dans le code.

### TEC-065 — Éliminer `__allow_unmapped__` de Payment

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : attributs transients déplacés vers `PaymentRead` via `_to_payment_read()`.

### TEC-066 — Settings singleton `@lru_cache`

- **Dates** : `created=2026-04-22`, `completed=2026-04-22`
- **Livré** : `@lru_cache(maxsize=1)` sur `get_settings()`, variable globale supprimée.

### TEC-067 — Gestionnaire d'erreurs global FastAPI

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : middleware `UnhandledExceptionMiddleware` → JSON 500 `{"detail": ..., "code": "INTERNAL_SERVER_ERROR"}`, log serveur. 5 tests.

### TEC-068 — Désactiver Swagger/ReDoc en production

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `docs_url`, `redoc_url`, `openapi_url` conditionnés à `cfg.debug`.

### BIZ-069 — Endpoint de sauvegarde SQLite

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `POST /api/settings/backup` avec `sqlite3.backup()` + rotation 5 fichiers.

### BIZ-070 — Page 404 dédiée

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `NotFoundView.vue` avec icône, titre i18n, bouton retour. Catch-all router remplacé.

### BIZ-071 — Skeleton loaders

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `<Skeleton>` PrimeVue sur les écrans de liste principaux.

### BIZ-072 — Fil d'Ariane (Breadcrumb)

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : composable `useBreadcrumb` + `<Breadcrumb>` PrimeVue via meta routes `label`/`breadcrumbParent`.

### BIZ-073 — Raccourcis clavier

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : composable `useKeyboardShortcuts` (Ctrl+N, Ctrl+S, Escape).

### BIZ-074 — Bandeau connexion perdue

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : composable `useNetworkStatus` + `AppOfflineBanner.vue` (events online/offline + intercepteur Axios).

### BIZ-075 — Dashboard KPI cliquables

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : KPI cliquables vers listes filtrées. Complète BIZ-036 et BIZ-041.

### BIZ-076 — Styles d'impression comptable

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : `@media print` sur journal, balance, grand livre, bilan, résultat. Sidebar/filtres/boutons masqués, en-tête imprimable.

### TEC-079 — Tests composables frontend

- **Dates** : `created=2026-04-23`, `completed=2026-04-24`
- **Livré** : 15 tests Vitest — `useDarkMode` (4), `useTableFilter` (8), `activeFilterLabels` (10). Suite 126/126 au vert.

### TEC-080 — Smoke test E2E Playwright

- **Dates** : `created=2026-04-23`, `completed=2026-04-24`
- **Livré** : `playwright.config.ts` (webServer auto-start, DB E2E dédiée). Smoke test : login → MDP obligatoire → dashboard → contacts → factures → paiements.

### TEC-081 — Tests d'intégration API manquants

- **Dates** : `created=2026-04-23`, `completed=2026-04-24`
- **Livré** : `test_accounting_rules_api.py` (11), `test_fiscal_year_api.py` (10), `test_salary_api.py` (+7), `test_dashboard_api.py` (+1). 52 tests intégration au vert.

### CHR-083 — Guide de migration Synology

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : guide FR+EN dans `doc/user/` couvrant mise à jour Docker, vérification post-migration, rollback.

### BIZ-084 — Notification expiration session

- **Dates** : `created=2026-04-23`, `completed=2026-05-03`
- **Livré** : composable `useSessionExpiry` (décode expiry JWT, avertissement T−5 min) + `AppSessionWarning.vue` avec bouton « Prolonger la session ».

### TEC-085 — Politique de complexité MDP

- **Dates** : `created=2026-04-23`, `completed=2026-04-23`
- **Livré** : validateur `_validate_password_complexity` (8 chars, majuscule, chiffre). 14 tests unitaires.

</details>

---

## Légende

| Préfixe | Signification |
| --- | --- |
| BIZ-NNN | Fonctionnalité métier — valeur utilisateur directe |
| TEC-NNN | Technique — qualité, refactoring, tests, sécurité technique |
| CHR-NNN | Maintenance — outillage, documentation, CI, DevOps |

| Priorité | Signification |
| --- | --- |
| P1 | Important — fort impact métier, risque ou besoin opérationnel |
| P2 | Utile — amélioration à programmer |
| P3 | Confort, finition ou dette technique optionnelle |

| Statut | Signification |
| --- | --- |
| Bac d'entrée | Besoin capturé, pas encore arbitré |
| ⬜ Prêt | Besoin clarifié, prêt à être pris |
| 🔄 En cours | Implémentation en cours sur une branche active |
| ✅ Fait | Sujet livré — détail dans `CHANGELOG.md` |
