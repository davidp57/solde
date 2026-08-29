# Lot PAY-GUARD — Garde-fou à la saisie d'un règlement en espèces

Status: ⬜ ready
Branch: feature/pay-guard → PR → develop

## Problem Statement

Cas réel (facture `2026-0135`, août 2026) : la facture a été encodée à **310 €** au lieu
de 270 € (remise oubliée), envoyée telle quelle, puis réglée en **espèces**. Les 270 €
reçus ont été enregistrés comme un règlement de **310 €**. Résultat : facture fausse,
règlement faux, et une caisse théorique supérieure de 40 € à la caisse réelle.

Aucune de ces trois étapes n'a produit le moindre signal. Sur la dernière, la cause est
identifiable :

- le dialogue de règlement **pré-remplit le montant avec le solde dû**
  (`InvoicePaymentDialog.vue:153`, `QuickPaymentWizard.vue:304`) ;
- la seule validation existante refuse un montant **supérieur** au solde dû
  (`InvoicePaymentDialog.vue:184`) — un montant **égal** passe sans un mot ;
- l'enregistrement se fait donc d'un clic, sans que personne ait eu à confirmer ce qui a
  réellement été compté.

Pour les espèces, la conséquence est double : le règlement crée un mouvement de caisse du
même montant (`_create_treasury_entries_for_payment`). L'écart avec la caisse physique ne
se révèle qu'au **prochain comptage**, sans lien visible avec le règlement fautif — et un
comptage enregistré n'est plus ni modifiable ni supprimable (`routers/cash.py` n'expose
que *lister* et *créer*), donc son écart reste faux même après correction.

Le chèque et le virement ne posent pas le même problème : le montant y est porté par un
document ou par le relevé bancaire, et le rapprochement finit par révéler l'écart. Les
espèces sont le seul mode où **le système n'a aucune source externe** — la saisie est la
seule chose qui atteste du montant.

## Solution

Pour un règlement en **espèces**, retirer le geste automatique : le montant n'est plus
pré-rempli, il doit être saisi. Le solde dû reste affiché, avec un bouton explicite pour
le reporter d'un clic quand c'est effectivement le montant reçu.

En complément, rattacher la saisie à une réalité vérifiable immédiatement : afficher
l'effet du règlement sur la caisse (« la caisse passera de X à Y »), en s'appuyant sur
`getCashBalance()`, déjà exposé côté frontend (`api/cash.ts:85`).

Le comportement des autres modes de paiement est inchangé : le pré-remplissage y reste
un confort légitime.

## User Stories

1. En tant que secrétaire encaissant des espèces, je veux saisir le montant que j'ai
   réellement compté plutôt que valider un montant proposé, pour ne pas enregistrer un
   encaissement que personne n'a vérifié.
2. En tant que secrétaire, je veux voir tout de suite ce que le règlement va faire au
   solde de caisse, pour rapprocher la saisie de ce que j'ai sous les yeux.
3. En tant que secrétaire encaissant le solde exact d'une facture, je veux reporter ce
   solde en un clic, pour que le garde-fou ne devienne pas une corvée au quotidien.

## Implementation Decisions

- **Espèces uniquement.** Le déclencheur est `method === 'especes'`, évalué à la volée :
  passer de « chèque » à « espèces » vide le montant, l'inverse le repropose.
- **Vider plutôt que bloquer.** Pas de case « je confirme avoir compté » : une case à
  cocher se coche aussi vite qu'un bouton se clique. C'est le champ vide qui impose le
  geste.
- **Le bouton « solde dû » est assumé.** Il rétablit le raccourci, mais en tant que
  **choix explicite** et non comme valeur par défaut. C'est la différence entre valider
  et décider.
- **Portée honnête.** Cette mesure réduit le risque, elle ne l'élimine pas : rien
  n'empêchera jamais de taper 310 sans avoir compté. Elle supprime le cas où l'erreur ne
  demande **aucun** geste.
- **Un seul endroit pour la règle.** Les deux dialogues (fiche facture et wizard rapide)
  partagent la logique via un composable, plutôt que de dupliquer la condition.
- **Aucun changement backend.** Ni schéma, ni service, ni migration : `getCashBalance()`
  et les validations existantes suffisent.

## Testing Decisions

- Ouvrir le dialogue avec « espèces » présélectionné → champ montant **vide**, bouton de
  report affichant le solde dû.
- Basculer chèque → espèces vide le montant ; espèces → chèque le repropose.
- Le bouton de report remplit le champ avec le solde dû exact (au centime).
- Validation impossible tant que le montant est vide ou nul (message existant
  `payments.errors.amount_positive`).
- Un montant inférieur au solde dû reste accepté (règlement partiel légitime) ; un montant
  supérieur reste refusé (comportement existant inchangé).
- L'effet caisse affiché correspond à `solde courant + montant saisi`, et se met à jour à
  chaque frappe.
- Mode chèque : le pré-remplissage est **inchangé** (non-régression).
- Les deux points de saisie (`InvoicePaymentDialog`, `QuickPaymentWizard`) se comportent
  à l'identique.

## Out of Scope

- **Correction ou suppression d'un comptage de caisse** enregistré (`balance_expected` et
  `difference` figés en base) — manque réel, constaté à cette occasion, mais distinct.
- Rapprochement automatique entre un écart de comptage et les règlements espèces de la
  période.
- Garde-fou à la saisie de la **facture** elle-même (remise oubliée) : rien dans le
  système ne permet de savoir qu'une remise était due.
- Avoir sur facture / facture rectificative — Solde n'a pas de type « avoir » et le total
  d'une facture client ne peut pas être négatif.
