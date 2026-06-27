# Lot RR — Corrections post-revue de la release v1.8

Status: ✅ done
Version: v1.8 — released 2026-06-21
Branch(es): release/1.8.0

Constats de la revue détaillée de la PR #96 (réalisée à la place de Sourcery, PR trop
volumineuse pour l'outil). Aucun blocker ; corrections de qualité, accessibilité et
couverture de tests, appliquées sur `release/1.8.0`.

| Ticket | Titre | Prio | Statut |
|--------|-------|------|--------|
| TEC-203 | Shell mobile : masquer barre d'onglets si < 2 items, aria-label burger, hauteurs en CSS vars | P2 | ✅ |
| TEC-204 | a11y filtres/bascule : `AppFilterSegments` en `role="group"` + `aria-pressed` ; `InvoiceTypeToggle` en liens `aria-current` | P2 | ✅ |
| TEC-205 | Util `formatCurrency` mutualisé (`utils/format.ts`) + dédup des `Intl.NumberFormat` | P2 | ✅ |
| TEC-206 | Chevauchement de breakpoint `main.css` (`max-width: 768px` → `767px`) | P3 | ✅ |
| TEC-207 | Couverture de tests : item « À rapprocher » dashboard + montant entonnoir | P2 | ✅ |
| BIZ-214 | Factures : dédoublonner « Envoyer email » quand « Relancer » est l'action principale | P3 | ✅ |
