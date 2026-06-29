# Lot RELANCES — Relances des factures impayées (historique, templates dédiés, filtrage irrécouvrables)

Status: ⬜ ready
Branch: feat/invoice-reminders → PR → develop

## Problem Statement

La gestion des factures client en retard est aujourd'hui rudimentaire. Trois manques :

1. **Aucune trace des relances** — quand le trésorier relance une facture en retard
   (bouton « Relancer »), rien n'est conservé : impossible de savoir si/quand une facture
   a déjà été relancée, ni de l'afficher dans la liste.
2. **Un seul template d'email** — l'envoi initial d'une facture et une relance utilisent
   le même texte (`email_subject_template` / `email_body_template`). Le ton d'une relance
   (rappel d'échéance, ancienneté) n'a rien à voir avec un premier envoi.
3. **Les factures irrécouvrables polluent la vue « en retard »** — `isOverdueInvoice()`
   exclut les brouillons et archivées mais **pas** les irrécouvrables. Or une créance
   abandonnée garde un montant restant dû > 0 et une échéance dépassée : elle remonte donc
   dans « en retard » (liste **et** métriques « Restant en retard »), alors qu'on a renoncé
   à la recouvrer.

## Solution

Trois livrables, sur la facture **client** uniquement :

1. **Historique des relances** — une colonne JSON `reminder_dates` (liste de dates ISO)
   sur `Invoice`, alimentée à chaque relance email **réussie**. La **dernière** date est
   affichée dans une colonne de la liste, visible **uniquement** dans le segment « en
   retard ».
2. **Templates de relance dédiés** — deux templates configurables en Paramètres, distincts
   du template d'envoi initial : **1ère relance** (jamais relancée) et **relance suivante**
   (déjà relancée, rappelle la dernière date). Le bon template est choisi automatiquement
   selon `reminder_dates`. L'envoi réutilise le **flux aperçu/envoi existant** ; seuls le
   sujet et le corps changent.
3. **Filtrage des irrécouvrables** — `isOverdueInvoice()` exclut désormais le statut
   `IRRECOVERABLE`, ce qui retire les créances abandonnées de la liste **et** des métriques
   « en retard ». Dans le segment « en retard », un **bouton bascule** à deux états permet
   d'afficher soit les factures en retard (hors irrécouvrables), soit **toutes** les
   factures irrécouvrables — les deux ensembles étant mutuellement exclusifs.

## User Stories

1. En tant que trésorier, je veux voir dans la liste des factures en retard la date de la
   dernière relance, pour savoir lesquelles relancer en priorité.
2. En tant que trésorier, je veux qu'une relance envoyée soit conservée (historique daté),
   pour ne pas relancer deux fois le même jour et adapter le ton.
3. En tant que trésorier, je veux un texte de relance distinct du premier envoi — courtois
   au premier rappel, plus ferme ensuite en mentionnant l'ancienneté.
4. En tant que trésorier, je ne veux plus voir les créances irrécouvrables dans « en retard »
   (ni dans les chiffres), mais pouvoir basculer sur la liste des irrécouvrables au besoin.

## Implementation Decisions

- **Stockage de l'historique** : colonne JSON `reminder_dates` sur `Invoice` (liste de
  dates ISO, défaut `[]`). Pas de table dédiée, pas de colonne dénormalisée. **Aucun tri /
  filtre SQL** sur cette colonne (volume faible, tri en mémoire côté front si besoin). Si un
  besoin de tri/filtre serveur émerge plus tard, migrer alors vers une table dédiée.
- **Déclencheur** : on append `date.today()` **uniquement** à l'envoi d'un email de type
  `reminder` réussi. L'envoi **initial** (DRAFT→SENT) n'alimente jamais `reminder_dates`.
  Pas de saisie manuelle de date.
- **Type d'envoi explicite** : le front indique le type (`initial` depuis « Envoyer » sur
  un brouillon, `reminder` depuis « Relancer » sur une facture en retard). Le backend choisit
  le template (initial ; ou 1ère relance si `reminder_dates` vide, sinon relance suivante) et
  n'append une date que pour `reminder`.
- **Templates** : deux jeux de champs (sujet + corps) ajoutés à `app_settings`, à côté des
  champs d'envoi initial existants. `null` ⇒ defaults intégrés.
- **Variables disponibles** (relance) : `{invoice_number}`, `{description}`,
  `{association_name}`, `{invoice_ref}` (existantes) + `{derniere_relance}` (date de la
  dernière relance, vide à la 1ère), `{montant_du}` (`total_amount − paid_amount`),
  `{echeance}` (`due_date`), `{nombre_de_relances}` (= `len(reminder_dates)`, soit les
  relances déjà faites avant celle en cours ; `0` à la 1ère).
- **Colonne « dernière relance »** : visible **uniquement** dans le segment « en retard ».
  Format date court FR `JJ/MM/AAAA` ; `—` si jamais relancée. Nombre de relances affiché
  **en tooltip** uniquement (pas en dur dans la colonne).
- **Filtrage irrécouvrables** : modifier `isOverdueInvoice()` pour exclure `IRRECOVERABLE`
  (aligne d'un coup liste + métriques). Bouton bascule **dans** le segment « en retard »
  (pas de 6ᵉ segment). Vue « irrécouvrables » = **toutes** les irrécouvrables (pas de filtre
  d'échéance). **Pas** de bouton « Relancer » sur une facture irrécouvrable.
- **Glossaire** : « irréconciliable » est proscrit (confusion avec le rapprochement
  bancaire) ; le terme canonique est « irrécouvrable » (cf. `CONTEXT.md`).

## Testing Decisions

- Append d'une date à `reminder_dates` à l'envoi `reminder` réussi ; **pas** d'append à
  l'envoi `initial` ni si l'envoi échoue.
- Sélection du template : `reminder_dates` vide ⇒ template 1ère relance ; non vide ⇒ template
  relance suivante. Résolution des variables (`{derniere_relance}`, `{montant_du}`,
  `{echeance}`, `{nombre_de_relances}`).
- `isOverdueInvoice()` renvoie `false` pour une facture `IRRECOVERABLE` même échue avec
  restant dû > 0 (liste **et** métriques).
- Bascule du segment « en retard » : par défaut, en retard hors irrécouvrables ; basculé,
  toutes les irrécouvrables et rien d'autre.
- Colonne « dernière relance » : visible seulement en segment « en retard », `—` si jamais
  relancée, date FR sinon.

## Out of Scope

- Relances sur les factures **fournisseur** (ce lot ne concerne que la facture client).
- Saisie **manuelle** d'une relance (téléphone, courrier) — uniquement les relances email.
- Métadonnées par relance (template utilisé, auteur, destinataire, canal) — historique =
  dates seules.
- Règles automatiques de relance (planification, nombre maximal, escalade) et auto-passage
  en `OVERDUE` côté serveur.
- Plus de deux variantes de message (pas de « 3ᵉ relance », etc.).

## Further Notes

Issu d'une session `/grill-with-docs` (2026-06-29). Glossaire initialisé dans `CONTEXT.md`
(facture en retard, irrécouvrable, relance).
