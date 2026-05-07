<!-- markdownlint-disable MD033 -->
# Backlog — Solde ⚖️

Backlog produit pour Solde ⚖️ — gestion comptable associative.
Quand le travail démarre sur un sujet, créer une branche `feature/` depuis `develop`.
Quand un sujet est livré, mettre à jour `CHANGELOG.md` et passer le ticket en ✅ Fait ici.

> Lots terminés depuis plus de 3 jours → [backlog-archive.md](backlog-archive.md)

---

## Calibration estimations

Facteur de marge actuel : **1,00** (0%) — inchangé (voir note CR2).

| Lot | Estimé Copilot | Réel Copilot | Ratio | Estimé gestion | Réel gestion | Ajustement |
| --- | --- | --- | --- | --- | --- | --- |
| UI | ~65 min | ~30 min | **0,46** | 15 min | ? | ↓ facteur → 1,00 |
| CR2 | ~70 min | ~20 min | **0,29** | — | — | voir note |
| REV | ~190 min | ~70 min | **0,37** | 15 min | — | voir note REV |

> Lot UI : estimations 2x trop élevées. Les tickets UI/bulk-replace et les vérifications de tickets "déjà fait" ont été surestimés.
> Lot CR2 : ratio 0,29 — très inférieur à 1,15. Cependant ces tickets étaient tous très petits (i18n, tests, nav, squelette) et le facteur 1,00 reflète déjà une marge nulle. Plutôt que d'abaisser le facteur en dessous de 1,00 (ce qui serait contre-productif), la leçon est : **pour les tickets de finition/tests simples, l'estimation de référence doit être 3–5 min, pas 10–20 min**. Facteur maintenu à 1,00 ; calibration des estimations unitaires à revoir pour ces catégories.
> Lot REV : ratio 0,37. Cause principale : 3 tickets sur 11 étaient en réalité déjà traités (TEC-161, TEC-163, TEC-166 = 80 min estimés → 7 min réels). Les tickets d'implémentation pure (TEC-160, TEC-162, TEC-167, TEC-169, TEC-172) ont un ratio ~0,55. **Leçon** : avant d'estimer un ticket de « review fix », vérifier si le problème existe réellement. Pour les tickets d'implémentation technique, appliquer un facteur **0,60** par rapport à l'estimation initiale naïve.

---

## Lots actifs

### Lot BK — Backup automatique (v1.7) — ~4h Copilot + 15 min gestion

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| BIZ-173 | Migration Alembic + modèle BackupDestination | P1 | ~15 min | 2026-05-05 | | |
| BIZ-174 | Schemas Pydantic backup | P1 | ~10 min | 2026-05-05 | | |
| BIZ-175 | Service rclone (backup_destination_service) | P1 | ~25 min | 2026-05-05 | | |
| BIZ-176 | Dockerfile — installation rclone | P1 | ~5 min | 2026-05-05 | | |
| BIZ-177 | Scheduler APScheduler + lifespan main.py | P1 | ~30 min | 2026-05-05 | | |
| BIZ-178 | Service restore (test-restore + restore distante) | P1 | ~15 min | 2026-05-05 | | |
| BIZ-179 | Router backup.py (12 endpoints) | P1 | ~35 min | 2026-05-05 | | |
| BIZ-180 | Frontend api/backup.ts | P1 | ~10 min | 2026-05-05 | | |
| BIZ-181 | Frontend SettingsBackupPanel.vue | P1 | ~45 min | 2026-05-05 | | |
| BIZ-182 | Frontend SettingsView + i18n fr/en | P1 | ~15 min | 2026-05-05 | | |
| BIZ-183 | Tests unitaires backend (rclone mock, scheduler) | P1 | ~15 min | 2026-05-05 | | |
| BIZ-184 | Tests intégration API backup | P1 | ~20 min | 2026-05-05 | | |

---

