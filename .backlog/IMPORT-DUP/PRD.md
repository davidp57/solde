# Lot IMPORT-DUP — Doublons d'import bancaire : les signaler, pouvoir les supprimer

Status: ✅ done
Branch: feature/import-dup → PR → develop

## Problem Statement

Cas réel (01/09/2026). Le solde du compte d'épargne affiché dans l'écran Banque
(39 820,46 €) ne correspondait ni à la balance comptable (42 820,46 €) ni au relevé de
la banque (42 820,46 €, confirmé par les extraits Crédit Mutuel n° 052 et 053). Cause :
le virement interne du 01/05/2026 figure **deux fois** dans le relevé de l'épargne.

- `#373` — saisie manuelle du 04/05/2026, libellé « Virement interne », **sans
  référence**, rapprochée ;
- `#410` — la même opération, ramenée par l'import OFX du 30/06/2026, libellé
  « VIR COMPTE COURANT ASSOCIATION », référence `LXS01G6OCF`, non rapprochée.

Deux défauts se sont additionnés :

1. **La dédup à l'import ne voit que les références.** `add_transaction` écarte une
   ligne dont la `reference` existe déjà (le FITID de l'OFX). Une opération saisie à la
   main n'en porte aucune : rien ne pouvait rapprocher les deux. Le garde-fou
   `get_excel_cutoffs` ne couvre que les sources `import` / `import_excel`, pas
   `manual`.
2. **Le doublon était incorrigible depuis l'interface.** `#373` est rapprochée, or la
   suppression refuse une opération rapprochée — et il n'existe aucun moyen de
   dé-rapprocher. `#410` n'est pas rapprochée, mais la suppression était réservée aux
   opérations **manuelles**. Aucune des deux lignes ne pouvait partir : la seule issue
   restante était une intervention SQL sur la base de production.

Le second défaut est le plus grave : il vaut pour **tout** doublon d'import, quelle
qu'en soit l'origine. La comptabilité, elle, n'a jamais été fausse — un virement interne
ne génère ses écritures que depuis le côté compte courant (choix documenté dans
`accounting_engine.generate_entries_for_bank_transaction`), donc une ligne d'épargne
en trop n'a aucun effet comptable. Ce qui explique aussi que l'écart ait pu vivre deux
mois sans être détecté : sur l'épargne, relevé et comptabilité sont deux chaînes
parallèles qui ne se confrontent nulle part.

## Solution

1. **Autoriser la suppression d'une opération importée non rapprochée** (OFX / CSV /
   QIF). Les lignes issues d'un **import Excel** restent verrouillées.
2. **Signaler les doublons probables au retour d'un import** — même compte, même
   montant, à quelques jours près — sans jamais en écarter un tout seul, et offrir la
   suppression sur place, les deux lignes côte à côte.

## User Stories

1. En tant que trésorier, je veux supprimer une ligne de relevé importée en double, pour
   que le solde affiché redevienne celui de ma banque.
2. En tant que trésorier, je veux qu'un import me signale ce qui ressemble à une
   opération déjà enregistrée, pour ne pas découvrir l'écart deux mois plus tard.
3. En tant que trésorier, je veux arbitrer moi-même laquelle des deux lignes part, pour
   garder celle qui porte la référence de la banque.

## Implementation Decisions

- **Signaler, ne pas écarter.** Un skip automatique aurait supprimé `#410` — la ligne
  qui porte la référence bancaire et le libellé de la banque — au profit d'une saisie
  manuelle approximative, et surtout aurait masqué l'anomalie au lieu de la montrer.
  La ligne est donc **importée**, puis remontée dans le résultat d'import avec celle
  qu'elle duplique probablement.
- **Critères de l'appariement** (`bank_service.find_probable_duplicate`) : même compte,
  même montant, écart de date ≤ 3 jours, la candidate **sans référence** et de **source
  différente**. Les deux dernières conditions évitent le bruit : une ligne importée qui
  portait déjà une référence aurait été écartée en amont par la dédup existante, et
  comparer deux lignes de même source revient à suspecter le fichier lui-même.
- **Fenêtre de 3 jours** : une ligne saisie à la main porte rarement la date de valeur
  que la banque publiera ensuite.
- **Sources supprimables** (`bank_service.DELETABLE_SOURCES`) : `manual`,
  `system_opening`, `import_csv`, `import_ofx`, `import_qif`. `import_excel` et le
  legacy `import` sont exclus — l'import réversible tient le registre des lignes qu'il a
  créées (`import_effects`), et en supprimer une dans son dos casserait l'annulation du
  run. Le garde-fou « opération rapprochée » est inchangé.
- **L'édition reste réservée aux opérations manuelles** : `canEditOrDelete` conserve son
  périmètre, seule la suppression s'élargit. Corriger une ligne de relevé reviendrait à
  réécrire ce que la banque a dit ; la supprimer, non.
- **Cette décision révise l'*Out of Scope* du lot EDIT-OPS** (« les opérations importées
  restent en lecture seule ») : elles le restent à l'édition, plus à la suppression.

## Testing Decisions

- Suppression : ligne OFX non rapprochée → 204 ; ligne OFX rapprochée → 422 ; ligne
  Excel → 422 ; ligne manuelle → 204 (inchangé).
- Appariement : saisie manuelle + import du même mouvement → une paire signalée ; à
  2 jours d'écart → signalée ; à 11 jours → non signalée ; montant différent → non
  signalée.
- Le réimport du même fichier reste un `skipped` par référence, sans rien à arbitrer.
- La ligne signalée peut effectivement être supprimée dans la foulée.

## Out of Scope

- **Le dé-rapprochement d'une opération** — manque distinct et plus large (il faudrait
  aussi défaire les écritures comptables générées). Sans lui, une ligne rapprochée en
  double reste incorrigible ; ici c'est l'autre côté de la paire qu'on supprime.
- La correction des données de production : le doublon `#373` / `#410` se supprime
  depuis l'interface une fois ce lot déployé.
- Un écran de contrôle « relevé vs balance » par compte de trésorerie : écarté par
  l'utilisateur, qui fait ce pointage à la main en fin de comptabilité mensuelle.
- La détection rétrospective des doublons déjà en base : seul l'import en signale.
