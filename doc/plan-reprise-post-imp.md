# Plan de reprise post-IMP

## Avancement depuis reprise

- [x] **Point `Comptabilite 2025` clos côté Journal** : la vue frontend charge maintenant jusqu'à `1000` écritures au lieu de `500`, ce qui couvre le cas réel déjà diagnostiqué (`930` écritures) sans remettre en cause l'import.
- [x] **Split `prenom NOM` des contacts historiques corrigé** : l'import `Contacts` découpe désormais `prenom` / `nom` quand la fin du libellé correspond à un nom en majuscules suffisamment fiable, avec fallback conservateur pour les cas ambigus.
- [x] **Chaîne d'identité contact réalignée** : preview, déduplication, création de contacts depuis les factures et rapprochement des paiements utilisent désormais la même représentation d'affichage (`prenom nom`) pour éviter les faux doublons et les mismatches après split.
- [x] **Import des factures fournisseurs historiques livré** : les lignes `Banque` et `Caisse` portant une référence `FF-...` créent désormais le contact fournisseur, la facture fournisseur historique et son paiement associé, tout en conservant l'import du mouvement de trésorerie et en gardant preview/idempotence cohérents.

## Problème

Le chantier IMP est clos, mais les essais fonctionnels font remonter un nouveau lot de besoins transverses :

1. les contacts importés depuis l'historique gardent parfois `prenom NOM` dans `nom`, avec `prenom` vide ;
2. les tables ont aujourd'hui un mélange de tri ponctuel et de filtre texte global, mais pas un comportement "Excel-like" complet sur tous les champs ;
3. la saisie des remises bancaires n'affiche pas encore de total attendu dans le flux de création/édition ;
4. les flux de trésorerie manuels (banque/caisse) n'imposent pas encore une référence de facture ;
5. le point remonté sur `Comptabilite 2025` a été diagnostiqué : l'import était correct, mais l'écran Journal tronquait l'affichage en ne chargeant que `500` écritures alors que le fichier réel en produit `930`.

## Constat actuel

- `parse_contact_sheet(...)` applique désormais une heuristique défensive pour splitter `prenom NOM` quand le suffixe majuscule est fiable ; les cas ambigus restent volontairement inchangés.
- Le domaine backend sait déjà gérer les contacts/factures fournisseurs (`InvoiceType.FOURNISSEUR`, vues et API dédiées) et l'import historique sait désormais créer ces factures à partir des références `FF-...` détectées dans `Banque` et `Caisse`, avec paiement associé et diagnostics cohérents.
- Les listes frontend ont déjà :
  - du tri ponctuel (`sortable` sur certaines colonnes) ;
  - un filtre texte générique partagé (`useTableFilter`) ;
  - parfois des filtres métier spécifiques (journal, factures).
  En revanche, on n'a pas encore un vrai dispositif homogène de tri + filtres par colonne sur tous les champs affichés.
- `BankView.vue` gère aujourd'hui la création d'une remise, mais pas d'affichage explicite du total attendu à partir des paiements sélectionnés.
- `BankTransactionCreate.reference` et `CashEntryCreate.reference` sont encore optionnels.
- Le point `Comptabilite 2025` est désormais corrigé côté UI : l'écran Journal ne tronque plus ce cas réel après relèvement de la limite de chargement à `1000`.

## Approche proposée

Traiter le chantier restant en 5 axes coordonnés :

1. **Corriger le split prénom/nom des contacts importés**
   - ajouter une heuristique sûre pour les contacts importés historiques quand le prénom est embarqué dans `nom` ;
   - s'appuyer sur la convention observée "nom toujours en MAJUSCULES" ;
   - préserver les cas ambigus via fallback conservateur.

2. **Déployer tri et filtres sur toutes les tables**
   - viser explicitement un **déploiement global** ;
   - extraire une base commune côté frontend pour éviter de réimplémenter la logique écran par écran ;
   - distinguer :
     - tri natif PrimeVue sur toutes les colonnes pertinentes ;
     - filtres par colonne adaptés au type (texte, date, enum, bool, montant) ;
     - conservation des filtres métier existants quand ils sont plus riches que le filtre générique.

3. **Durcir les flux trésorerie**
   - imposer une référence de facture (ou une règle métier explicitement équivalente) sur toutes les entrées/sorties d'argent manuelles ;
   - couvrir banque, caisse et éventuellement les flux dérivés si le formulaire permet une création hors facture ;
   - clarifier les cas autorisés où la référence n'est pas une facture client/fournisseur standard.

4. **Améliorer l'UX des remises bancaires**
   - afficher le total attendu dans le flux de remise ;
   - vérifier si un vrai écran d'édition de remise manque encore ;
   - si l'édition n'existe pas, décider si le besoin doit être traité dans le dialogue courant de création ou via un futur écran d'édition dédié.

## Todos proposés

1. [x] Corriger le split prénom/nom à l'import historique avec tests unitaires + intégration.
2. [x] Concevoir puis implémenter l'import des factures fournisseurs depuis l'historique, avec preview/import/idempotence/tests/doc.
3. Concevoir une couche frontend commune pour tri + filtres par colonne, puis la déployer sur toutes les tables.
4. Durcir les schémas, services et formulaires banque/caisse pour exiger une référence de facture sur les flux manuels.
5. Ajouter le total attendu dans le flux de remise bancaire et décider/traiter l'écart éventuel entre création et édition.
6. Revalider backend, frontend, documentation et procédure utilisateur après intégration des axes restants.

## Ordre recommandé

1. Référence obligatoire banque/caisse
2. Total attendu des remises
3. Déploiement global tri/filtres
4. Validation et documentation finale

## Notes / points d'attention

- Le point **tri/filtre sur toutes les tables** est le plus large du lot ; il faut le traiter comme un sous-chantier UX transverse, pas comme une série de micro-correctifs isolés.
- Le point `Comptabilite 2025` est **clos** : le diagnostic réel était un tronquage d'affichage du Journal, et le correctif frontend correspondant est en place.
- L'import des **factures fournisseurs** est désormais branché sur les signaux réels `FF-...` dans `Banque` / `Caisse` ; les paiements fournisseurs issus de `Caisse` utilisent en plus un trigger comptable dédié en espèces pour produire les écritures cohérentes.
- Le split prénom/nom reste volontairement défensif : la convention "nom en MAJUSCULES" est utile, mais certains cas réels restent trop ambigus pour être corrigés automatiquement sans risque.
