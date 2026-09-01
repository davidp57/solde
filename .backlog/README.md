<!-- markdownlint-disable MD033 -->
# Backlog — Solde ⚖️

Backlog **par lot**. Les lots actifs sont des dossiers `.backlog/<LOT-ID>/`
(`PRD.md` + `tickets/NN-slug.md`) ; les lots terminés sont compactés dans
`.backlog/archive/<LOT-ID>.md`. Le **séquencement** vit dans
[`../docs/roadmap.md`](../docs/roadmap.md) ; cet index est la source de vérité pour le
**scope et le statut**.

Index maintenu **à la main** par l'agent à la création/clôture d'un lot (pas de script
générateur). Les artefacts sont créés à `⬜ ready`. Convention détaillée :
[`../docs/agents/issue-tracker.md`](../docs/agents/issue-tracker.md).

## Légende

- **Status** : ⬜ ready · 🔄 in-progress · 🧑 waiting-human · ✅ done · 🚫 wontfix
  (voir [`../docs/agents/triage-labels.md`](../docs/agents/triage-labels.md)).
- **Préfixe de ticket** : `BIZ-NNN` métier · `TEC-NNN` technique · `CHR-NNN` maintenance.
- **Priorité** : P1 important · P2 utile · P3 confort/finition.

## Lots actifs

| Lot | Statut |
|-----|--------|
| [BK3](BK3/PRD.md) — backups : ne sauvegarder que les PDFs non régénérables (BIZ-216 + garde-fou regen) | ✅ |
| [EDIT-OPS](EDIT-OPS/PRD.md) — édition/suppression des opérations bancaires manuelles (BIZ-169) | ✅ |
| [CREANCES-RAPPEL](CREANCES-RAPPEL/PRD.md) — rappel créances exercice/historique sur factures client (BIZ-210) | 🚫 |
| [RELANCES](RELANCES/PRD.md) — relances factures impayées : historique daté, templates dédiés, filtrage irrécouvrables (BIZ-218→221) | ✅ |
| [TABLE-FIT](TABLE-FIT/PRD.md) — supprimer le scroll horizontal des tableaux sur grand écran (TEC-212) | ✅ |
| [SALARY-FIX](SALARY-FIX/PRD.md) — fiabiliser les écritures comptables des salaires : net auto-validé, régénération à l'édition, garde-fou incomplet (BIZ-222 + TEC-213/214) | ✅ |
| [PAY-CANCEL](PAY-CANCEL/PRD.md) — annulation d'un règlement client non encore encaissé, réservée à l'admin (BIZ-223/224) | ✅ |
| [FY-ROLLOVER](FY-ROLLOVER/PRD.md) — bascule d'exercice depuis l'interface : pré-contrôles, ouverture avec report à nouveau, anti-chevauchement (BIZ-226 + TEC-217) | ✅ |
| [DEPOSIT-MERGE](DEPOSIT-MERGE/PRD.md) — fusionner une remise confirmée avec sa ligne de relevé au lieu de la dupliquer (BIZ-227) | ✅ |
| [DOCS](DOCS/PRD.md) — espace de documents : dépôt libre, exercice facultatif, étiquettes (BIZ-240→242) | ✅ |
| [PAY-GUARD](PAY-GUARD/PRD.md) — garde-fou à la saisie d'un règlement en espèces : montant saisi, pas pré-rempli (BIZ-250) | ✅ |
| [DEPOSIT-MERGE-2](DEPOSIT-MERGE-2/PRD.md) — rattraper la remise que la fusion automatique a manquée : date du bordereau, fenêtre élargie, rattachement manuel (TEC-250/251/252 + BIZ-251/252) | ✅ |
| [DEPOSIT-ADOPT](DEPOSIT-ADOPT/PRD.md) — confirmer un bordereau sans créer de doublon : adoption de la ligne du relevé, fusion rapprochée d'office (BIZ-253 + TEC-253) | ✅ |
| [CHECKLIST](CHECKLIST/PRD.md) — checklist mensuelle de tenue comptable : séance ordonnée par passages externes, état en base, clôture explicite (BIZ-254→256) | ⬜ |

## Lots archivés

| Lot | Version | Statut |
|-----|---------|--------|
| [RF](archive/RF.md) — refonte UI/UX (dashboard · factures · admin · mode sombre · responsive) | v1.8 | ✅ |
| [RR](archive/RR.md) — corrections post-revue de la release v1.8 | v1.8 | ✅ |
| [BK2](archive/BK2.md) — optimisation de l'espace des backups (rétention + miroir incrémental) | v1.8.1 | ✅ |
| [ML](archive/ML.md) — mailing aux adhérents actifs | v1.8.1 | ✅ |
| [_legacy-history](archive/_legacy-history.md) — ledger consolidé des lots terminés avant la restructuration (v0.2 → v1.7.3) | — | ✅ |

## Calibration estimations

Facteur de marge actuel : **1,00** (0%) — inchangé (voir note CR2).

| Lot | Estimé Copilot | Réel Copilot | Ratio | Estimé gestion | Réel gestion | Ajustement |
| --- | --- | --- | --- | --- | --- | --- |
| UI | ~65 min | ~30 min | **0,46** | 15 min | ? | ↓ facteur → 1,00 |
| CR2 | ~70 min | ~20 min | **0,29** | — | — | voir note |
| REV | ~190 min | ~70 min | **0,37** | 15 min | — | voir note REV |
| BK | ~280 min | ~2h04+ (6 tickets n/m) | **≤0,44** | 15 min | ~10 min | ratio partiel, 6 tickets non mesurés |

> Lot UI : estimations 2x trop élevées (tickets UI/bulk-replace et vérifications « déjà fait » surestimés).
> Lot CR2 : ratio 0,29 — tickets très petits (i18n, tests, nav, squelette). Leçon : pour les tickets de
> finition/tests simples, l'estimation de référence doit être **3–5 min**, pas 10–20 min. Facteur maintenu à 1,00.
> Lot REV : ratio 0,37. 3 tickets sur 11 étaient déjà traités. Leçon : avant d'estimer un « review fix »,
> vérifier si le problème existe réellement ; pour les tickets d'implémentation technique, appliquer un
> facteur **0,60** par rapport à l'estimation initiale naïve.
