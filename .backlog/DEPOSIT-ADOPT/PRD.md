# Lot DEPOSIT-ADOPT — Confirmer un bordereau sans créer de doublon

Status: ✅ done
Branch: feature/deposit-adopt-statement-row → PR → develop

## Problem Statement

Suite de [DEPOSIT-MERGE-2](../DEPOSIT-MERGE-2/PRD.md). Le parcours réel a été rejoué pas
à pas sur une restauration de la production :

| étape | journal bancaire | solde |
|---|---|---|
| relevé importé | `REM CHQ REF05001A05` · 111 € · non rapprochée | 1 191,72 € |
| bordereau #8 confirmé | **+ une ligne `manual` de 111 €** | **1 302,72 €** |
| rattachement manuel | une seule ligne, Import OFX, **non rapprochée** | 1 191,72 € |

Deux défauts distincts :

1. **Le doublon n'avait pas lieu d'être.** `confirm_deposit` crée sa ligne provisoire
   sans jamais regarder si le mouvement figure déjà au relevé. L'import sait pourtant
   regarder dans l'autre sens depuis BIZ-227. Quand le relevé arrive **avant** la
   confirmation — le cas courant d'un bordereau confirmé en retard — on crée un doublon
   puis on demande à l'utilisateur de le résorber. Le solde est faux entre les deux.
2. **La ligne fusionnée reste « à rapprocher ».** Après fusion, la ligne *est* le
   bordereau : la correspondance est établie par construction. Réclamer un clic de plus
   n'apporte rien et laisse la ligne dans la file des opérations à traiter.

## Solution

- **Adoption à la confirmation** — image symétrique de l'absorption à l'import : à la
  confirmation, chercher une ligne de relevé non rapprochée, du même montant et de la
  **même** catégorie de remise, dans la fenêtre de ± 10 jours autour de la date du
  bordereau. S'il y en a exactement une, l'adopter (reprendre le libellé qui nomme le
  bordereau, la marquer rapprochée) au lieu d'en créer une seconde. Zéro ou plusieurs
  candidates : comportement inchangé, on ne devine pas.
- **Rapprocher à la fusion** — les deux chemins de fusion (automatique à l'import,
  manuel depuis la ligne du relevé) marquent la ligne rapprochée et renseignent la
  référence comptable avec « Bordereau #N ».

## Implementation Decisions

- **Catégorie exacte, pas « une remise »** : un dépôt d'espèces du même montant ne doit
  jamais être adopté par un bordereau de chèques. La détection sur le libellé bancaire
  distingue déjà `VRST` de `REM CHQ`.
- **La ligne adoptée garde la date, la référence et la source de la banque** ; seul le
  libellé passe à celui de Solde, qui nomme le bordereau. Cohérent avec BIZ-227.
- **Marquer rapproché ne génère aucune écriture** : les catégories de remise sont
  volontairement absentes de `_BANK_CATEGORY_TRIGGER` (les écritures sont produites par
  `generate_entries_for_deposit`). C'est un pur changement d'état.
- **Référence comptable déduite de la référence de la ligne provisoire**
  (`DEP-ESP-8` / `DEP-CHQ-8`). Si l'utilisateur a saisi sa propre référence bancaire sur
  le bordereau, le numéro n'est pas récupérable : la colonne reste vide plutôt que de
  porter une valeur devinée — le lien vers le bordereau vit alors dans le libellé.

## Out of scope

Clé étrangère `deposit_id` sur `bank_transactions`, toujours. Elle rendrait la référence
comptable exacte dans tous les cas, y compris avec une référence bancaire personnalisée.