### Lot REV2 — Refactoring technique différé (v1.7) — ~55 min Copilot + 15 min gestion

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| TEC-170 | Standardiser les codes d'erreur API (EN + code structuré) | P2 | ~20 min | 2026-05-06 | 2026-05-07 | 2026-05-07 |
| TEC-171 | Audit : supprimer les commit() dans les services | P2 | ~20 min | 2026-05-06 | 2026-05-07 | 2026-05-07 |
| TEC-173 | Découper bank.py en sous-routeurs | P3 | ~15 min | 2026-05-06 | 2026-05-07 | 2026-05-07 |

---

### Hors lots

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| BIZ-169 | Édition/suppression des opérations manuelles | P2 | ~25 min | 2026-05-04 | 2026-05-04 | |
| BIZ-171 | Améliorations tuiles et détail factures — mobile | P2 | ~35 min | 2026-05-05 | 2026-05-05 | 2026-05-05 |
| BIZ-172 | Section admin : paiements chèques incohérents | P2 | ~45 min | 2026-05-05 | 2026-05-05 | 2026-05-05 |

---

## Détails

### TEC-170 — Standardiser les codes d'erreur API

Certaines erreurs sont en français (`"Une transaction avec cette référence existe déjà."`), d'autres en anglais (`"Invoice not found"`). Standardiser : champ `code` structuré (EN, machine-readable) + `detail` humain ; le frontend affiche via i18n selon le `code`.

### TEC-171 — Audit : supprimer les commit() dans les services

Certains services (`accounting_account`, `accounting_rule_service`, etc.) font `await db.commit()` directement. Le pattern correct : les services font `flush()`, la session commit/rollback est gérée par `get_db()`. Auditer et corriger pour éviter les commits partiels.

### TEC-173 — Découper bank.py en sous-routeurs

`backend/routers/bank.py` (~550 lignes, 15+ endpoints) est le plus gros routeur. Découper en `bank_transactions.py`, `bank_deposits.py`, `bank_import.py` pour la maintenabilité.

### BIZ-173 — Migration Alembic + modèle BackupDestination

Migration Alembic ajoutant 7 colonnes dans `app_settings` : `backup_enabled` (bool), `backup_schedule_type` (str, "interval"|"cron"), `backup_interval_hours` (int), `backup_cron_expression` (str|None), `backup_include_uploads` (bool), `backup_notify_on_failure` (bool), `backup_last_run_at` (datetime|None), `backup_last_run_status` (str|None). Nouvelle table `backup_destination` : `id`, `name`, `type` (local|smb|onedrive), `enabled` (bool), `rclone_remote_name` (str), `rclone_config` (JSON text), `target_path` (str), `created_at`. Création de `backend/models/backup_destination.py` avec le modèle SQLAlchemy.

### BIZ-174 — Schemas Pydantic backup

Création de `backend/schemas/backup.py` avec : `BackupDestinationRead`, `BackupDestinationCreate`, `BackupDestinationUpdate` (champs name, type, enabled, rclone_remote_name, rclone_config, target_path), `BackupScheduleRead`, `BackupScheduleUpdate` (enabled, schedule_type, interval_hours, cron_expression, include_uploads, notify_on_failure), `BackupRunStatus` (last_run_at, status, destinations_results), `BackupConnectionTestResult` (success, message), `BackupRestoreTestResult` (ok, integrity_check, tables_found, tables_missing, error).

### BIZ-175 — Service rclone (backup_destination_service)

Création de `backend/services/backup_destination_service.py` avec :
- `write_rclone_config(destinations)` → génère `data/rclone.conf` à partir des destinations en base (section `[nom]` par destination selon le type : `type = local`, `type = smb` avec host/user/pass/share, `type = onedrive` avec token depuis rclone_config).
- `sync_destination(dest, src_paths)` → subprocess `rclone sync {src} {remote}:{path} --update --config data/rclone.conf` pour chaque chemin source.
- `test_destination_connection(dest)` → subprocess `rclone lsd {remote}: --config ...`, retourne `BackupConnectionTestResult`.
- `fetch_remote_backup(dest, filename)` → `rclone copy {remote}:backups/{file} data/backups/ --config ...` pour rapatrier un backup distant avant restore.

### BIZ-176 — Dockerfile — installation rclone

