# Lot CHECKLIST — Checklist mensuelle de tenue comptable

Status: ⬜ ready
Branch: —

## Problem Statement

La tenue mensuelle est décrite dans le manuel en **quatre workflows séparés** (émettre et
encaisser une facture, enregistrer un règlement, traiter un relevé bancaire, saisir les
salaires). Aucun ne dit dans quel **ordre** les enchaîner, et aucun ne mentionne les
**allers-retours avec l'extérieur** qui rythment pourtant le mois : récupérer les
bulletins sur la plateforme de paie, exécuter les virements depuis la banque en ligne,
porter les chèques et les espèces au guichet, télécharger le relevé.

Trois conséquences :

1. **L'ordre se redécouvre chaque mois.** Télécharger le relevé avant d'avoir exécuté les
   virements oblige à un second import. Confirmer un bordereau après avoir importé le
   relevé fonctionne désormais (BIZ-253) mais laisse la caisse fausse entre-temps.
2. **Rien ne retient où on en est.** Une session interrompue — le cas normal, la
   comptabilité se tient entre deux autres choses — laisse l'utilisateur reconstituer de
   mémoire ce qui est fait. C'est ainsi qu'un bordereau reste non confirmé pendant un
   mois, ou qu'une remise passe à la banque sans exister dans l'application.
3. **Les étapes de contrôle sautent en premier.** Comptage de caisse, comparaison du
   solde avec le relevé, relances : rien ne les réclame, donc elles se font quand on y
   pense.

Le modèle demandé est celui de l'aéronautique : une liste **ordonnée**, **cochée au fur
et à mesure**, dont l'état **survit à l'interruption**, et qui distingue ce qui se fait
dans l'application de ce qui se fait ailleurs.

## Séquence proposée

Le principe d'ordonnancement : **regrouper tout ce qui se fait dans Solde avant chaque
sortie vers l'extérieur**, pour ne faire qu'un aller-retour par destination. Les étapes
marquées ⇢ sont externes à l'application.

**1. Saisir ce qui est arrivé**
1. Créer, valider et envoyer les factures clients du mois
2. Encoder les factures fournisseurs reçues
3. Enregistrer les règlements reçus (chèques, espèces, virements déjà identifiés)
4. Enregistrer les mouvements de caisse hors règlements

**2. Salaires** — aller-retour n° 1 : plateforme de paie
5. ⇢ Récupérer les bulletins du mois sur la plateforme CEA
6. Saisir les fiches de salaire, vérifier le net calculé contre le bulletin
7. Vérifier le récapitulatif mensuel (brut, net, cotisations, coût total)

**3. Préparer les sorties** — aller-retour n° 2 : banque en ligne
8. Relever les factures fournisseurs à payer et les salaires nets à verser
9. ⇢ Exécuter les virements depuis la banque en ligne
10. Préparer les bordereaux de remise (chèques, espèces)

**4. Passage à la banque** — aller-retour n° 3 : guichet
11. ⇢ Déposer les chèques et les espèces
12. Confirmer les bordereaux au retour — c'est ce geste qui sort l'argent de la caisse

**5. Relevé** — aller-retour n° 4 : banque en ligne
13. ⇢ Télécharger le relevé OFX, une fois les virements et les remises passés
14. Importer le relevé
15. Vérifier les catégories détectées, corriger celles qui sont fausses
16. Rapprocher les opérations restantes

**6. Contrôles de fin de mois**
17. Comptage de caisse : solde théorique contre espèces réellement présentes
18. Comparer le solde bancaire de l'application au solde du relevé
19. Passer en revue les impayés et lancer les relances
20. Vérifier que la dernière sauvegarde est passée

## Questions ouvertes (à trancher avant découpage)

1. **Où vit la checklist ?** Écran dédié, panneau sur l'accueil, ou fenêtre appelée
   depuis l'accueil.
2. **Où vit son état ?** Une instance par mois en base (partagée entre postes et entre
   utilisateurs, historisable) ou stockage local du navigateur (aucun changement de
   schéma, mais perdu en changeant de poste et invisible pour un second utilisateur).
3. **Cochage automatique ?** Certaines étapes sont détectables — relevé importé ce
   mois-ci, fiches de salaire saisies, bordereaux confirmés, comptage de caisse
   enregistré, sauvegarde réussie. Les cocher d'office, les proposer comme suggestion,
   ou tout laisser au manuel.
4. **Contenu figé ou modifiable ?** Liste livrée avec l'application, ou étapes que
   l'utilisateur peut renommer, ajouter, supprimer, réordonner.
5. **Quelle granularité de période ?** Mensuelle seulement, ou aussi une checklist
   annuelle de fin d'exercice (l'ordre de clôture est déjà documenté et non outillé).
6. **Que fait-on d'un mois non terminé ?** Le mois suivant s'ouvre-t-il quand même, la
   checklist précédente reste-t-elle consultable, signale-t-on ce qui n'a pas été coché.

## Non-objectifs

- Empêcher une action parce que l'étape précédente n'est pas cochée. La checklist guide,
  elle ne verrouille pas : l'ordre réel dépend d'aléas extérieurs.
- Automatiser les étapes externes (aucune connexion à la banque ni à la plateforme de
  paie).
