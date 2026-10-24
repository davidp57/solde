# Lot CHECKLIST — Checklist mensuelle de tenue comptable

Status: ✅ done
Branch: feature/monthly-checklist → PR → develop

## Problem Statement

La tenue mensuelle est décrite dans le manuel en **quatre workflows séparés** (émettre et
encaisser une facture, enregistrer un règlement, traiter un relevé bancaire, saisir les
salaires). Aucun ne dit dans quel **ordre** les enchaîner, et aucun ne mentionne les
**allers-retours avec l'extérieur** qui rythment la séance : faire les paies sur le site
du CEA, lancer les virements et télécharger le relevé sur celui du Crédit Mutuel.

Trois conséquences :

1. **L'ordre se redécouvre chaque mois.** Deux passages sur la banque en ligne là où un
   seul suffit, ou un relevé téléchargé avant les virements et donc à réimporter.
2. **Rien ne retient où on en est.** Une séance interrompue — le cas normal — laisse
   l'utilisateur reconstituer de mémoire ce qui est fait.
3. **Les étapes de contrôle sautent en premier.** Comptage de caisse, comparaison du
   solde au relevé : rien ne les réclame, donc elles se font quand on y pense.

Le modèle demandé est celui de l'aéronautique : une liste **ordonnée**, **cochée au fur
et à mesure**, dont l'état **survit à l'interruption**, et qui distingue ce qui se fait
dans l'application de ce qui se fait ailleurs.

## Séquence

Établie avec l'utilisateur, à partir de sa séance réelle. Principe d'ordonnancement :
**un seul passage par destination externe**, tout ce qui le conditionne étant fait avant.
Les étapes ⇢ sont externes à l'application.

**0. Reprise** — *bloc affiché uniquement s'il y a du report*
- Étapes non cochées lors de la clôture du mois précédent

**1. Saisie**
- Encoder les factures fournisseurs reçues
- Enregistrer les mouvements de caisse divers

**2. Paies**
- ⇢ Site du CEA : faire les paies du mois
- Saisir les fiches de salaire, vérifier le net calculé contre le bulletin
- Vérifier le récapitulatif mensuel (brut, net, cotisations, coût total)

**3. Passage au Crédit Mutuel** — *un seul, tout est prêt à ce stade*
- ⇢ Lancer les virements de salaires
- ⇢ Lancer les virements fournisseurs
- ⇢ Télécharger le relevé, « toutes les opérations disponibles »

**4. Relevé**
- Importer le relevé
- Vérifier les catégories détectées, corriger celles qui sont fausses
- Créer les règlements clients depuis les lignes de virement reçues
- Rapprocher les opérations restantes
- Comparer le solde de l'application au solde du relevé

**5. Caisse et remises**
- Comptage de caisse : théorique contre espèces réellement présentes
- Préparer le bordereau de remise d'espèces
- Préparer le bordereau de remise de chèques

**6. Clôture**
- Vérifier que la dernière sauvegarde est passée
- Clôturer la séance

Le dépôt physique et la confirmation des bordereaux **ne font pas partie de la séance** :
les sous partent plus tard, et la confirmation se fait au guichet depuis un téléphone,
juste après le dépôt.

Conséquence assumée : les virements lancés en 3 ne figurent pas au relevé téléchargé dans
la foulée. Ils se rapprochent à la séance suivante.

## Décisions

Prises avec l'utilisateur ; quatre vont contre la recommandation initiale et sont notées
comme telles.

1. **État en base de données** — une table portant, pour un mois donné, l'état de chaque
   étape avec son auteur et son horodatage. L'état suit d'un poste à l'autre, reste
   visible pour un second trésorier, et les mois passés forment un historique.
2. **Liste figée, livrée avec l'application** — comme une checklist constructeur : elle
   vit dans le code, évolue avec le manuel, et chaque étape interne pointe vers son
   écran. Pas d'édition par l'utilisateur.
3. **Détection sans cochage** *(recommandation suivie)* — six étapes sont détectables
   (relevé importé, fiches de salaire saisies, aucun bordereau en attente, aucune
   opération non rapprochée, comptage de caisse enregistré, sauvegarde passée). Le signal
   est **affiché à côté de l'étape**, jamais coché à la place de l'utilisateur : une
   checklist sert à vérifier, pas à constater.
4. **Mensuelle d'abord, modèle ouvert** — le modèle porte un type de période dès le
   départ pour qu'une checklist annuelle de clôture ne demande qu'une seconde liste.
5. **Clôture explicite** *(contre la recommandation d'un report automatique)* — un mois
   se déclare terminé. Un seul mois ouvert à la fois ; pour passer au suivant, on
   clôture. La clôture d'un mois incomplet est possible : un récapitulatif montre ce qui
   n'a pas été coché et demande confirmation, et ces étapes sont reportées en tête du
   mois suivant.
6. **Fenêtre appelée depuis la barre du haut** *(contre la recommandation d'un écran
   dédié)* — un bouton permanent dans l'en-tête, portant la progression (« 12/16 »),
   ouvre la checklist par-dessus l'écran courant. On coche là où l'on travaille, sans
   revenir à l'accueil.
7. **Trésorier et plus** — même niveau d'accès que les écrans Banque et Comptabilité.
8. **La facturation client est hors périmètre** *(contre la recommandation d'un point de
   contrôle)* — la gestionnaire saisit les factures clients et encode les règlements en
   chèques et en espèces ; la checklist ne liste que ce que fait le trésorier. Les
   relances d'impayés en font partie et sont donc exclues elles aussi.
9. **Bloc de reprise conditionnel** — il n'apparaît que s'il y a effectivement du report.
   Les bordereaux étant confirmés au guichet, il sera vide la plupart du temps.
10. **La séance porte le mois traité** — « Septembre 2026 », quelle que soit la date à
    laquelle elle est tenue. À l'ouverture, l'application propose le mois précédent avant
    le 15, le mois courant ensuite ; l'utilisateur peut corriger.
11. **Utilisable sur mobile** — la confirmation des bordereaux se fait déjà depuis un
    téléphone, au guichet. La fenêtre suit le responsive du reste de l'application.
12. **Un mois clôturé ne se rouvre pas** — l'historique est en lecture seule. À revoir si
    le besoin apparaît.

## Non-objectifs

- Empêcher une action parce que l'étape précédente n'est pas cochée. La checklist guide,
  elle ne verrouille pas : l'ordre réel dépend d'aléas extérieurs.
- Automatiser les étapes externes : aucune connexion au CEA ni au Crédit Mutuel.
- Cocher une étape à la place de l'utilisateur (décision 3).
