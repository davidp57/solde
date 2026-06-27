# Lot BK3 — Backups : ne sauvegarder que les PDFs non régénérables

Status: ⬜ ready
Branch: fix/bk3-nonregenerable-pdf-backups → PR → develop

## Problem Statement

Le lot BK2 (TEC-208 rétention + TEC-209 miroir incrémental) a réglé la saturation
OneDrive en supprimant la duplication des PDFs et en purgeant les snapshots. Reste
un gisement d'espace : le miroir distant (`solde/pdfs/`) contient **tous** les PDFs,
alors que la majorité sont **régénérables** par WeasyPrint. Seuls les PDFs de factures
**archivées** (`status=ARCHIVED`, valeur légale) et les imports `data/uploads/` (.docx)
ne le sont pas.

Le filtrage ne peut pas être activé tel quel : aujourd'hui la régénération à la
demande ne se déclenche que si `invoice.pdf_path` est **vide**. Exclure du backup le
PDF d'une facture non archivée (dont `pdf_path` est renseigné) laisserait, après une
restauration de désastre, un `pdf_path` pointant vers un **fichier absent** →
consultation cassée.

## Solution

Deux livrables séquentiels :

1. **Garde-fou de régénération** (prérequis bloquant) — régénérer le PDF d'une facture
   à la consultation/au téléchargement dès que le fichier référencé est **manquant**,
   indépendamment de la valeur de `pdf_path`.
2. **Filtre du miroir** — au moment du miroir (TEC-209), ne conserver côté distant que
   les PDFs **non régénérables** (factures archivées + `data/uploads/`), derrière un
   réglage **« Sauvegarder uniquement les PDFs non régénérables »** dans
   Paramètres › Sauvegardes, **off par défaut**.

## User Stories

1. En tant que trésorier, je veux que mes backups OneDrive ne stockent que les PDFs
   irremplaçables, pour réduire encore l'espace consommé sans perdre de pièce légale.
2. En tant qu'utilisateur, je veux qu'une facture dont le PDF a été exclu du backup
   reste consultable après restauration, le fichier étant régénéré à la volée.

## Implementation Decisions

- Le garde-fou est **indépendant** du réglage de backup : il sécurise la consultation
  dans tous les cas (et remplace la condition « `pdf_path` vide » par « fichier absent »).
- Le filtre s'applique dans `mirror_dir_incremental` (TEC-209) en fonction du statut de
  la facture liée ; les factures **archivées** et `data/uploads/` sont toujours inclus.
- Réglage **off par défaut** par prudence (un PDF régénéré peut diverger visuellement
  si le template a changé — acceptable car sans valeur légale, à documenter).

## Testing Decisions

- Régénération déclenchée quand le fichier manque **même si `pdf_path` est défini**.
- Avec le réglage activé : seuls les PDFs de factures archivées + uploads sont inclus
  dans le miroir ; les non-archivés sont exclus.

## Out of Scope

- Toute modification de la rétention des snapshots (TEC-208) ou du miroir lui-même
  (TEC-209) — livrés en BK2.

## Further Notes

Issu de BIZ-216, reporté hors de la PR BK2 (TEC-208/209) faute du garde-fou ci-dessus.
Voir l'archive [`../archive/BK2.md`](../archive/BK2.md).