Ajout de `rclone` dans le Dockerfile stage runtime : `RUN apt-get update && apt-get install -y --no-install-recommends rclone && rm -rf /var/lib/apt/lists/*`. Vérification : `docker exec solde rclone version`.

### BIZ-177 — Scheduler APScheduler + lifespan main.py

Ajout de `apscheduler>=3.10` dans `pyproject.toml`. Création de `backend/services/backup_scheduler.py` avec :
- `BackupScheduler` (wrapper `AsyncIOScheduler`) : `start()`, `stop()`, `reload(settings)` — replanifie le job selon `backup_schedule_type` (interval ou cron), annule l'ancien job si les settings changent.
- `run_backup_job(db_path, backup_dir, settings)` : appelle `create_backup()`, appelle `sync_destination()` pour chaque destination activée, met à jour `backup_last_run_at` et `backup_last_run_status` en base, envoie un email via le service SMTP existant si échec et `backup_notify_on_failure=True`.
- Intégration dans `backend/main.py` lifespan : démarrer le scheduler au startup si `backup_enabled`, arrêter au shutdown. Exposer `reload_scheduler()` appelé depuis le router settings quand les paramètres de planification sont mis à jour.

### BIZ-178 — Service restore (test-restore + restore distante)

Création de `backend/services/backup_restore_service.py` avec :
- `test_restore(backup_path)` : ouvre le fichier `.db` via `sqlite3`, exécute `PRAGMA integrity_check`, vérifie la présence des tables attendues (liste hardcodée des tables du modèle), retourne `BackupRestoreTestResult` sans toucher à la DB live.
- `restore_from_destination(dest, filename, backup_dir, db_path)` : appelle `fetch_remote_backup()` pour rapatrier le fichier si la destination est distante, puis appelle `restore_backup()` existant dans `backup_service.py`.

### BIZ-179 — Router backup.py (12 endpoints)

Création de `backend/routers/backup.py` (admin uniquement) avec :
- `GET /api/backup/destinations` — liste toutes les destinations.
- `POST /api/backup/destinations` — créer une destination (génère rclone.conf).
- `PUT /api/backup/destinations/{id}` — modifier.
- `DELETE /api/backup/destinations/{id}` — supprimer.
- `POST /api/backup/destinations/{id}/test` — teste la connexion rclone, retourne `BackupConnectionTestResult`.
- `GET /api/backup/schedule` — lit les settings de planification depuis `AppSettings`.
- `PUT /api/backup/schedule` — met à jour les settings + replanifie le scheduler.
- `POST /api/backup/run` — déclenche un backup immédiat (background task).
- `GET /api/backup/status` — retourne `BackupRunStatus` (dernier run, statut par destination).
- `POST /api/backup/backups/{filename}/test-restore` — dry-run `test_restore()` sur un fichier local.
- `POST /api/backup/backups/{filename}/restore` — restore réelle (locale ou distante) ; accepte `?destination_id=` optionnel pour les fichiers distants.
- `GET /api/backup/oauth/onedrive/start` — spawn `rclone authorize onedrive`, capture le port local, retourne `{ port, auth_url }` avec l'URL construite en remplaçant `127.0.0.1` par `{request.client.host}` (NAS IP).
- `GET /api/backup/oauth/onedrive/status` — poll : retourne `{ done, token }` une fois que rclone a capturé le token, ou `{ done: false }` tant que l'autorisation est en cours (timeout 5 min).

### BIZ-180 — Frontend api/backup.ts

Création de `frontend/src/api/backup.ts` avec les interfaces TypeScript (`BackupDestination`, `BackupDestinationCreate`, `BackupSchedule`, `BackupRunStatus`, `BackupConnectionTestResult`, `BackupRestoreTestResult`) et les fonctions client pour tous les endpoints de `backup.py`.

### BIZ-181 — Frontend SettingsBackupPanel.vue

