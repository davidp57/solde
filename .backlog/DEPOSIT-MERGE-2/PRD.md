# Lot DEPOSIT-MERGE-2 — Rattraper la remise que la fusion automatique a manquée

Status: 🔄 in-progress
Branch: fix/deposit-merge-window → PR → develop

## Problem Statement

[DEPOSIT-MERGE](../DEPOSIT-MERGE/PRD.md) (BIZ-227) devait supprimer le doublon entre la
ligne provisoire créée à la confirmation d'un bordereau et la ligne du relevé. Le
bordereau **#7** l'a pris en défaut :

| | date |
|---|---|
| Bordereau (`deposits.date`) | 03/08/2026 |
| Écritures comptables | **03/08** — `generate_entries_for_deposit` date sur `deposit.date` |
| Ligne provisoire en banque | **09/08** — `date.today()` au moment de la confirmation |
| Crédit réel de la banque | **04/08** |

Cinq jours d'écart, pour une fenêtre de fusion de trois : les deux lignes ont été
conservées et l'utilisateur a dû supprimer la provisoire à la main — le geste que
BIZ-227 était censé supprimer.

La cause n'est pas la fenêtre mais la **date de la ligne provisoire** :
`confirm_deposit` la datait du jour du clic. Une confirmation tardive — cas banal, on
confirme quand on y repense — produit donc une date que la banque n'a jamais utilisée,
en désaccord avec les écritures comptables du même bordereau.

Le PRD de BIZ-227 pariait explicitement sur « la confirmation se fait le jour du
crédit », sur la foi des cinq bordereaux existants. Le sixième a démenti le pari.

## Solution

Trois volets, du plus structurant au filet de sécurité :

1. **Dater le mouvement sur le bordereau.** La ligne bancaire et la sortie de caisse
   prennent `deposit.date` — le jour où la remise a été portée à la banque — au lieu du
   jour de confirmation. Elles rejoignent ainsi les écritures comptables, déjà datées
   de là. `confirmed_date` continue d'enregistrer *quand* la confirmation a eu lieu.
2. **Élargir la fenêtre de fusion à ± 10 jours.** La date du bordereau reste
   déclarative : elle peut précéder le dépôt réel de quelques jours. La garde « une
   seule candidate » interdit toujours de deviner.
3. **Rattraper depuis l'interface.** Quand la fusion n'a pas eu lieu, une action sur la
   ligne du relevé permet de désigner le bordereau : les deux lignes n'en font plus
   qu'une. Plus aucune raison de supprimer une ligne à la main.

## User Stories

1. En tant que trésorier, je veux qu'une remise confirmée en retard soit tout de même
   reconnue à l'import, pour ne pas avoir de doublon à nettoyer.
2. En tant que trésorier, quand le rapprochement automatique n'a pas eu lieu, je veux
   désigner moi-même le bordereau correspondant depuis la ligne du relevé, plutôt que
   de supprimer une ligne et rapprocher l'autre.

## Implementation Decisions

- **`deposit.date` plutôt que `confirmed_date`** : c'est la date que le reste du
  système utilise déjà pour ce bordereau (écritures comptables, `payment.deposit_date`).
  La ligne bancaire et la sortie de caisse étaient les deux seules à s'en écarter.
- **Sortie de caisse alignée elle aussi** : dater le crédit bancaire du 03 en laissant
  la sortie de caisse au 09 ferait entrer l'argent en banque six jours avant d'avoir
  quitté la caisse.
- **± 10 jours** : couvre un bordereau préparé une semaine avant d'être porté, sans
  atteindre la remise du mois suivant. Au-delà, le volet 3 prend le relais.
- **Le rattrapage manuel exige le même montant, sans fenêtre de date** : c'est
  l'utilisateur qui désigne, la proximité de date ne sert qu'à ordonner la liste.
- **La ligne conservée reste celle du bordereau**, comme dans BIZ-227 : elle prend la
  date, la référence et la source du relevé, garde sa description, et la ligne importée
  est supprimée. Cohérent avec la fusion automatique, et l'identifiant reste stable.

## Out of scope

- Clé étrangère `deposit_id` sur `bank_transactions`. Le lien vers le bordereau reste
  textuel (description) et disparaît de la référence après fusion. À traiter séparément
  si l'on veut afficher le bordereau d'origine sur la ligne bancaire.
