# Lot RF — Refonte UI/UX (tableau de bord · factures · admin · mode sombre · responsive)

Status: ✅ done
Version: v1.8 — released 2026-06-21
Branch(es): PR #96 → release/1.8.0

Source : `design_handoff_solde_refonte-v2/` (handoff Claude Design). Reprise de la
**hiérarchie de l'information**, **mutualisation des composants dupliqués** et
**adaptation mobile/tablette/desktop**, dans l'identité Solde (Manrope, emerald, slate).
Couleurs mappées sur les tokens du thème (pas d'inline-styles). Ordre de livraison :
`InvoiceWorkspace` → mode sombre → tableau de bord/admin → responsive transverse.

| Ticket | Titre | Prio | Statut |
|--------|-------|------|--------|
| TEC-193 | Composant `InvoiceStatusBadge` mutualisé | P2 | ✅ |
| TEC-194 | Composant `InvoiceWorkspace` paramétré par type | P1 | ✅ |
| BIZ-206 | Migrer vues factures client/fournisseur → `InvoiceWorkspace` | P1 | ✅ |
| TEC-195 | Store/bascule thème clair-sombre topbar (déjà couvert via `useDarkMode`) | P2 | ✅ |
| TEC-196 | Tokens de thème clair/sombre (preset Aura dark) + rayons sobres | P2 | ✅ |
| TEC-197 | Composant `AppWorklist` mutualisé (« À traiter » / anomalies) | P2 | ✅ |
| BIZ-207 | Refonte `DashboardView` — héro trésorerie, file à traiter, graphe unique | P1 | ✅ |
| TEC-198 | Enrichissement API dashboard (`to_reconcile_count`) | P3 | ✅ |
| BIZ-208 | Refonte `UsersView` — matrice de rôles vivante + filtres | P2 | ✅ |
| BIZ-209 | Refonte `SystemView` — bandeau d'état, anomalies, restauration isolée | P2 | ✅ |
| TEC-199 | Shell de navigation adaptatif (3 breakpoints) | P2 | ✅ |
| TEC-200 | Responsive des écrans refondus (table→cartes, KPI, FAB, cibles ≥44px) | P2 | ✅ |
| TEC-201 | Généraliser `AppRowActions` + `AppFilterSegments` | P2 | ✅ |
| BIZ-211 | Rollout actions de ligne + segments aux autres écrans | P2 | ✅ |
| TEC-202 | Refonte Admin — `AppSettingRow` (motif ligne de réglage) | P2 | ✅ |
| BIZ-212 | Refonte Supervision — 2 onglets (État & surveillance / Sauvegardes) | P2 | ✅ |
| BIZ-213 | Refonte Paramètres — 4 onglets + lignes de réglage + barres d'enregistrement | P1 | ✅ |
| CHR-195 | Quality gate + CHANGELOG + docs + release v1.8 | P2 | ✅ |

## Notes de clôture

- **TEC-195** : mode sombre déjà existant via `composables/useDarkMode.ts` (persistance
  `solde-dark-mode`, classe `html.dark-mode`, anti-FOUC) + bascule lune/soleil. Non
  réécrit en store Pinia (équivalent fonctionnel). Reliquat optionnel : `prefers-color-scheme`.
- **BIZ-207** : livré avec dégradation gracieuse (delta trésorerie + sparkline dérivés
  côté front depuis `getResourcesChartApi`). « Opérations à rapprocher » et « adhérents »
  initialement omis faute de donnée API (rapprochement ajouté en TEC-198).
- **TEC-198** : seul `to_reconcile_count` ajouté (transactions `reconciled == False`).
  Pas d'entité adhérent dans le modèle → carte « Adhérents » de la maquette sans objet.