Création de `frontend/src/components/settings/SettingsBackupPanel.vue` avec :
- **Section planification** : toggle activé/désactivé, sélecteur interval (heures) ou cron (input expression + preview "prochain run dans X"), checkbox inclure uploads, checkbox notifier en cas d'échec.
- **Section destinations** : `DataTable` avec colonnes nom / type / statut / activé ; actions Tester (badge ✓/✗), Activer/Désactiver, Supprimer.
- **Dialog ajouter destination** : champ type (local / SMB / OneDrive) → formulaire adapté : local = chemin cible ; SMB = host, share, user, password, chemin cible ; OneDrive = bouton « Autoriser OneDrive » (ouvre le dialog OAuth).
- **Dialog OneDrive OAuth** : bouton → `GET /api/backup/oauth/onedrive/start` → ouvre `auth_url` dans un nouvel onglet → poll `GET /api/backup/oauth/onedrive/status` toutes les 2s → affiche spinner « En attente d'autorisation » → quand `done=true`, le token est stocké côté backend dans `rclone_config`, dialog se ferme.
- **Section statut** : date du dernier run, icône succès/erreur, résultat par destination.
- **Bouton « Lancer maintenant »** : déclenche `POST /api/backup/run`, toast confirmation.
- **Section restauration** : liste les backups locaux (`GET /api/settings/backups`) + backups distants (par destination) ; chaque entrée a deux boutons : « Tester » (dry-run, modale avec rapport intégrité) et « Restaurer » (confirmation puis restore réelle).

### BIZ-182 — Frontend SettingsView + i18n fr/en

Ajout de `<SettingsBackupPanel />` dans `SettingsView.vue` après `<SettingsSmtpPanel />`. Ajout de toutes les clés `settings.backup.*` dans `frontend/src/i18n/fr.ts` et `en.ts` (planification, destinations, types, OAuth, statuts, restore).

### BIZ-183 — Tests unitaires backend

Tests pour `backup_destination_service` (mock subprocess rclone : génération `rclone.conf` par type, parsing résultat sync, test connexion OK/KO) et `backup_restore_service` (test-restore sur fichier DB valide et fichier corrompu). Fichier : `tests/unit/test_backup_services.py`.

### BIZ-184 — Tests intégration API backup

Tests pour les endpoints du router `backup.py` : CRUD destinations (create/list/update/delete), test connexion (mock rclone), trigger backup (mock job), GET status, test-restore (mock service), PUT schedule (vérifie settings en base). Fichier : `tests/integration/test_backup_api.py`.

### BIZ-172 — Section admin : paiements chèques incohérents

