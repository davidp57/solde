# Lot DEPOSIT-MERGE — Fusionner une remise avec la ligne du relevé

Status: ✅ done
Branch: feature/deposit-import-merge → PR → develop

## Problem Statement

Chaque remise en banque produisait **deux opérations** pour un seul mouvement réel :

1. à la confirmation du bordereau, `confirm_deposit` crée une transaction `manual` pour
   créditer le compte immédiatement ;
2. à l'import du relevé, la banque apporte la même opération avec sa propre référence.

Rien ne les rapproche : l'import ne déduplique que sur `reference`, et la référence
bancaire (`LF9UM92LLO`) n'a aucun rapport avec celle générée par Solde (`DEP-CHQ-6`). Le
solde comptait donc chaque remise deux fois, jusqu'à ce que l'utilisateur supprime la
provisoire à la main — geste à refaire à chaque remise, et invisible pour qui ne le sait
pas. Cinq bordereaux confirmés en production, donc cinq nettoyages manuels déjà faits.

Le cas a été découvert par un écart de solde de 526 € qui, après enquête, n'était que
l'affichage périmé d'un nettoyage correct (corrigé par TEC-218) — mais il a mis au jour
le doublon structurel.

## Solution

À l'import d'un relevé, une ligne reconnue comme remise est **absorbée** par la
transaction provisoire correspondante au lieu d'en créer une seconde.

Critères de correspondance, tous requis : même compte, même montant, catégorie de remise
détectée sur la ligne du relevé, transaction existante `manual` **non rapprochée** dont
la catégorie est aussi une remise, dans une fenêtre de **± 3 jours**.

Si **plusieurs** candidates correspondent, aucune fusion : la ligne est importée
normalement et l'ambiguïté est journalisée. On ne devine pas.

## User Stories

1. En tant que trésorier, je veux qu'une remise déjà enregistrée dans Solde ne réapparaisse
   pas une deuxième fois à l'import du relevé, pour que mon solde reste juste sans ménage.
2. En tant que trésorier, je veux savoir combien de remises ont été rapprochées lors d'un
   import, pour comprendre pourquoi le nombre d'opérations importées est plus petit que le
   nombre de lignes du fichier.

## Implementation Decisions

- **La ligne conservée est celle de Solde, mise à jour** : elle prend la date, la
  référence et la source du relevé, mais garde sa description — « Remise de chèques
  (bordereau #6) » nomme le bordereau, là où le libellé bancaire (« REM CHQ REF05001A05 »)
  n'apprend rien. L'identifiant reste stable, rien de ce qui pointe dessus n'est cassé.
- **Fenêtre de ± 3 jours** : sur les cinq bordereaux réels, la ligne provisoire et celle du
  relevé portaient toujours **la même date** (la transaction est datée du jour de
  confirmation, et la confirmation se fait le jour du crédit). Trois jours couvrent le
  décalage sans ouvrir la porte aux faux positifs.
  **Démenti par le bordereau #7** (confirmé six jours après le crédit) : la date de la
  ligne provisoire vient désormais du bordereau et la fenêtre est passée à ± 10 jours —
  voir [DEPOSIT-MERGE-2](../DEPOSIT-MERGE-2/PRD.md).
- **Non rapprochée seulement** : une ligne déjà rapprochée est un mouvement traité, on n'y
  touche pas.
- **Le point d'entrée est l'import** (`_import_rows`), donc les trois formats — CSV, OFX,
  QIF — en bénéficient sans duplication de code.
- **Comptage séparé** : `BankImportResult.merged` distingue les lignes fusionnées des
  lignes créées, et le message de fin d'import l'annonce.

## Testing Decisions

- Fusion nominale : une seule transaction subsiste, elle porte la référence bancaire et la
  source du relevé, et conserve la description de Solde.
- Refus de fusion : montant différent, date hors fenêtre, deux candidates, ligne déjà
  rapprochée, ligne de relevé qui n'est pas une remise.
- Intégration : un import OFX contenant la remise renvoie `merged = 1`, `created = []`, et
  la base ne contient qu'une seule opération.

## Out of Scope

- Nettoyage des doublons historiques : vérifié sur la base de production, il n'en reste
  aucun.
- Rapprochement automatique de la ligne fusionnée avec les paiements du bordereau.
- Détection de doublons entre deux imports de formats différents.
