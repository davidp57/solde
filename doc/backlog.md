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

> Lot UI : estimations 2x trop élevées. Les tickets UI/bulk-replace et les vérifications de tickets "déjà fait" ont été surestimés.
> Lot CR2 : ratio 0,29 — très inférieur à 1,15. Cependant ces tickets étaient tous très petits (i18n, tests, nav, squelette) et le facteur 1,00 reflète déjà une marge nulle. Plutôt que d'abaisser le facteur en dessous de 1,00 (ce qui serait contre-productif), la leçon est : **pour les tickets de finition/tests simples, l'estimation de référence doit être 3–5 min, pas 10–20 min**. Facteur maintenu à 1,00 ; calibration des estimations unitaires à revoir pour ces catégories.

---

## Lots actifs

### Hors lots

| ID | Titre | Prio | Est. | Créé | Démarré | Terminé |
| --- | --- | --- | --- | --- | --- | --- |
| BIZ-169 | Édition/suppression des opérations manuelles | P2 | ~25 min | 2026-05-04 | 2026-05-04 | |

---

## Détails

### BIZ-166 — Vue contacts : onglet clients par défaut + tri par récence

Onglet "Clients" activé par défaut (ordre : Clients > Fournisseurs > Tout).
Tri synthétique : facture < 6 mois en tête, puis ordre alphabétique (nom, prénom).

### BIZ-034 — Support multi-compte banque

Distinguer compte courant et compte épargne dans les données, imports et écrans.
Décisions métier nécessaires avant implémentation.

### BIZ-169 — Édition/suppression des opérations manuelles

Permettre de modifier ou supprimer les opérations bancaires créées manuellement depuis BankView (opérations sans import source).



---

## Lots terminés récents (≤ 3 jours)

| Lot | Nom | Version | Tickets | Terminé | Est. Copilot | Réel Copilot |
| --- | --- | --- | --- | --- | --- | --- |
| BIZ-170 | Gestion bordereaux en attente | v1.5 | BIZ-170 | 2026-05-05 | ~60 min | ~45 min |
| BIZ-034 | Support multi-compte banque + bugfixes comptables | v1.5 | BIZ-034, fix virement, fix journal filtré, fix fiscal_year_id manuel | 2026-05-04 | — | — |
| CR2 | Correctifs & finitions post-MOB | v1.5 | TEC-157, TEC-158, TEC-159, BIZ-165, BIZ-166, BIZ-167, BIZ-168, CHR-078 | 2026-05-04 | ~95 min | ~30 min |
| Wizard | Wizard factures & Contacts | v1.2 | BIZ-144, BIZ-145, BIZ-147, BIZ-151 | 2026-05-02 | — | — |
| CR | Correctifs revue de code | v1.3.1 | TEC-133, TEC-134, TEC-135, TEC-136, TEC-137, TEC-138, TEC-139, TEC-140, TEC-141, TEC-155 | 2026-05-02 | — | — |
| DOC | Documentation utilisateur | v1.5 | BIZ-161, BIZ-162, BIZ-163 | 2026-05-03 | ~115 min | ~45 min |
| UI | Améliorations UI & saisie | v1.4 | BIZ-149, BIZ-150, BIZ-157, BIZ-158 | 2026-05-03 | ~65 min | ~30 min |
| MOB | Mode téléphone | v1.5 | BIZ-164 | 2026-05-03 | ~90 min | — |

<details>
<summary>Lot CR2 — Correctifs &amp; finitions post-MOB (2026-05-04)</summary>

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