Panneau dans la vue Supervision système (admin uniquement) listant les paiements par chèque dont `deposited=True` mais `deposit_date=NULL` (état incohérent produit par l'import Excel). Chaque ligne propose une action « Corriger » avec un sélecteur de date pour poser la `deposit_date` manquante. Ces paiements sont actuellement comptabilisés à tort dans "Chèques non remis" sur le dashboard.

### BIZ-166 — Vue contacts : onglet clients par défaut + tri par récence

Onglet "Clients" activé par défaut (ordre : Clients > Fournisseurs > Tout).
Tri synthétique : facture < 6 mois en tête, puis ordre alphabétique (nom, prénom).

### BIZ-034 — Support multi-compte banque

Distinguer compte courant et compte épargne dans les données, imports et écrans.
Décisions métier nécessaires avant implémentation.

### BIZ-169 — Édition/suppression des opérations manuelles

Permettre de modifier ou supprimer les opérations bancaires créées manuellement depuis BankView (opérations sans import source).

### BIZ-171 — Améliorations tuiles et détail factures — mobile

Améliorations de l'expérience mobile sur les vues factures client et fournisseur :
- Tuile facture client : supprimer l'étiquette (label catégorie) qui n'apporte rien en vue liste et augmente la hauteur de la tuile inutilement.
- Tuile facture fournisseur : fusionner la ligne « Référence fournisseur » et l'icône trombone en une seule ligne ; supprimer la div dédiée au seul trombone.
- Détail facture fournisseur (dialog prévisualisation) : présenter date / échéance / référence sur lignes séparées au lieu d'une phrase en ligne ; rendre les boutons icon-only sur mobile ; empiler la section header en colonne sur mobile ; réduire la taille des labels de la grille TOTAL / RÉGLÉ / RESTANT DÛ pour éviter le débordement sur 2 lignes.



---

## Lots terminés récents (≤ 3 jours)

| Lot | Nom | Version | Tickets | Terminé | Est. Copilot | Réel Copilot |
| --- | --- | --- | --- | --- | --- | --- |
| REV | Revue de code technique | v1.6.1 | TEC-160–165, 167–169, 172 (+ TEC-161, 163, 166 déjà faits) | 2026-05-06 | ~190 min | ~70 min |
| BIZ-172 | Paiements chèques incohérents | v1.6 | BIZ-172 | 2026-05-05 | ~45 min | — |
| BIZ-171 | Améliorations factures mobile | v1.6 | BIZ-171 | 2026-05-05 | ~35 min | — |
| BIZ-170 | Gestion bordereaux en attente | v1.6 | BIZ-170 | 2026-05-05 | ~60 min | ~45 min |
| BIZ-034 | Support multi-compte banque + bugfixes comptables | v1.5 | BIZ-034, fix virement, fix journal filtré, fix fiscal_year_id manuel | 2026-05-04 | — | — |
| CR2 | Correctifs & finitions post-MOB | v1.5 | TEC-157, TEC-158, TEC-159, BIZ-165, BIZ-166, BIZ-167, BIZ-168, CHR-078 | 2026-05-04 | ~95 min | ~30 min |
| Wizard | Wizard factures & Contacts | v1.2 | BIZ-144, BIZ-145, BIZ-147, BIZ-151 | 2026-05-02 | — | — |
| CR | Correctifs revue de code | v1.3.1 | TEC-133, TEC-134, TEC-135, TEC-136, TEC-137, TEC-138, TEC-139, TEC-140, TEC-141, TEC-155 | 2026-05-02 | — | — |
| DOC | Documentation utilisateur | v1.5 | BIZ-161, BIZ-162, BIZ-163 | 2026-05-03 | ~115 min | ~45 min |
| UI | Améliorations UI & saisie | v1.4 | BIZ-149, BIZ-150, BIZ-157, BIZ-158 | 2026-05-03 | ~65 min | ~30 min |
| MOB | Mode téléphone | v1.5 | BIZ-164 | 2026-05-03 | ~90 min | — |

<details>
<summary>Lot REV — Revue de code technique (2026-05-06)</summary>

| Ticket | Titre | Est. | Réel | Note |
| --- | --- | --- | --- | --- |
| TEC-160 | Fix race condition entry_number | ~15 min | ~10 min | Migration + unique index + retry |
| TEC-161 | Masquer clés API/SMTP | ~15 min | ~2 min | Déjà traité (schema excluait déjà les champs) |
| TEC-162 | Frontend .catch vides | ~30 min | ~8 min | 11 occurrences → console.error |
| TEC-163 | Optimiser fonds mensuels | ~20 min | ~2 min | Déjà efficace (2 queries, pas N) |
| TEC-164 | Rendre next_entry_number public | ~5 min | ~2 min | Fusionné avec TEC-160 |
| TEC-165 | max_length mot de passe | ~5 min | ~2 min | +2 lignes |
| TEC-166 | Tests accounting_engine | ~45 min | ~3 min | Tests déjà existants (8 classes) |
| TEC-167 | Allocation batch numéros | ~15 min | ~8 min | next_entry_numbers + refacto apply |
| TEC-168 | Cache Jinja2 Environment | ~5 min | ~2 min | @lru_cache |
| TEC-169 | max_length schemas bank | ~20 min | ~8 min | Field(max_length=…) |
| TEC-172 | CSRF X-Requested-With | ~15 min | ~8 min | Header check + frontend + tests |
| — | Quality gate + fixes | — | ~15 min | ruff, mypy, pytest, eslint, vue-tsc, vitest |
| **Total** | | **~190 min** | **~70 min** | Ratio 0,37 |

</details>

| Ticket | Titre | Est. | Réel |
| --- | --- | --- | --- |
| TEC-157 | i18n AppMobileCardList + CashView | ~10 min | ~3 min |
| TEC-158 | Tests intégration suggest_cheque_number (5 tests) | ~20 min | ~5 min |
| TEC-159 | Tests cheque_number_template settings API (4 tests) | ~15 min | ~4 min |
| BIZ-165 | Navigation prev/next preview factures client | ~10 min | ~5 min |
| CHR-078 | Squelette i18n anglais (en.ts) | ~15 min | ~3 min |
| CR-077 | Corrections revue Copilot PR #77 (8 threads) | ~25 min | ~20 min |
| **Total** | | **~95 min** | **~36 min** |

### Détail

- **TEC-157** : `AppMobileCardList.vue` — prop `emptyMessage` default migré vers `t('common.empty')` + import `useI18n`. `CashView.vue` — `'Écart :'` remplacé par `t('cash.count_diff')`. Clé `common.empty: 'Aucune donnée.'` ajoutée dans `fr.ts`.
- **TEC-158** : 5 tests dans `test_payments_api.py` : statut 200, string non vide, pas de date → aujourd'hui, incrément après un chèque existant, 401 sans auth, 403 readonly.
- **TEC-159** : 4 tests dans `test_settings_api.py` (dans `TestUpdateSettings`) : valeur par défaut `{date}.{seq}`, update valide, 422 sans `{seq}`, 422 avec placeholder inconnu.
- **BIZ-165** : `ClientInvoicesView.vue` — `historyIndex` ref, `openHistory` indexe dans `displayedInvoices`, barre nav ◀ N/total ▶ dans le dialog, `goToPrevHistory` / `goToNextHistory`, styles `.preview-nav-bar`.
- **CHR-078** : `frontend/src/i18n/en.ts` créé — sections `app`, `auth`, `common` traduits en anglais. Enregistré dans `index.ts` (messages: `{ fr, en }`).
- **CR-077** : Corrections des 8 threads de revue Copilot sur PR #77 — CSS dupliqué supprimé (`SupplierInvoicesView`), fuite Blob URL corrigée (`ClientInvoicesView`), bouton créance douteuse restreint à `type === 'client'` (`ContactHistoryContent`), commentaire `en.ts` corrigé, tests `suggest_cheque_number` renforcés (format exact + date today), 4 tests Vitest nav prev/next ajoutés (client + fournisseur). Version 1.4.7 → 1.4.8.

</details>

<details>
<summary>Lot MOB — Mode téléphone (2026-05-03)</summary>

| Ticket | Titre | Est. | Réel | Écart |
| --- | --- | --- | --- | --- |
| BIZ-164 (mobile) | Vues cartes + composant + breakpoint | ~50 min | — | — |
| BIZ-164 (depot) | Tuile dépôt espèces redesignée | ~15 min | — | — |
| BIZ-164 (stat) | Stat cards 2 colonnes mobile | ~5 min | — | — |
| BIZ-164 (cheque) | Suggestion auto n° chèque | ~20 min | — | — |
| **Total** | | **~90 min** | **—** | **—** |

### BIZ-164 — Mode téléphone & UX mobile
Migration Alembic `0049` : `cheque_number_template` dans `app_settings`. Endpoint `GET /api/payments/suggest_cheque_number`. Service `suggest_cheque_number` dans `settings.py`. Auto-suggestion dans `ClientInvoicesView`, `SupplierInvoicesView`, `QuickPaymentWizard`. Champ configurable dans `SettingsAssociationPanel`. Vues cartes mobile sur **toutes les listes** via `AppMobileCardList` (générique `T`) + `useBreakpoints` : Factures client/fournisseur (historiques), Contacts, Banque (transactions + dépôts), Règlements, Caisse, Salaires (3 tables), Employés, Comptabilité (Comptes, Balance, Bilan, Résultat, Règles, Journal, Grand-livre), Exercices, Utilisateurs. Dialogs full-width mobile. Stat grid 2 colonnes mobile.

</details>

<details>
<summary>Lot UI — Améliorations UI & saisie (2026-05-03)</summary>

| Ticket | Titre | Est. | Réel | Écart |
| --- | --- | --- | --- | --- |
| BIZ-158 | Limite API 1000 items + warning | ~30 min | ~18 min | −12 min |
| BIZ-149 | Auto-capitalisation intitulés facture | ~15 min | ~2 min | −13 min |
| BIZ-150 | Accepter la virgule comme séparateur décimal | ~10 min | ~7 min | −3 min |
| BIZ-157 | Pagination 50 items par défaut | ~10 min | ~3 min | −7 min |
| **Total** | | **~65 min** | **~30 min** | **−35 min** |

### BIZ-158 — Limite API 1000 items + warning si atteinte
`default=1000, le=1000` sur 6 routeurs (`invoice.py`, `payment.py`, `contact.py`, `bank.py` transactions + dépôts, `salary.py`). Bandeau `Message` PrimeVue severity `warn` dans chaque vue liste quand le résultat atteint 1 000 items. 4 tests mis à jour (renommage + assertions). Correction d'un bug de docstring introduit en cours de session.

### BIZ-149 — Auto-capitalisation des intitulés facture
Déjà implémenté (`@blur="capitalizeFirstLetter(line)"` dans `ClientInvoiceForm.vue`) — vérification rapide, ticket fermé.

### BIZ-150 — Accepter la virgule comme séparateur décimal
Champs `quantity` et `unit_price` dans `ClientInvoiceForm.vue` : `type="text" inputmode="decimal"` + fonction `normalizeDecimalInput()` (remplace `,` par `.` à la saisie, met à jour le modèle via `parseFloat`).

### BIZ-157 — Pagination 50 items par défaut
`:rows="50"` dans tous les composants Vue (anciennement 20). Remplacement global dans `frontend/src/`.

</details>

<details>
<summary>Lot CR — Correctifs revue de code (2026-05-02)</summary>

### TEC-133 — Access token en mémoire uniquement (XSS)
Token stocké dans un `ref` Pinia non persisté ; rechargement via `POST /api/auth/refresh` (cookie HttpOnly) ; `initFromStorage()` supprimé.

### TEC-134 — Atomicité audit log
`record_audit()` appelé avant `await db.commit()` dans `update_user`.

### TEC-135 — Race condition numérotation factures
Retry loop sur `IntegrityError` (3 tentatives) dans `invoice_service._next_number()`.

### TEC-136 — Chemins relatifs en base
`Invoice.file_path` / `Invoice.pdf_path` stockés en relatif ; résolution absolue uniquement à la lecture via `resolve_file_path()`.

### TEC-137 — Décodage JWT unique
Payload JWT mis en cache dans `request.state.jwt_payload` par le middleware ; `get_current_user` le réutilise.

### TEC-138 — Rate limiter : mémoire bornée
Purge des clés expirées toutes les 100 tentatives dans `rate_limiter.py`.

### TEC-139 — Tokens OpenAI en streaming
`stream_options={"include_usage": True}` + extraction de `chunk.usage` sur le dernier événement SSE.

### TEC-140 — Pagination audit log
`GET /api/settings/audit-logs` : `skip`, `limit`, `action`, `actor_id`, `from_date`, `to_date` ; vue Paramètres mise à jour.

### TEC-141 — Constante `USER_ROLES`
`frontend/src/constants/roles.ts` : source unique pour les chaînes de rôles.

### TEC-155 — Suppression `# type: ignore`
13 suppressions dans `backend/routers/invoice.py` éliminées ; annotations corrigées.

</details>

Tickets fermés hors lots récents : **BIZ-127**, **BIZ-128**, **BIZ-129**, **BIZ-130**, **BIZ-131**, **BIZ-132**, **TEC-156**.

> Lots et tickets plus anciens → [backlog-archive.md](backlog-archive.md)

<details>
<summary>TEC-156 — Fix token auth chat (2026-05-03)</summary>

### TEC-156 — Fix token auth chat (localStorage → Pinia)

`streamChat` dans `api/chat.ts` lisait `localStorage.getItem('access_token')` — toujours `null` car le token est stocké uniquement en mémoire Pinia (mitigation XSS). Chaque `POST /api/chat` retournait 401. Corrigé en lisant `useAuthStore().accessToken`. Découvert lors du test du Lot DOC (2026-05-03).

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
