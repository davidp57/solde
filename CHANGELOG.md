# Changelog

<!-- markdownlint-disable MD024 MD036 -->

Toutes les modifications notables apportées à Solde ⚖️ sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Ce projet respecte le [Versionnage sémantique](https://semver.org/lang/fr/).

---

## [Non publié]

### Ajouté
- **BIZ-231** — **Bascule « Tout l'historique » sur les écrans Factures et Paiements**, à l'image de celle de la caisse. Ces écrans bornent leurs listes à l'exercice sélectionné : une facture ou un règlement daté hors de cet exercice — ou hors de tout exercice, cas classique au changement d'année — n'apparaissait nulle part, sans indication. La bascule lève le filtre de dates et recharge sans borne (factures client, factures fournisseur, paiements).

### Modifié
- **CHR-020** — **Image Docker construite aussi sur `develop`**. Chaque merge sur `develop` publie désormais une image de test `ghcr.io/davidp57/solde:develop`, déployable sur le NAS via `SOLDE_IMAGE`. Le tag `latest` — celui que tire la production par défaut — reste **réservé à `main`** : sans cette restriction, un build depuis `develop` aurait silencieusement envoyé une image de test en production au prochain `docker pull`. Chaque branche construite reçoit en plus un tag à son nom, et le tag `sha-<court>` permet d'épingler un commit précis.

### Ajouté
- **BIZ-229** — **Avertissement quand une date sort de tout exercice comptable**. Saisir une écriture datée hors de tout exercice déclaré la rendait invisible partout : aucun écran filtré par exercice ne la montre, et son écriture comptable part sans `fiscal_year_id`. Les formulaires de saisie (entrée de caisse, comptage de caisse, opération bancaire manuelle, règlement de facture et assistant de règlement rapide) affichent désormais un avertissement dès que la date choisie n'est couverte par aucun exercice. Le message informe sans bloquer : il invite à créer l'exercice ou à corriger la date. Cas réel : un comptage saisi le 3 août, l'exercice suivant n'ayant pas encore été ouvert.
- **BIZ-230** — **Bascule « Tout l'historique » dans l'écran Caisse**. Le journal et les comptages étaient systématiquement bornés à l'exercice sélectionné, sans moyen de voir ce qui existait en dehors. Un interrupteur lève ce filtre et recharge sans borne de dates, sur le modèle de « À remettre en banque » de l'écran Paiements.

### Ajouté
- **BIZ-228** — **Total du comptage de caisse calculé en direct**. Le dialogue de comptage n'affichait aucun total : il fallait enregistrer pour connaître le montant compté. Le total se met désormais à jour à chaque frappe, avec le détail billets/pièces et l'**écart par rapport au solde théorique** de la caisse — l'écart étant précisément ce qu'un comptage cherche à mettre en évidence.
- **BIZ-227** (Lot DEPOSIT-MERGE) — **Une remise n'apparaît plus deux fois**. Confirmer un bordereau créait une opération bancaire pour créditer le compte tout de suite ; l'import du relevé apportait ensuite le même mouvement avec la référence de la banque. Rien ne les rapprochait (la déduplication ne porte que sur `reference`), donc le solde comptait chaque remise deux fois jusqu'à un nettoyage manuel. À l'import, une ligne reconnue comme remise est désormais **absorbée** par l'opération provisoire correspondante — même compte, même montant, catégorie remise, non rapprochée, à ± 3 jours. La ligne conserve la description de Solde (qui nomme le bordereau) et prend la date, la référence et la source du relevé. En cas d'ambiguïté (plusieurs candidates), **aucune fusion** : la ligne est importée normalement et le cas est journalisé. Le résultat d'import distingue les opérations créées des remises rapprochées, et l'annonce en fin d'import.
- **BIZ-226** (Lot FY-ROLLOVER) — **Bascule d'exercice utilisable depuis l'interface**. Le moteur était complet côté serveur, mais aucun écran n'appelait `open-next` (création de l'exercice suivant **avec reports à nouveau**) ni `pre-close-checks` — les fonctions front correspondantes existaient pourtant, en code mort. L'utilisateur n'avait donc que « Nouvel exercice », qui crée une période **sans reprise des soldes** : banque, caisse, créances et dettes repartaient à zéro.
  - La fenêtre de clôture affiche désormais les **vérifications avant clôture** (balance déséquilibrée, écritures sans exercice) ; elles informent sans bloquer.
  - Une action **« Ouvrir le prochain exercice »** apparaît sur un exercice clôturé sans successeur, avec nom et dates pré-remplis dans la continuité (lendemain de la fin, douze mois), et génère les reports à nouveau.
  - Manuel utilisateur : procédure de fin d'exercice, ordre à respecter, et mise en garde explicite sur « Nouvel exercice ».

### Corrigé
- **TEC-217** (Lot FY-ROLLOVER) — Deux exercices comptables ne peuvent plus **se chevaucher** : la création (et l'ouverture du suivant) est refusée en `422 FISCAL_YEAR_OVERLAP` en nommant l'exercice en conflit. Des périodes recouvrantes rendaient l'exercice d'une écriture dépendant de l'ordre de tri de `find_fiscal_year_for_date`.
- **FY-ROLLOVER** — Les dates du nouvel exercice sont calculées sur les composantes locales et non via `toISOString()`, qui décalait la frontière d'exercice d'un jour à l'est de Greenwich.
- **TEC-218** — **Soldes bancaires périmés à l'écran après suppression d'une opération**. Supprimer une opération manuelle ne retirait que la ligne du tableau côté navigateur, alors que le serveur recalcule le `balance_after` de **toutes** les opérations suivantes (`recompute_bank_balances`). Les lignes postérieures gardaient donc leur ancien solde à l'écran, gonflé du montant supprimé — donnant l'impression d'une comptabilité fausse juste après un nettoyage pourtant correct (cas réel : deux remises supprimées, soldes affichés 526 € trop hauts alors que la base était juste). La liste est désormais rechargée depuis le serveur après suppression.
- **TEC-219** — **Écran Caisse : un règlement fournisseur en espèces était étiqueté « Paiement client »**. Le libellé d'origine était déduit de la seule source de l'écriture (`payment`), sans tenir compte du sens du mouvement. Le montant et le sens étaient corrects (sortie de caisse), seul l'intitulé induisait en erreur. L'origine distingue désormais **Règlement client** (entrée) et **Règlement fournisseur** (sortie).

## [1.10.0] — 2026-08-03

### Ajouté
- **BIZ-223 / BIZ-224** (Lot PAY-CANCEL) — **Annulation d'un règlement non encore encaissé**, réservée à l'**administrateur**. Un règlement était jusqu'ici immuable après création (`delete_payment` refusait systématiquement, montant/date/mode figés par la politique BL-030) : une saisie erronée — par exemple deux chèques réglant une même facture enregistrés comme un seul règlement — n'avait aucune correction possible.
  - **Règle d'éligibilité** : facture **client**, règlement **non encaissé** (`deposited = false`), **aucun** lien avec une opération bancaire, exercice **non clôturé**. Les espèces et les virements issus du rapprochement sont exclus mécaniquement (déjà `deposited` à la création).
  - **Effets** : détachement du bordereau de remise non confirmé (total recalculé, ou bordereau supprimé s'il ne restait que ce règlement), suppression des écritures comptables `source_type=payment`, suppression du règlement, recalcul du statut de la facture, journalisation dans l'audit.
  - **API** : `DELETE /api/payments/{id}` passe en **admin uniquement** et renvoie un `409` porteur d'un code explicite (`PAYMENT_SUPPLIER`, `PAYMENT_DEPOSITED`, `PAYMENT_RECONCILED`, `FISCAL_YEAR_CLOSED`) au lieu d'un refus générique ; nouvel endpoint `GET /api/payments/{id}/cancel-preview` décrivant l'éligibilité et l'impact sur le bordereau.
  - **Interface** : action « Annuler ce règlement » dans le menu de ligne de l'écran Paiements (visible pour les seuls administrateurs), avec une confirmation qui annonce le montant supprimé et l'effet exact sur le bordereau de remise.

## [1.9.1] — 2026-06-30

### Corrigé
- **BIZ-222 / TEC-213/214** (Lot SALARY-FIX) — **Fiabilisation des écritures comptables des salaires**. Un salaire pouvait être enregistré avec un **net à 0** (champ « Net à payer » manuel, par défaut 0, découplé du « Net calculé » affiché), ce qui **sautait silencieusement l'écriture de paiement banque** (421000 D / 512100 C) ; corriger le net ensuite ne régénérait rien (`update_salary` ne touchait pas la comptabilité), laissant un trou permanent (cas réel : paie WOLFF mai 2026, banque faussée de 157,50 €).
  - **A (BIZ-222)** — Le champ « Net à payer » se **remplit automatiquement** depuis le net calculé (brut − cotisations − impôt) en saisie, tout en restant éditable ; l'enregistrement est **refusé si le net est ≤ 0**.
  - **B (TEC-213)** — `update_salary` **régénère les écritures comptables** du salaire quand un montant change (brut, cotisations, impôt, net) ; un changement sans incidence comptable (notes) ne régénère rien. Refus (409) si l'exercice concerné est **clôturé**.
  - **C (TEC-214)** — Garde-fou moteur : **avertissement journalisé** lorsqu'un salaire est constaté sans paiement (net ≤ 0), et fonction `find_incomplete_salaries` pour détecter les salaires constatés mais non payés.
  - **C (TEC-214, correctif)** — `find_incomplete_salaries` renvoyait une **liste vide** sur la base réelle : les paiements de salaires **importés** ont un `source_id` à `NULL`, et un `NULL` dans la sous-requête `NOT IN` rendait toute la comparaison indéterminée (piège SQL classique). La sous-requête exclut désormais les `NULL`. Détecté en passant le détecteur sur la base de production (un seul salaire incomplet confirmé : le cas WOLFF mai déjà corrigé).
- **TEC-215** — **Tableau de bord : tuiles « Recettes/Dépenses du mois » corrigées**. Elles affichaient le **dernier mois de l'exercice** (souvent encore vide car dans le futur) au lieu du **mois calendaire en cours**, d'où des montants à 0 € alors que le graphique montrait bien une activité. La tuile cible désormais le mois courant (repli sur le dernier mois de l'exercice si celui consulté ne contient pas le mois en cours).

## [1.9.0] — 2026-06-29

### Corrigé
- **TEC-212** (Lot TABLE-FIT) — **Scroll horizontal des tableaux supprimé sur grand écran**. Le conteneur de contenu (`.main-inner`) plafonnait toutes les pages à 1320 px, ce qui **neutralisait le mode « large » (1640 px)** des écrans denses (Banque, comptabilité…) : la table débordait son panneau (scroll horizontal) tout en laissant de l'espace inutilisé sur les côtés. `.main-inner` suit désormais la largeur « large », les tableaux s'étirent à leur conteneur (`width: 100%`) et les colonnes texte de la Banque (libellé/référence) ne sont plus compressées. Vérifié sur 16 écrans à tableau : aucun débordement.

### Ajouté
- **BIZ-216** (Lot BK3) — **Sauvegarde des PDFs non régénérables uniquement**. Nouveau réglage (Système › Sauvegardes, **off par défaut**) : quand il est activé, le miroir distant ne conserve que les PDFs **non régénérables** — factures **archivées** (valeur légale) et pièces importées (`data/uploads`) ; les PDFs des factures non archivées sont exclus (ils sont reconstruits à la demande, cf. TEC-211), réduisant l'espace occupé. Filtre appliqué dans le miroir incrémental (OneDrive : sélection fichier par fichier ; rclone : `--files-from`). Risque documenté : un PDF régénéré peut diverger visuellement si le modèle a changé (sans valeur légale).

### Technique
- **TEC-211** (Lot BK3) — **Garde-fou de régénération PDF** verrouillé par un test : la consultation `GET /{id}/pdf` reconstruit le PDF d'une facture lorsque le fichier référencé est absent (déjà le comportement pour les factures non archivées et le repli des archivées) — c'est l'invariant sur lequel repose l'exclusion des PDFs régénérables du backup (BIZ-216).
- **BIZ-169** (Lot EDIT-OPS) — **Garde-fou comptable sur l'édition des opérations bancaires rapprochées**. L'édition/suppression des opérations bancaires manuelles existait déjà (UI + endpoints `PUT`/`DELETE`, refus sur opération importée ou rapprochée pour la suppression). Ce lot ferme une incohérence côté API : le `PUT` autorisait encore l'édition des champs comptablement sensibles (date, montant, compte, catégorie) d'une opération **rapprochée**, ce qui laissait le journal obsolète. Désormais refusé tant que l'opération n'est pas dérapprochée (cohérent avec le `DELETE`) ; les champs cosmétiques (libellé, référence) restent éditables. Couverture de tests ajoutée pour tous les garde-fous (manuelle/importée/rapprochée).
- **BIZ-218** (Lot RELANCES) — Socle de l'**historique des relances** : colonne `reminder_dates` (JSON, défaut `[]`) sur les factures + migration Alembic, exposition dans l'API de lecture des factures, et fonction service d'ajout d'une date de relance. Câblage à l'envoi (type `reminder`) et UI à suivre dans les tickets suivants du lot.
- **BIZ-219** (Lot RELANCES) — **Modèles d'e-mail de relance** distincts de l'envoi initial : deux jeux sujet + corps (1ʳᵉ relance / relance suivante) configurables dans Paramètres › Communication, avec moteur de composition `compose_reminder()` (sélection 1ʳᵉ/suivante selon le nombre de relances, variables `{montant_du}`, `{echeance}`, `{derniere_relance}`, `{nombre_de_relances}` + variables facture, messages FR par défaut). 4 champs `app_settings` + migration. Câblage au flux d'envoi (« Relancer ») à suivre.
- **BIZ-220** (Lot RELANCES) — **Flux de relance branché** : les endpoints d'aperçu/envoi acceptent un type d'envoi (`initial` / `reminder`) ; le bouton « Relancer » d'une facture en retard ouvre l'aperçu éditable prérempli avec le bon modèle de relance, et un envoi `reminder` réussi enregistre la date dans l'historique (l'envoi initial et les échecs n'y touchent pas). Nouvelle colonne **« Dernière relance »** dans la liste, visible uniquement en vue « En retard » (date de la dernière relance, `—` si jamais relancée, nombre de relances en infobulle).
- **BIZ-221** (Lot RELANCES) — **Les factures irrécouvrables sortent de « En retard »** : `isOverdueInvoice()` exclut désormais le statut `irrecoverable`, ce qui les retire à la fois de la liste **et** des métriques « Restant en retard » (créances déjà passées en perte). Dans la vue « En retard », un bouton bascule **exclusif** permet d'afficher soit les factures en retard, soit **toutes** les irrécouvrables. Aucune action « Relancer » sur une facture irrécouvrable.
- **Restructuration du backlog** — passage du backlog monolithique `doc/backlog.md` (+ archive) à une structure **par lot** sous `.backlog/` : un dossier `PRD.md` + `tickets/NN-slug.md` par lot actif, archives compactes par lot, index `.backlog/README.md`. Câblage (sans fork) des skills d'ingénierie `/to-prd` · `/to-issues` · `/triage` via `docs/agents/*`. Vocabulaire de statut unique (⬜ 🔄 🧑 ✅ 🚫). Décision actée dans `docs/adr/0001-backlog-restructure.md`
- **Renommage `doc/` → `docs/`** — alignement sur la convention usuelle. Chemins runtime mis à jour (manuel/changelog servis par le chatbot), `Dockerfile`, `README.md` et docs de process. `CHANGELOG.md` conservé tel quel (ledger historique)

## [1.8.1] — 2026-06-23

### Ajouté
- **TEC-210 / BIZ-217** (Lot ML) — **Envoi d'un email aux adhérents (clients) actifs**. Depuis l'écran Contacts, un assistant en 3 étapes : (1) choix de la période (« actif » = facture client OU paiement sur les N derniers mois, défaut 6) ; (2) liste des adhérents concernés, tous présélectionnés et désélectionnables ; (3) rédaction (objet + message, placeholders `{prenom}`/`{nom}`) et envoi. Côté serveur : un email individuel par destinataire sur **une seule connexion SMTP** (adresses secondaires en `Cc`), récapitulatif envoyés/échecs, journalisé. Accès Secrétaire+.

### Technique
- **TEC-209** (Lot BK2) — Miroir incrémental des PDFs/pièces jointes : `data/pdfs` (et `data/uploads` si activé) ne sont plus rebundlés dans chaque snapshot horodaté mais synchronisés vers un **dossier distant stable** en mode « envoyer si absent » (OneDrive via Graph : diff par nom + taille ; rclone : `copy` incrémental natif). Fin de la duplication des PDFs à chaque backup. La restauration (base seule) est inchangée ; les PDFs vivent dans le dossier miroir pour la reprise
- **TEC-208** (Lot BK2) — Rétention distante des backups : après chaque synchronisation réussie, les **snapshots horodatés** au-delà des **5 plus récents** sont purgés sur chaque destination (OneDrive via Graph, autres via rclone). Plafonne l'espace occupé sur OneDrive (croissance jusque-là illimitée). Purge best-effort (n'échoue jamais le backup) ; ne touche qu'aux dossiers `YYYY-MM-DDTHH-MM-SS`, jamais aux futurs dossiers miroirs

### Corrigé
- **BIZ-215** — Tableau de bord, file « À traiter » : le compteur **« À rapprocher »** était faux (212 affichés alors que seules 2 transactions sont réellement à rapprocher). Il comptait toutes les transactions bancaires non rapprochées **tous exercices confondus**, gonflé par l'historique importé ; il est désormais **scopé à l'exercice courant**, comme l'écran Banque

## [1.8.0] — 2026-06-21

### Corrigé
- **BIZ-211** (Lot RF) — Clé i18n manquante `payments.edit` sur l'action « Modifier » des paiements (le bouton affichait `common.edit` brut). Ajout de la clé générique `common.edit`, et correction de trois clés i18n absentes décelées lors d'une vérification complète : `common.error.title` (toast d'erreur de l'envoi d'e-mail de facture), `accounting.rules.empty` et `accounting.fiscalYear.empty` (messages de liste vide en vue mobile)
- **TEC-205** (Lot RR) — Dialog d'encaissement : le total de la facture s'affichait en chaîne brute (`1234.50 €`) au lieu du format monétaire fr-FR. Nouveau `formatCurrency` mutualisé (`utils/format.ts`) utilisé dans le dialog et en remplacement des `Intl.NumberFormat` recopiés (`DashboardView`, `SalaryView`, `BankPendingDepositsPanel`, `InvoiceFunnelHero`)
- **BIZ-214** (Lot RR) — Factures en retard : l'entrée de menu « Envoyer email » faisait doublon avec l'action principale « Relancer » (même fonction) ; elle est désormais omise dans ce cas
- **TEC-203** (Lot RR) — Barre d'onglets basse mobile masquée lorsqu'une seule destination est accessible (utilisateur lecture seule) au lieu d'un onglet unique pleine largeur

### Technique
- **TEC-204 / TEC-206 / TEC-207** (Lot RR) — Suite de revue de la PR de release : accessibilité des filtres (`AppFilterSegments` en `role="group"` + `aria-pressed`) et de la bascule factures (`InvoiceTypeToggle` en liens `aria-current`) ; hauteurs de chrome en CSS vars (`--app-topbar-height`/`--app-bottom-nav-height`) ; correction d'un chevauchement de breakpoint dans `main.css` (768 → 767 px) ; couverture de tests étendue (item « À rapprocher » du dashboard, montant de l'entonnoir factures)
- **TEC-198** (Lot RF) — API tableau de bord : nouveau champ `to_reconcile_count` (`GET /api/dashboard/`) comptant les transactions bancaires non rapprochées, surfacé en ligne **« À rapprocher »** dans la file « À traiter » (lien profond vers la Banque avec présélection du filtre non-rapprochées via `?reconcile=1`). Le delta de trésorerie reste dérivé côté front ; le compteur d'adhérents n'a pas été ajouté faute d'entité « membre » dans le modèle de données. Tests d'intégration sur le nouveau champ
- **TEC-200** (Lot RF) — Finitions responsive des écrans refondus : sur cartes mobiles, l'action principale passe **pleine largeur** avec le `⋯` à droite (conforme à la maquette) et les cibles tactiles montent à ≥ 40 px ; les grilles KPI restent à 2 colonnes en mobile. Table→cartes (`AppMobileCardList`), scroll horizontal des segments de filtre et tokens du mode sombre étaient déjà en place. **Écart assumé** : pas de FAB d'action primaire sur mobile — il entrerait en conflit avec la barre d'onglets basse et le FAB chat déjà ancrés au pouce ; l'action reste dans l'en-tête de page
- **TEC-199** (Lot RF) — Shell de navigation adaptatif à 3 breakpoints : **sidebar pleine** (≥ 1200 px, contenu centré max 1320 px), **rail d'icônes 72 px** en tablette (768–1199 px, libellés au survol, cibles 44 px), **barre d'onglets basse** en mobile (< 768 px, 4 destinations principales) + **drawer** (burger) pour le reste. `useBreakpoints` expose désormais `isMobile`/`isTablet`/`isDesktop` ; nouvelle source unique de navigation `useNavigation` (sections + items de la barre basse) partagée par la sidebar, le rail et la barre basse. FAB chat relevé au-dessus de la barre basse. Tests Vitest des bascules de breakpoint et de la barre basse
- **TEC-193** (Lot RF) — Badge de statut de facture mutualisé : nouveau composant `InvoiceStatusBadge` + helper `invoiceStatusSeverity` ; suppression de la fonction `statusSeverity` dupliquée à l'identique dans `ClientInvoicesView`, `SupplierInvoicesView` et `ContactHistoryContent`
- **TEC-194** (Lot RF) — Dialog d'encaissement de paiement mutualisé : nouveau composant `InvoicePaymentDialog` ; suppression du formulaire de paiement, de la suggestion de numéro de chèque et de la logique de soumission dupliqués entre `ClientInvoicesView` et `SupplierInvoicesView`
- **TEC-194 / BIZ-206** (Lot RF) — Héro « entonnoir » de facturation mutualisé : nouveau composant `InvoiceFunnelHero` (reste à encaisser/payer + barre empilée Encaissé / À venir / En retard) ; remplace les grilles de KPI hétérogènes des factures client et fournisseur
- **TEC-194 / BIZ-206** (Lot RF) — Actions de ligne factures : remplacement de la rangée de boutons-icônes (jusqu'à 9) par une **action principale contextuelle selon le statut** (Encaisser / Relancer / Voir / Modifier / Traiter) + un **menu de débordement `⋯`** regroupant le reste, avec les actions destructives (abandon de créance, suppression) isolées. Composant `AppRowActions` (mutualisé, cf. TEC-201), appliqué aux vues client et fournisseur (table + cartes mobiles)
- **TEC-194 / BIZ-206** (Lot RF) — Filtres factures : remplacement du menu déroulant de statut par des **segments rapides** avec compteurs (Toutes / En retard / Impayées / Brouillons / Payées). Composant `AppFilterSegments` (mutualisé, cf. TEC-201) ; le filtrage fin par colonne reste disponible dans les en-têtes du tableau
- **TEC-194 / BIZ-206** (Lot RF) — Factures : **bascule de type** Clients/Fournisseurs (`InvoiceTypeToggle`) en tête de page pour signaler l'espace partagé, et **pied de tableau** affichant le nombre de factures et le total affiché
- **TEC-194 / BIZ-206** (Lot RF) — Patron mutualisé `InvoiceWorkspace` : composant unique regroupant l'en-tête, la bascule de type, l'entonnoir, la toolbar (segments + recherche + actions) et le panneau ; les vues factures client et fournisseur en deviennent de fines enveloppes (table et dialogs passés en slots)
- **TEC-197** (Lot RF) — Composant `AppWorklist` mutualisé : file d'actions (icône + libellé + montant coloré par sévérité + chevron, lignes cliquables) réutilisée par le tableau de bord et, à venir, l'écran Système
- **TEC-201** (Lot RF) — Généralisation des composants de liste : `InvoiceRowActions`/`InvoiceFilterSegments` promus en composants génériques `AppRowActions` (type `RowAction`) et `AppFilterSegments` (type `FilterSegment`) sous `components/ui/`, avec classes renommées (`app-row-actions*`, `app-filter-segments*`). Prépare le rollout aux autres écrans listes (BIZ-211). Aucun changement fonctionnel

### Modifié
- **TEC-196** (Lot RF) — Thème : rayons plus sobres (panneaux 22→16 px, cartes 16→12 px) pour un registre comptable plus sérieux, et palette du mode sombre alignée sur le handoff (panneaux navy slate `#13203a`/`#0e1a30`, bordure `#2a3a55`, fond app `#020617`, ombre renforcée)
- **BIZ-207** (Lot RF) — Refonte du tableau de bord : hiérarchisé par action requise — en-tête avec sous-titre (exercice + date de mise à jour), **héro Trésorerie nette** (montant + delta vs mois dernier + sparkline + détail banque/épargne/caisse), file **« À traiter »**, actions rapides, chiffres de référence non cliquables, et un **graphe unique** Produits & charges. Suppression du second graphique et du sélecteur d'exercice local (l'exercice vit dans le sélecteur de la barre du haut)
- **BIZ-208** (Lot RF) — Refonte de l'écran Utilisateurs : matrice de rôles vivante (compteur de comptes par rôle + pastille de couleur), **filtres rapides par rôle** (Tous / Admins / Trésoriers / Inactifs) au-dessus du tableau, et badge **« vous »** sur sa propre ligne. La réinitialisation de mot de passe reste désactivée sur son propre compte
- **BIZ-209** (Lot RF) — Refonte de l'écran Système : **bandeau d'état** en tête (Opérationnel + version / taille BDD / démarré le), **file d'anomalies** (`AppWorklist`) mettant en avant les données à corriger, et **restauration sécurisée** par saisie obligatoire de « RESTAURER » avant confirmation
- **BIZ-212** (Lot RF) — Supervision système réorganisée en **2 onglets** : « État & surveillance » (état, anomalies, journaux, audit) et « Sauvegardes & restauration » (sauvegarde automatique, liste, restauration). Contenu aligné sur la maquette : anomalies en **bandeau ambre** avec bouton « Corriger » (ouvre la correction des chèques), **terminal de journaux** affiché directement avec filtres INFO/WARN/ERROR en chips, et **restauration en panneau rouge inline** (saisie de « RESTAURER ») au lieu d'un dialogue
- **TEC-202** (Lot RF) — Nouveau composant `AppSettingRow` (motif « ligne de réglage » : libellé + description + contrôle), socle de la refonte des écrans de configuration
- **BIZ-213** (Lot RF) — Refonte de l'écran Paramètres : passage de 5 panneaux empilés à **4 onglets** (Organisation · Comptabilité · Communication · Zone dangereuse), champs présentés en lignes de réglage (`AppSettingRow`), **barre d'enregistrement par onglet** (état modifié/à jour, Annuler/Enregistrer), et aperçu en direct du numéro de facture. Soldes d'ouverture, assistant IA et zone dangereuse intégrés dans leurs onglets respectifs
- **BIZ-211** (Lot RF) — Généralisation des actions de ligne aux écrans listes : Contacts, Paiements, Banque, Caisse (journal), Salaires, Employés, Écritures comptables, **Plan comptable** et **Règles comptables** utilisent désormais `AppRowActions` (action principale contextuelle + menu `⋯` regroupant le reste, actions destructives isolées en rouge). Sur Banque, jusqu'à 6 actions conditionnelles par transaction sont regroupées (l'édition de catégorie reste un bouton dédié car elle ancre une popover). Sur Employés, le bascule « Afficher les inactifs » devient des **segments Actifs / Inactifs / Tous** avec compteurs (`AppFilterSegments`). Sur Règles comptables, l'activation/désactivation et la suppression (réservées aux gestionnaires) passent dans le menu `⋯` ; sans droit de gestion, l'unique bascule reste l'action principale. `AppRowActions` masque automatiquement le `⋯` quand il n'y a aucune action secondaire

## [1.7.5] — 2026-05-30

### Corrigé
- **BIZ-201** — Backup automatique : le répertoire `data/pdfs` (factures et documents PDF) est désormais inclus systématiquement dans chaque sauvegarde envoyée vers les destinations distantes
- **BIZ-202** — Factures client : il est désormais possible de saisir un prix unitaire négatif sur une ligne (remise, trop-perçu). La soumission reste bloquée si le total de la facture est négatif

## [1.7.3] — 2026-05-14

### Corrigé
- Contacts : le bouton « Fusionner » est désormais masqué pour les utilisateurs non-administrateurs (seuls les admins peuvent fusionner des contacts)
- **BIZ-203** — Dialogue de fusion contacts : affichage du nom complet (NOM Prénom) via une computed property — évite les espaces parasites liés aux données
- **BIZ-204** — Contacts : le nom (`nom`) est désormais normalisé en majuscules et dépouillé des espaces à la création et à la modification
- **BIZ-205** — Aperçu PDF sur iOS Safari : remplacement de l'`<embed>` non supporté par un bouton « Ouvrir le PDF » (nouvel onglet) sur mobile
- **BIZ-205** — Historique contact : aperçu PDF ajouté pour les factures client (colonne droite, même layout que les factures fournisseur)

## [1.7.2] — 2026-05-12

### Sécurité
- **TEC-160** — Prévention des doublons de numéros d'écriture comptable (index unique + retry)
- **TEC-165** — Limitation de la longueur maximale des mots de passe à 128 caractères (protection DoS bcrypt)
- **TEC-169** — Ajout de `max_length` sur les champs texte des schémas bancaires (référence, description, notes)
- **TEC-172** — Protection CSRF renforcée sur le endpoint `/api/auth/refresh` (header `X-Requested-With` obligatoire)

### Amélioré
- **TEC-164** — `next_entry_number` rendue publique pour réutilisation externe
- **TEC-167** — Allocation par lot des numéros d'écriture (`next_entry_numbers`) — réduction des requêtes DB
- **TEC-168** — Cache de l'environnement Jinja2 pour la génération PDF (`@lru_cache`)
- **TEC-162** — Remplacement des `.catch(() => {})` silencieux par `console.error` dans le frontend

### Refactorisé
- **TEC-170** — Standardisation des codes d'erreur API : format structuré `{"code": "...", "detail": "..."}`, helpers centralisés (`backend/errors.py`), composable frontend `useApiError`, clés i18n FR/EN
- **TEC-171** — Suppression de tous les `db.commit()` dans les services et routeurs ; utilisation de `flush()` uniquement (commit/rollback gérés par `get_db()`)
- **TEC-173** — Découpage de `bank.py` (781 lignes) en 3 sous-routeurs : `bank_transactions.py`, `bank_import.py`, `bank_deposits.py`

### Corrigé
- **TEC-185** — Régression aperçu PDF Chrome : standardisation des aperçus intégrés sur `<embed>` (abandon de `<object>`) avec paramètres viewer pour masquer le volet pages quand le moteur PDF du navigateur le permet
- **TEC-185** — Aperçus PDF intégrés : demande explicite de masquage du volet latéral « Pages » par défaut quand le moteur PDF du navigateur le permet
- **BIZ-189** — Sauvegarde automatique : le spinner de progression n'était pas visible lorsqu'un backup planifié se déclenchait pendant que la page de paramètres était déjà ouverte ; ajout d'une veille (10 s) qui détecte le démarrage et active le polling rapide (3 s)
- **BIZ-198** — Limite d'affichage : alignement UX/documentation pour expliciter que la désactivation de la limite côté session charge jusqu'au plafond API (5 000 éléments)

### Ajouté
- **BIZ-173→184 / BIZ-187 / BIZ-188 / BIZ-189 / BIZ-200** — **Feature majeure : Sauvegarde automatique** (planification intervalle/cron/quotidien HH:MM, destinations local/SMB/OneDrive, restauration/test de restauration, notifications d'échec, OneDrive device code + transfert Microsoft Graph, suivi d'exécution en temps réel)
- **BIZ-196** — **Feature majeure : Import des factures historiques Word** (`scripts/import_word_invoices.py`) avec mode dry-run/commit, rattachement PDF existant, reprise correcte du montant déjà réglé et rapport final détaillé (erreurs + cas ignorés utiles)
- **BIZ-198** — Limite d'affichage configurable par liste : paramètre global `Limite d'affichage par défaut` (défaut 500, modifiable dans Paramètres > Association), bannière d'avertissement quand des éléments sont masqués, bouton « Désactiver la limite » par session ; applicable aux 6 vues liste (factures client, fournisseur, paiements, contacts, salaires, banque) ; en-tête `X-Total-Count` sur tous les endpoints de liste
- **BIZ-173→184** — Lot BK : Sauvegarde automatique — planification (intervalle ou cron), destinations de sauvegarde (local, SMB, OneDrive via rclone), test de connexion, restauration, test de restauration (intégrité SQLite + vérification des tables), e-mail de notification en cas d'échec
- **BIZ-173→184** — Backend : migration Alembic (colonnes `backup_*` dans `app_settings`, table `backup_destination`), modèle `BackupDestination`, schémas Pydantic, services `backup_destination_service`, `backup_restore_service`, `backup_scheduler` (APScheduler), router 12 endpoints `/api/backup/…`
- **BIZ-173→184** — Docker : rclone installé dans l'image, `rclone.conf` généré dynamiquement depuis les destinations activées
- **BIZ-173→184** — Frontend : API `backup.ts`, panneau `SettingsBackupPanel.vue` (planification, statut, destinations, restauration, OAuth OneDrive), clés i18n FR/EN
- **BIZ-186** — Filigrane « PAYÉ » en rouge diagonal sur les PDF des factures intégralement réglées
- **BIZ-187** — Sauvegarde automatique : nouveau type de planification **Quotidien (heure fixe)** — saisir l'heure au format HH:MM pour déclencher la sauvegarde chaque jour à l'heure choisie
- **BIZ-187** — Migration Alembic : colonnes `backup_daily_time` (String 5, défaut `"02:00"`) et `backup_include_all_backups` (Boolean, défaut `False`) dans `app_settings`
- **BIZ-188** — Sauvegarde automatique : par défaut, seul le fichier snapshot `.db` le plus récent est envoyé vers la destination ; option **« Inclure tous les fichiers de sauvegarde précédents »** (désactivée par défaut) pour envoyer l'intégralité du dossier `backups/`
- **BIZ-195** — Nouveau statut `archivée` pour les factures client payées (terminal, irréversible) ; badge gris « Archivée » dans les listes
- **BIZ-196** — Script `scripts/import_word_invoices.py` : import en masse de factures historiques au format Word (`.docx`) dans Solde (mode dry-run par défaut, `--commit` pour valider), conversion/rattachement automatique du PDF existant, reprise correcte du montant déjà réglé sur les archives et rapport final détaillant les erreurs et cas ignorés utiles
- **BIZ-197** — Endpoint `POST /api/invoices/bulk-archive` : archivage en masse des factures payées sélectionnées
- **BIZ-190** — Frontend : type `archived` dans `InvoiceStatus`, badge gris, bouton télécharger le document sur les factures archivées ; masquage des boutons email / dupliquer / créance irrécouvrable pour les archivées
- **BIZ-191** — Vue factures client : bouton « Archiver la sélection » dans la toolbar, visible dès qu'au moins une facture payée est affichée, avec confirmation et toast de résultat
- **BIZ-193** — Bouton « Exporter Excel » sur toutes les vues DataTable : factures fournisseur, paiements, contacts, employés, salaires, caisse (entrées), banque (transactions), exercices, plan comptable, règles, journal, grand livre, balance, bilan, compte de résultat — exporte les lignes filtrées visibles au format `.xlsx`
- **BIZ-199** — Contacts : fusion de doublons (dialog de fusion côté frontend + endpoint backend dédié + tests d'intégration)
- **BIZ-200** — Sauvegarde OneDrive : authentification appareil (device code) et transfert direct via Microsoft Graph API, plus robuste en environnement Docker/headless

### Technique
- **TEC-192** — Composable `useTableExport` (SheetJS) : `exportToExcel(rows, columns, filename)` avec 4 tests Vitest

---

## [1.6.0] — 2026-05-05

### Ajouté
- **BIZ-170** — Gestion des bordereaux en attente : bouton « Actions » remplace « Confirmer le dépôt » ; dialogue modal permettant de modifier la sélection (retirer des chèques ou billets), puis de choisir entre : annuler les changements, valider les changements, annuler le dépôt ou confirmer le dépôt
- **BIZ-170** — Backend : endpoint `PATCH /api/bank/deposits/{id}` (mise à jour d'un bordereau non confirmé) et `DELETE /api/bank/deposits/{id}` (annulation avec libération des paiements)
- **BIZ-170** — Panneau « Dépôts en attente » factorisé en composant partagé `BankPendingDepositsPanel` (BankView + Dashboard)
- **BIZ-171** — Tuiles factures client : suppression de la ligne étiquette (catégorie) pour alléger les cartes mobiles
- **BIZ-171** — Tuiles factures fournisseur : référence et trombone fusionnés sur une seule ligne conditionnelle
- **BIZ-171** — Dialog prévisualisation facture fournisseur : date, échéance et référence sur lignes séparées ; boutons icône uniquement sur mobile ; intro empilée en colonne ; libellés TOTAL/RÉGLÉ/RESTANT DÛ réduits pour éviter le débordement
- **BIZ-172** — Vue Supervision (admin) : panneau « Paiements chèques incohérents » listant les chèques marqués comme remis mais sans date de remise, avec sélecteur de date et bouton « Corriger » par ligne
- **BIZ-172** — Backend : filtre `inconsistent_only` sur `GET /api/payments/` et endpoint dédié `POST /api/payments/{id}/fix-deposit-date` pour corriger les données importées sans altérer les validateurs d'immutabilité

### Corrigé
- **BIZ-170** — Dépôts espèces : suppression du champ « total » éditable dans les dialogues de création et d'édition ; le total est désormais toujours calculé depuis les coupures saisies
- **BIZ-170** — Confirmations demandées avant « Annuler le dépôt » (danger) et « Confirmer le dépôt » (succès)

---

## [1.5.1] — 2026-05-04

### Ajouté
- **BIZ-034** — Support multi-compte bancaire (compte courant + compte épargne) : chaque transaction peut désormais être associée à l'un des deux comptes
- **BIZ-034** — Import OFX multi-comptes : un seul fichier OFX peut contenir les deux comptes, identifiés par leur ACCTID ; le compte est attribué automatiquement selon les identifiants configurés dans les réglages
- **BIZ-034** — Réglages association : champs « Identifiant ACCTID OFX » pour le compte courant et le compte épargne
- **BIZ-034** — Vue Banque : filtre par compte (Tous / Courant / Épargne), solde du compte épargne affiché en stat card
- **BIZ-034** — Dashboard : stat card « Solde épargne » en complément du solde courant
- **TEC-160** — Migration Alembic `0050` : colonne `bank_account` sur `bank_transactions` (valeur par défaut : `courant`)
- **TEC-161** — Migration Alembic `0051` : colonnes `bank_account_courant_acctid` et `bank_account_epargne_acctid` dans `app_settings`
- **BIZ-164** — Mode téléphone : vue carte mobile sur toutes les listes de l'application (Factures client/fournisseur, Contacts, Banque, Règlements, Caisse, Salaires, Employés, Comptabilité, Exercices, Règles comptables, Journal, Balance, Bilan, Résultat, Utilisateurs) — les DataTables laissent place à des cartes empilées sous 767 px
- **BIZ-164** — Composable `useBreakpoints` (breakpoint 767 px via `window.matchMedia`, avec listener réactif)
- **BIZ-164** — Composant générique `AppMobileCardList` avec slot `#card="{ item }"` et typage générique `T` pour inférence TypeScript correcte dans les slots
- **BIZ-164** — Suggestion automatique du numéro de chèque (`AAAAMMJJ.NN`) à l'ouverture du formulaire de paiement chèque (factures client et fournisseur, assistant saisie rapide) ; modèle de numérotation configurable dans les paramètres
- **BIZ-164** — Endpoint `GET /api/payments/suggest_cheque_number` (sans effet de bord) et service `suggest_cheque_number` côté backend
- **BIZ-164** — Paramètre `cheque_number_template` dans les réglages (champ `{date}.{seq}` par défaut, validé côté backend)
- **BIZ-164** — Migration Alembic `0049` : colonne `cheque_number_template` dans `app_settings`
- **BIZ-165** — Boutons de navigation Précédent / Suivant dans le dialog d'historique des factures client (parité avec la vue factures fournisseur)
- **BIZ-166** — Vue Contacts : onglet « Clients » actif par défaut (ordre : Clients > Fournisseurs > Tout) ; contacts triés par récence de dernière facture (< 6 mois en tête) puis ordre alphabétique
- **CHR-078** — Fichier `frontend/src/i18n/en.ts` créé : squelette de localisation anglaise avec `app`, `auth` et `common` traduits ; enregistré dans `vue-i18n` avec `fallbackLocale: 'fr'`

### Amélioré
- **BIZ-164** — Dialogs pleine largeur sur mobile (`app-dialog`, `app-dialog--medium`, `app-dialog--large`, `app-dialog--xlarge`) : 100 vw et hauteur max 95 dvh en dessous de 767 px
- **BIZ-164** — Styles utilitaires mobiles ajoutés dans `main.css` : `app-mobile-card-row`, `app-mobile-card-label`, `app-mobile-card-value`, `app-mobile-card-actions`
- **BIZ-164** — Tuile dépôt en attente : liste de coupures espèces ou comptage chèques en colonne de droite alignée ; layout desktop (1 ligne, coupures à droite alignées, bouton en bout de ligne) et layout mobile (empilé) séparés
- **BIZ-164** — Grille de stat cards : 2 colonnes sur mobile
- **TEC-157** — `AppMobileCardList` : message vide par défaut remplacé par la clé i18n `common.empty` (suppression de la chaîne en dur `'Aucune donnée'`)
- **TEC-157** — `CashView` : libellé `'Écart :'` des comptages remplacé par la clé i18n `cash.count_diff`

### Corrigé
- **BIZ-034** — Virements internes (512100 ↔ 512102) : seul le côté COURANT génère désormais des écritures comptables ; le côté EPARGNE retourne une liste vide, ce qui évitait que 512102 soit débité et crédité du même montant (solde nul) lors de chaque virement
- **BIZ-034** — Journal filtré sur un compte : les colonnes Débit/Crédit d'une écriture groupée affichent désormais uniquement la contribution du compte filtré (et non le total équilibré de l'écriture complète) — ex. l'ouverture FY2024 affichait 61 791,51 au lieu de 52 115,89 sur 512102
- **BIZ-034** — Saisie manuelle d'écriture : le `fiscal_year_id` est désormais automatiquement dérivé de la date saisie quand le frontend ne le fournit pas, évitant que l'écriture soit invisible lors d'un filtre par exercice
- **BIZ-164** — Mock `window.matchMedia` ajouté dans le setup de tests Vitest pour éviter des erreurs jsdom dans les composants utilisant `useBreakpoints`
- **BIZ-164** — Clé stable dans `AppMobileCardList` : prop `itemKey` optionnelle pour éviter les réutilisations erronées de nœuds DOM lors d'un tri/filtrage
- **BIZ-164** — Tuile dépôt espèces : `total_amount` affiché même si `denomination_details` est vide ou invalide (fallback `v-else-if`)
- **BIZ-164** — Suppression du double appel API de suggestion de numéro de chèque à l'ouverture du dialog (guard `paymentDialogVisible` dans le `watch`)
- **BIZ-164** — Annotation de type `payment_date: date | None` dans `GET /api/payments/suggest_cheque_number` (était `date` alors que le paramètre est optionnel)
- **BIZ-167** — Bouton « Passer en créance douteuse » masqué pour les contacts de type Fournisseur (n'a de sens que pour les clients)
- **BIZ-168** — Barre de navigation Précédent / Suivant dupliquée en bas des dialogs preview factures client et fournisseur ; le défilement est conservé en bas du dialog lors de la navigation depuis la barre du bas (pour faciliter la consultation du PDF attaché)
- **CR-077** — CSS dupliqué supprimé dans `SupplierInvoicesView` (bloc `.preview-nav-bar--bottom` en double)
- **CR-077** — Fuite mémoire Blob URL corrigée dans `ClientInvoicesView` : l'ancienne URL est révoquée avant d'en créer une nouvelle à l'ouverture de l'historique
- **CR-077** — Bouton « Passer en créance douteuse » désormais masqué pour les contacts de type `les_deux` (visible uniquement pour `type === 'client'`)
- **CR-077** — Commentaire d'en-tête de `frontend/src/i18n/en.ts` corrigé : précise que les sections absentes tombent en fallback French via `fallbackLocale: 'fr'`
- **BIZ-034** — Catégorie bancaire « Sans écriture » (`no_entry`) : une transaction avec cette catégorie ne génère aucune écriture comptable lors du rapprochement, même si des règles actives existent — il est architecturalement impossible de créer une règle pour cette catégorie

### Tests
- **BIZ-034** — 2 nouveaux tests unitaires de régression pour le virement interne : `test_internal_transfer_courant_side_generates_entries` (côté COURANT → entrées générées) et `test_internal_transfer_epargne_side_returns_empty` (côté EPARGNE → liste vide)
- **BIZ-034** — 2 nouveaux tests unitaires de régression pour `get_grouped_journal` : totaux filtrés par compte (`test_filter_by_account_keeps_full_group` enrichi) et simulation d'une ouverture multi-comptes (`test_filter_by_account_totals_multi_line_group`)
- **TEC-158** — 5 nouveaux tests d'intégration pour `GET /api/payments/suggest_cheque_number` : statut 200 + format, date par défaut (aujourd'hui), incrément séquentiel, 401 sans auth, 403 pour `readonly`
- **TEC-159** — 4 nouveaux tests d'intégration pour `cheque_number_template` dans settings API : valeur par défaut renvoyée, mise à jour valide, rejet sans `{seq}`, rejet avec placeholder non supporté
- **CR-077** — Tests de régression renforcés sur `suggest_cheque_number` : vérification du format exact `YYYYMMDD.NN` et de la date d'aujourd'hui utilisée en fallback
- **CR-077** — 2 nouveaux tests Vitest pour la navigation Précédent / Suivant du dialog historique (`ClientInvoicesView`)
- **CR-077** — 2 nouveaux tests Vitest pour la navigation Précédent / Suivant du dialog preview facture fournisseur, barre du bas (`SupplierInvoicesView`)
- **BIZ-034** — 4 nouveaux tests unitaires `TestGenerateEntriesForBankTransaction` : catégorie `no_entry` → liste vide, objet non-`BankTransaction` → liste vide, `uncategorized` → liste vide, `bank_fee` avec règle → 2 écritures équilibrées
- **BIZ-034** — 1 nouveau test d'intégration : `POST /api/accounting/rules/` avec `trigger_type: "no_entry"` retourne 422

---

## [1.4.0] — 2026-05-03

### Ajouté
- **BIZ-161** — Onglet « Nouveautés » dans la page Aide : endpoint `GET /api/help/changelog`, affichage du changelog utilisateur rendu en Markdown
- **BIZ-163** — Guide par rôle « Je veux… » ajouté en fin de `doc/user/manuel.md` (index des activités par rôle avec liens vers les sections)
- **BIZ-158** — Limite API relevée à 1 000 éléments par défaut sur `invoice`, `payment`, `contact`, `bank transactions`, `bank deposits`, `salary` (anciennement 100) ; bandeau d'avertissement PrimeVue `warn` affiché dans chaque vue liste quand le résultat atteint 1 000 items

### Corrigé
- **TEC-156** — Assistant IA : token d'authentification lu depuis le store Pinia (mémoire) au lieu de `localStorage` — corrige le 401 systématique sur `POST /api/chat`

### Amélioré
- **BIZ-162** — Liens d'ancre dans le manuel en ligne : intercepteur de clics dans `HelpView.vue` pour défilement fluide vers les sections cibles
- **BIZ-149** — Auto-capitalisation de la première lettre des intitulés de lignes de facture client au `blur` (déjà implémentée — ticket fermé)
- **BIZ-150** — Champs quantité et prix unitaire dans `ClientInvoiceForm` acceptent désormais la virgule comme séparateur décimal (normalisée en point à la saisie)
- **BIZ-157** — Pagination des DataTables : 50 lignes affichées par défaut (anciennement 20) dans toutes les vues de liste

---

## [1.3.1] — 2026-05-02

### Sécurité

- **TEC-133** — Access token stocké uniquement en mémoire Pinia (suppression de `localStorage`) ; au rechargement, la session est restaurée silencieusement via `POST /api/auth/refresh` (cookie HttpOnly) — atténuation XSS
- **TEC-135** — Race condition sur la numérotation des factures : retry loop sur `IntegrityError` (jusqu'à 3 tentatives) pour garantir l'unicité sans verrou explicite

### Corrigé

- **TEC-134** — `record_audit()` appelé avant `await db.commit()` dans `update_user` — atomicité audit/modification restaurée
- **TEC-136** — Chemins de fichiers factures stockés en relatif en base ; résolution absolue uniquement à la lecture
- **TEC-137** — Payload JWT décodé une seule fois dans le middleware et mis en cache dans `request.state.jwt_payload` ; `get_current_user` le réutilise sans second décodage
- **TEC-138** — Rate limiter : purge périodique des clés expirées toutes les 100 tentatives pour borner l'empreinte mémoire
- **TEC-139** — Tokens OpenAI correctement comptabilisés en mode streaming (`stream_options={"include_usage": True}`)
- **TEC-140** — `GET /api/settings/audit-logs` : pagination (`skip`/`limit`) et filtres (`action`, `actor_id`, `from_date`, `to_date`)
- **TEC-155** — Suppression des 13 `# type: ignore[return-value]` dans `backend/routers/invoice.py` (annotations corrigées)

### Technique

- **TEC-141** — Constante `USER_ROLES` (`frontend/src/constants/roles.ts`) : source unique pour les chaînes de rôles côté frontend

---

## [1.3.0] — 2026-05-02

### Ajouté

- **BIZ-141** — Rapprochement bancaire : les boutons « Rapprocher », « Tout rapprocher » et « Rapprocher avant… » génèrent désormais des écritures comptables automatiques selon la catégorie de la transaction (`BANK_FEE` → Frais bancaires, `SOCIAL_CHARGE`, `GRANT`, `INTERNAL_TRANSFER`) ; source `bank_transaction` traçable dans le journal
- **BIZ-144** — Wizard facture rapide : l'étape de confirmation affiche le nom du contact (`{Prénom} NOM`)
- **BIZ-145** — Wizard facture rapide : bouton « Envoyer par e-mail » dans la confirmation ; badge « E-mail envoyé » après envoi
- **BIZ-147** — Contacts : gestion de plusieurs adresses e-mail (jusqu'à 2 supplémentaires, libellé libre) ; table `contact_emails` (migration 0047) ; dialogue d'envoi de facture multi-destinataires (cases à cocher)
- **BIZ-151** — Contacts : marquage « Client indésirable » (`blocked`) avec ToggleSwitch, badge rouge dans la liste, blocage strict de la création de facture (HTTP 422)
- **BIZ-155** — Paiement fournisseur en espèces : crée automatiquement une sortie caisse (`CashMovementType.OUT`)
- **BIZ-156** — Factures fournisseur : bouton « Enregistrer un règlement » dans la liste et dans la prévisualisation
- **BIZ-157** — Comptage de caisse : champ unique « Pièces (ferraille) » pour le total des pièces, migration `0048`
- **BIZ-160** — Bordereaux en attente visibles depuis le tableau de bord (en plus de la vue Banque)
- **BIZ-133** — Relevé bancaire : édition de la catégorie détectée via icône crayon
- **BIZ-135** — Relevé bancaire : boutons « Tout rapprocher » et « Rapprocher avant… » (bulk reconcile)
- **BIZ-139** — Factures fournisseur : dialogue de prévisualisation avec historique paiements, aperçu PDF/image et navigation précédent/suivant ; même prévisualisation inline dans l'historique contact
- Lot I-BNK : l'import bancaire distingue les sources précises (Excel, CSV, OFX, QIF) ; la colonne Référence affiche la référence comptable au lieu du FITID technique

### Corrigé

- **BIZ-158** — Bordereau de dépôt depuis un comptage : total billets uniquement (les pièces ne sont pas déposables)
- **BIZ-159** — Dialog bordereau : préremplissage depuis un comptage corrigé (race condition entre watchers Vue, flag `_isPrefilling`)
- Référence OFX (FITID) : suppression du fallback `description || reference` dans les dialogues de rapprochement et le service journal — le FITID opaque n'est plus jamais affiché
- Salaires : écritures comptables datées au dernier jour du mois (correction `calendar.monthrange`)
- Salaires : erreur `MissingGreenlet` à la création/modification — accès lazy remplacé par requêtes async explicites
- Factures fournisseur : statut initial `sent` (au lieu de `draft`) pour les factures créées manuellement
- Import OFX multi-comptes : rejet explicite au lieu d'importer les opérations de tous les comptes en vrac
- Import bancaire : doublons (même FITID) détectés et ignorés silencieusement
- Sauvegarde : libellé jusqu'à 100 caractères ; message de validation affiché dans l'UI
- **TEC-146** — Aperçu PDF : `<object type="application/pdf">` pour Chrome/Firefox
- **TEC-152** — Docker : fuseau horaire `Europe/Paris`
- **TEC-153** — Logs : handler fichier désactivé sous pytest ; SQLAlchemy reclassé en DEBUG
- **TEC-154** — Backup : nettoyage du fichier de destination en cas d'échec ; chemin absolu pour éviter les ambiguïtés

---

## [1.1.0] — 2026-04-28

### Ajouté

- Lot H : Paramètres (`GET /settings/` et `GET /settings/system-opening`) désormais accessibles aux gestionnaires (trésorier, comptable) en lecture — les mises à jour (`PUT`) restent réservées aux administrateurs
- Lot H : Dialogue paiement — affiche désormais le nom du client, la description, le montant total et la date d'échéance de la facture concernée
- Lot H : Nouveaux champs famille sur les contacts clients : prénom/nom de l'enfant, prénom/nom de l'autre parent
- Lot H : Date du jour pré-remplie à la création d'une facture client
- Lot H : Système de commentaires internes (`/comments`) — chaque utilisateur peut saisir des notes/remarques ; les admins voient tous les commentaires
- Lot H : PDF facture — instructions de règlement avec IBAN, BIC et numéro de chèque ajoutées en pied de facture (numéro de facture réel inclus)

### Modifié

- Lot H : Édition d'une facture client bloquée si elle est à l'état `SENT` avec un montant déjà payé, ou à l'état `PAID`
- Lot H : PDF facture — bloc Émetteur supprimé (doublon du en-tête)

### Ajouté

- BIZ-132 : État intermédiaire « en bordereau » (en transit) pour les chèques — un chèque intégré dans un bordereau non confirmé passe à `in_deposit=True, deposited=False` ; `deposited=True` n'est positionné qu'à la **confirmation** du bordereau (migration Alembic 0040)
- BIZ-132 : Bouton « Tout sélectionner / Tout désélectionner » dans le dialogue de création de bordereau (chèques)
- BIZ-132 : Colonne « Remis en banque » dans la vue Paiements — affiche trois états distincts : remis (✓), en bordereau (horloge, orange), à remettre (✗)

### Corrigé

- BIZ-132 : Confirmation d'un bordereau espèces — la `BankTransaction` de crédit (entrée banque) n'était pas créée ; seule la `CashEntry OUT` était générée

### Modifié

- BIZ-132 : Filtre `undeposited_only` sur les paiements — exclut désormais les chèques déjà en bordereau (état « en transit »)
- BIZ-132 : Dashboard — le compteur de paiements non remis exclut les chèques en bordereau non confirmé

### Modifié

- BIZ-131 : Refonte sémantique du modèle de dépôt espèces — les paiements espèces sont désormais marqués `deposited=True` dès leur création (ils entrent immédiatement en caisse) ; un bordereau espèces est préparé à partir d'un montant et d'un détail optionnel de coupures (billets), sans lien vers des paiements individuels
- BIZ-131 : Bordereau espèces — la caisse sort (CashEntry OUT) et les écritures comptables sont générées à la **confirmation** du bordereau, non à sa création
- BIZ-131 : Migration Alembic 0039 — colonne `denomination_details` (TEXT nullable) sur `deposits` ; mise à jour des paiements espèces existants à `deposited=True`
- BIZ-131 : Vue Paiements — suppression de la métrique « Espèces à déposer » (toujours 0 désormais) ; seule la métrique « Chèques à remettre » reste

### Ajouté

- BIZ-130 : Confirmation de dépôt bancaire — champ `confirmed` (booléen) et `confirmed_date` sur les bordereaux de dépôt (migration 0038) ; endpoint `POST /api/bank/deposits/{id}/confirm` ; audit log `bank.deposit.confirm`
- BIZ-130 : Panneau « Dépôts en attente de confirmation » dans la vue Banque — liste les bordereaux préparés mais non encore remis à l'agence, avec résumé (nb chèques ou encaissements, montant) et bouton « Confirmer »
- BIZ-130 : Colonne « Statut » (en attente / confirmé) dans le tableau des dépôts de la vue Banque, avec filtre

---

## [1.0.0] — 2026-04-27

### Ajouté

- BIZ-129 : Notes de crédit (avoirs) — nouveau type de document `avoir` sur les factures ; numérotation séparée `AV-YYYY-NNN` ; endpoint `POST /api/invoices/{id}/credit-note` pré-remplissant les lignes inversées ; contrainte total ≥ 0 levée pour les avoirs ; badge « Avoir » dans les listes et formulaires ; template PDF dédié avec en-tête « NOTE DE CRÉDIT » ; bouton « Créer un avoir » sur les factures envoyées/payées
- BIZ-129 : Migration Alembic 0038 — colonnes `invoice_type` (défaut `facture`) et `credit_note_for_id` (FK nullable vers `invoices.id`) sur la table `invoices`
- BIZ-128 : Modèles d'e-mail configurables dans les paramètres SMTP — le sujet et le corps par défaut des e-mails de factures peuvent être personnalisés via l'interface admin ; variables disponibles : `{invoice_number}`, `{description}`, `{association_name}`, `{invoice_ref}` ; laisser vide conserve le comportement automatique
- BIZ-128 : Migration 0037 — colonnes `email_subject_template` et `email_body_template` (nullable) dans `app_settings`
- BIZ-128 : `_SafeFormatMap` dans `email_service.py` — variables inconnues dans un modèle sont conservées telles quelles (pas de `KeyError`)
- BIZ-128 : 7 nouveaux tests unitaires pour `compose_subject`/`compose_body` avec modèle, variable `{invoice_ref}`, et variable inconnue

### Ajouté

- BIZ-127 : Dialogue de confirmation avant envoi de facture par e-mail — sélection de la facture ouvre un dialog avec le destinataire (lecture seule), le sujet et le corps du message (éditables), et un aperçu PDF de la facture ; l'envoi est déclenché avec le contenu édité par l'utilisateur
- BIZ-127 : Endpoint `GET /api/invoices/{id}/email-preview` — retourne le destinataire, le sujet et le corps pré-composés sans envoyer de mail
- BIZ-127 : `POST /api/invoices/{id}/send-email` accepte désormais un payload JSON `{subject, body}` (contenu édité par l'utilisateur) ; l'audit log inclut le sujet
- BIZ-127 : Helpers `compose_subject()` et `compose_body()` extraits de `email_service.py` ; `send_invoice_email` accepte `override_subject`/`override_body`
- BIZ-127 : 8 nouveaux tests unitaires pour `compose_subject`, `compose_body` et les paramètres `override_subject`/`override_body`

### Ajouté

- BIZ-125 : Chatbot IA — sidebar de chat flottante avec streaming SSE (Google Gemini ou OpenAI), bouton FAB dans AppLayout, annulation du flux, rendu Markdown via `marked`
- BIZ-125 : Page `/aide` — affichage du manuel utilisateur `doc/user/manuel.md` rendu en HTML avec styles prose
- BIZ-125 : Panneau admin « Assistant IA » dans les Paramètres — configuration du fournisseur (gemini/openai), clé API et modèle ; badge d'état activé/non configuré
- BIZ-125 : Backend — endpoint `POST /api/chat` (streaming SSE), `GET /api/chat/config`, `GET /api/chat/logs` (admin), `GET /api/help/manual` ; migration 0035 (colonnes chat dans `app_settings`) et 0036 (table `chat_log`)
- BIZ-126 : Refactoring UX écran Paramètres — `SettingsAssociationSmtpPanel.vue` (413 lignes) remplacé par `SettingsAssociationPanel.vue` (association/facturation) et `SettingsSmtpPanel.vue` (SMTP) ; chaque panneau sauvegarde indépendamment
- Nav : lien « Aide » visible dans la section accueil de la barre de navigation (tous les utilisateurs authentifiés)

### Supprimé

- BIZ-126 : `SettingsAssociationSmtpPanel.vue` — remplacé par les deux composants ci-dessus

### Ajouté

- CHR-079 : `doc/admin/installation.md` — guide d'installation Docker bilingue (FR+EN) avec Docker Compose complet, configuration `.env`, option Synology Portainer
- CHR-079 : `doc/admin/configuration.md` — référence des variables d'environnement et paramètres association, bilingue
- CHR-079 : `doc/admin/excel-import.md` — procédure complète d'import Excel bilingue : types de fichiers, structure attendue, prérequis, ordre recommandé, pas à pas, historique/undo, reset sélectif
- CHR-079 : `doc/admin/administration.md` — guide d'administration bilingue : montée de version, sauvegardes, restauration, gestion des utilisateurs et rôles
- CHR-079 : `doc/dev/architecture.md`, `doc/dev/contributing.md`, `doc/dev/testing.md`, `doc/dev/development-process.md` — documentation développeur complète en anglais
- CHR-079 : `doc/user/manuel.md` — manuel utilisateur FR complet par cas d'usage (connexion, contacts, factures, paiements, caisse, banque, salaires, comptabilité, profil)
- CHR-079 : `doc/llm/reference.md` — référence dense en anglais pour assistants IA (modèle de données complet, API, règles métier, conventions)

### Corrigé

- fix(invoice) : champ `lines` restauré dans `InvoiceRead` — retiré accidentellement lors de BIZ-127, rendait le formulaire d'édition vide (champs et lignes)
- fix(invoice) : bouton « Supprimer » masqué pour les factures non-brouillon — le bouton n'est affiché que pour les factures au statut `draft`
- fix(invoice) : dialog d'envoi d'e-mail élargi (`min(95vw, 1180px)`) et aperçu PDF corrigé (`<embed>` au lieu de `<iframe>`) ; CSP étendue à `object-src blob: ; frame-src blob:`
- fix(settings) : variables de modèle d'e-mail affichées correctement — les accolades dans les clés i18n étaient interprétées comme interpolation vue-i18n v11 (résultat : « , , , »)
- fix(tests) : test `test_swagger_disabled_in_production` corrigé — la route SPA catch-all interceptait `/api/*` quand `frontend/dist` existe ; `chat_log` manquait dans le schéma de test

### Supprimé

- CHR-079 : Suppression des fichiers de documentation obsolètes — `doc/recette.md`, `doc/import-excel-plan.md`, `doc/plan-reprise-post-imp.md`, `doc/architecture.md`, `doc/dev/audit-report-2026-04.md`, `doc/dev/bl-*`, `doc/dev/contribuer.md`, `doc/dev/exploitation.md`, `doc/dev/gestion-utilisateurs-et-permissions.md`, `doc/dev/import-excel-contract.md`, `doc/dev/import-excel-procedure.md`, anciens fichiers `doc/user/`

---

## [Précédent — v0.7.13]

### Ajouté

- BIZ-111 : Script one-shot `scripts/import_addresses_from_docx.py` — extrait les adresses postales depuis les factures Word historiques (`.docx`) et enrichit `Contact.adresse` ; dry-run par défaut, `--commit` pour appliquer, `--verbose` pour le détail extraction par fichier
- TEC-106 : Audit i18n complet — 2 clés manquantes identifiées et ajoutées dans `fr.ts` : `common.active` ('Actif') et `common.inactive` ('Inactif'), utilisées dans la vue Employés
- BIZ-122 : Intégration du champ `description` de la facture dans l'objet de l'e-mail d'envoi — si renseigné, le sujet devient `Facture {numéro} — {description}` au lieu de `Facture {numéro} — {association}`
- BIZ-122 : `tests/unit/test_email_service.py` — test `test_send_invoice_email_subject_with_description` ajouté
- BIZ-124 : Numérotation configurable pour les factures clients et fournisseurs — champ `client_invoice_number_template` (`{year}` + `{seq}`, ex. `{year}-{seq}` → `2026-001`) et `supplier_invoice_number_template` (strftime Python, ex. `FF-%Y%m%d%H.%M.%S` → `FF-2026040717.56.01`) modifiables dans les paramètres de l'association
- BIZ-124 : Migrations Alembic 0032 (`client_invoice_seq_digits`) et 0033 (`client_invoice_number_template` + `supplier_invoice_number_template`)
- BIZ-123 : Prix par défaut par type de ligne de facture — colonnes `default_price_cours`, `default_price_adhesion`, `default_price_autres` sur `AppSettings` (migration 0034) ; section « Prix unitaires par défaut » dans les paramètres ; pré-remplissage automatique au `addLine()` et au changement de `line_type` dans `ClientInvoiceForm`
- BIZ-111 (suite) : Adresse postale du contact (`Contact.adresse`) affichée dans la section Destinataire des factures PDF — chaque ligne rendue séparément
- BIZ-111 (suite) : SIRET de l’émetteur supprimé de la carte Émetteur dans les factures PDF (déjà présent dans l’en-tête et le pied de page)
- BIZ-119 : Panneau « Actions rapides » sur le tableau de bord — 3 cartes d'accès direct (nouvelle facture client, encoder un paiement, nouvelle entrée de caisse) ; navigation vers la vue cible avec ouverture automatique du dialog de création via le paramètre `?create=1`
- BIZ-119 : Carte « Saisir une facture client » — ouvre désormais un wizard inline (dialog) avec formulaire de création et bouton « Saisir une autre facture » après succès, sur le modèle du wizard de paiement
- BIZ-112 : Numéro de facture affiché dans le titre du dialog de modification (factures clients et fournisseurs) — header dynamique `Modifier — F-2025-042` au lieu du libellé générique
- BIZ-113 : Statut `IRRECOVERABLE` sur les factures clients — passage en irrécouvrable avec écriture comptable automatique 654/411 (Pertes sur créances irrécouvrables / Adhérents) et bouton de restauration du statut avec écriture de reprise 411/754
- BIZ-113 : Comptes PCG `654000` (Pertes sur créances irrécouvrables) et `754000` (Reprises sur créances amorties) ajoutés aux comptes par défaut
- BIZ-113 : Endpoints `POST /api/invoices/{id}/write-off` et `POST /api/invoices/{id}/restore-from-writeoff` — transitions gérées par service dédié avec validation d'état et génération d'écritures
- BIZ-113 : Migration Alembic documentaire `0031` — marqueur de version, aucun changement de schéma (statuts stockés en VARCHAR)
- BIZ-113 : Bouton « Passer en irrécouvrable » dans la colonne actions des factures clients (dialog de confirmation avec mention des écritures) ; bouton « Annuler le statut irrécouvrable » pour les factures IRRECOVERABLE ; toggle « Afficher/Masquer les irrécouvrables » (masqués par défaut)
- BIZ-115 : Libellé optionnel (champ texte libre) sur les sauvegardes — saisie avant création, inclus dans le nom de fichier et affiché en colonne dans la liste
- BIZ-116 : Restauration d'une sauvegarde depuis la vue système — double confirmation (saisie de « RESTAURER » + récapitulatif) ; polling `/api/health` après déclenchement ; rechargement automatique de la page
- BIZ-116 : Endpoint `POST /api/settings/backups/{filename}/restore` — validation du nom de fichier par regex, audit `admin.backup.restore`, arrêt du processus via `SIGTERM` après `_engine.dispose()`
- TEC-099 : Contrainte `ON DELETE CASCADE` sur la FK `payments.invoice_id → invoices.id` (migration Alembic `0030_payment_invoice_cascade`) — suppression d'une facture en base entraîne désormais la suppression en cascade des paiements associés, éliminant le risque d'enregistrements orphelins
- TEC-100 : `tests/unit/test_pdf_service.py` — 13 tests couvrant `render_invoice_html` (contenu HTML) et `generate_invoice_pdf` / `save_invoice_pdf` (WeasyPrint mocké via `sys.modules` pour éviter l'import natif GTK)
- TEC-100 : `tests/unit/test_email_service.py` — 11 tests couvrant STARTTLS, SSL, BCC optionnel, sujet du message, et gestion des erreurs SMTP/OS/auth
- TEC-101 : Composable `frontend/src/composables/useInvoiceMetrics.ts` — extrait `receivableMetrics` et `portfolioMetrics` de `ClientInvoicesView.vue`, avec export des helpers purs `remainingForInvoice`, `isOpenReceivableInvoice`, `isOverdueInvoice`
- TEC-102 : Utilitaire `frontend/src/utils/errorUtils.ts` — fonction `getErrorDetail(error, fallback)` qui extrait le message `detail` des erreurs FastAPI structurées
- TEC-103 : Debounce 300 ms sur le filtre global de `ClientInvoicesView.vue` via `globalFilterInput` ref + `setTimeout`/`clearTimeout` natif — évite les re-renders à chaque frappe sur de longues listes
- BIZ-108 : Écran de supervision système (`/system`) — panneau état (version, taille DB, uptime, badge statut), panneau sauvegardes (création + liste), journaux applicatifs (filtres niveau + texte, couleur par niveau, défilement)
- BIZ-109 : Journal d'audit — endpoint `GET /api/settings/audit-logs` et panneau dédié dans l'écran système (tableau horodatage / acteur / action / cible / détail)
- BIZ-108 : Schémas Pydantic `SystemInfoRead`, `BackupFileRead`, `LogEntryRead`, `AuditLogRead` dans `backend/schemas/settings.py`
- BIZ-108 : Endpoints admin `GET /api/settings/system-info`, `GET /api/settings/backups`, `GET /api/settings/logs` avec parsing des fichiers de rotation
- BIZ-108 : Fonctions API TypeScript `getSystemInfoApi`, `listBackupsApi`, `getLogsApi`, `getAuditLogsApi` dans `frontend/src/api/settings.ts`
- BIZ-107 : Colonne « Dernière facture » dans le tableau des contacts (référence + date) — enrichissement backend avec sous-requête SQLAlchemy MAX(date) par contact
- BIZ-107 : Historique contact en Dialog centré (au lieu d'une navigation vers une page dédiée) — composant `ContactHistoryContent` partagé entre la vue pleine page et le dialog
- BIZ-107 : `ContactHistoryContent.vue` — composant extrait de `ContactDetailView`, réutilisable via prop `contactId` et événement `contact-loaded`
- BIZ-107 : `ContactHistoryDialog.vue` — enveloppe `ContactHistoryContent` dans un `<Dialog>` PrimeVue avec le nom du contact en titre

### Modifié

- BIZ-121 : Couverture d'audit étendue à toutes les mutations métier — `AuditAction` enrichi de 40 nouvelles valeurs (paiements, factures, caisse, salaires, transactions bancaires, rapprochements, imports CSV/OFX/QIF, remises, contacts, import Excel) ; `record_audit()` appelé après chaque opération réussie dans 7 routers (`payment`, `invoice`, `cash`, `salary`, `contact`, `bank`, `excel_import`) ; libellés i18n français ajoutés dans `fr.ts`
- BIZ-120 : Tri par date décroissante par défaut sur toutes les listes — journal, grand livre, banque, caisse, salaires, paiements, factures clients et fournisseurs
- TEC-098 : `backend/services/accounting_entry_service.py` — suppression de `limit=100_000` ; `get_balance`, `get_resultat`, `get_bilan` utilisent désormais des agrégations SQL (`GROUP BY + SUM`) ; `get_grouped_journal` utilise une pagination SQL réelle (`OFFSET/LIMIT` poussés dans la requête SQLAlchemy, plus de slice Python)
- TEC-098 : `backend/services/export_service.py` — `export_journal_csv` passe `limit=None` pour lever le plafond de 100 000 lignes sans charger en mémoire
- TEC-102 : `BankClientPaymentDialog.vue`, `BankSupplierPaymentDialog.vue`, `BankLinkClientPaymentDialog.vue`, `BankLinkSupplierPaymentDialog.vue` — extraction d'erreur inline remplacée par `getErrorDetail()`
- TEC-104 : `CashView.vue` — type `CashDenomField` dédié élimine le cast `as unknown as Record<string, number>` dans le template ; `CashEntryFormState.date` déclaré `Date | string` élimine les deux casts `as unknown as Date`
- Navigation : page « Employés » déplacée de la section Comptabilité vers la section Gestion
- Navigation : ajout de l'entrée « Supervision système » dans la section Administration (admins uniquement)
- BIZ-107 : `ContactDetailView.vue` — réécrit comme wrapper léger autour de `ContactHistoryContent`
- BIZ-107 : `ContactsView.vue` — bouton historique ouvre le dialog au lieu de naviguer, nouvelle colonne « Dernière facture »
- `PUT /api/accounting/rules/{id}` : accès resserré de trésorier+admin à **admin uniquement**, cohérent avec `POST /` et `DELETE /{id}` (REC-008)

### Corrigé

- BIZ-108 : Ordre de lecture des fichiers de rotation inversé — `.log.1` (plus récent) était lu après `.log.2` (plus ancien), masquant les entrées récentes
- BIZ-108 : Filtre de niveau des journaux passé côté serveur — le filtre s'applique maintenant avant la limite de 500 lignes, rechargement automatique à chaque changement de filtre
- BIZ-109 : Labels des actions d'audit traduits en français dans l'écran de supervision (clés i18n imbriquées `system.action.*`)
- BIZ-109 : Horodatages affichés en heure locale — SQLite stockant les dates sans suffixe de fuseau, elles étaient interprétées comme heure locale plutôt qu'UTC (décalage −2h)
- TEC-110 (REC-016) : Fix SPA — `index.html` servi avec `Cache-Control: no-store, no-cache, must-revalidate` ; assets hachés `/assets/*` avec `immutable, max-age=1 an`. Élimine l'erreur `TypeError: error loading dynamically imported module` après un rebuild Docker (navigateur chargeait un `index.html` mis en cache référençant des hashes de chunks obsolètes)
- BIZ-118 : Saisie de dates pénible dans tous les formulaires (`DatePicker` PrimeVue reformate à chaque frappe) — nouveau composant `AppDatePicker.vue` basé sur `<input type="date">` natif ; segment jour/mois/année éditable indépendamment, aucun reformatage pendant la frappe ; date émise à midi pour éviter les décalages DST
- BIZ-106 : Journal comptable et caisse limités à 100 lignes — valeur par défaut du paramètre `limit` passée de 100 à 5000 (max 10 000) dans les endpoints `/api/accounting/journal`, `/api/accounting/journal-grouped`, `/api/cash/entries` et `/api/cash/counts`
- BIZ-114 : Suppression des entrées caisse manuelles impossible — endpoint `DELETE /api/cash/entries/{id}` avec cascade sur les écritures comptables liées (`source_type='cash'`) ; endpoint `GET /api/cash/entries/{id}/connections` pour aperçu avant suppression ; bouton de suppression avec confirmation dans `CashView.vue`
- REC-019 : `ClientInvoiceForm.vue`, `SupplierInvoiceForm.vue` — ajout de `:show-on-focus="false"` sur les `DatePicker` (date et échéance) pour empêcher le calendrier de s'ouvrir automatiquement à l'ouverture du dialog
- `doc/dev/exploitation.md` : section déploiement Portainer / NAS Synology — stack YAML, variables d'environnement, données persistantes, procédure de mise à jour (CHR-019, REC-004)
- Écran Salaires rendu accessible au rôle `secretaire` (Management) en plus des rôles `tresorier` et `admin` (REC-005)
- CRUD complet des règles comptables réservé aux admins : création, modification, suppression avec confirmation ; dialog formulaire avec sélecteur de déclencheur, lignes comptables éditables ; 26 libellés et descriptions métier en français par déclencheur (REC-008)
- Docker : rechargement direct sur une route Vue retournait 404 — FastAPI sert désormais `index.html` en fallback pour toutes les routes hors `/api/**` (REC-003)
- Docker : `libgdk-pixbuf2.0-0` absent de Debian Trixie remplacé par `libgdk-pixbuf-xlib-2.0-0` — génération PDF WeasyPrint rétablie (REC-002)
- Docker : `pyproject.toml` absent du stage `frontend-builder`, causant un échec de build de l'image (REC-007)
- `.gitattributes` ajouté pour forcer LF sur `entrypoint.sh` et éviter les erreurs de syntaxe shell après checkout Windows (REC-003)

### Technique

- Version de l'application lue depuis `pyproject.toml` via `importlib.metadata` (backend) et regex Vite (frontend) — `APP_VERSION` supprimé de `.env` (REC-001, REC-006)

### UX & Formulaires

- BIZ-094 : Confirmation avant « Recréer le socle comptable » — dialog warn avec annulation (SettingsDangerZonePanel)
- BIZ-095 : Avertissement modifications non sauvegardées sur tous les formulaires — garde `@update:visible` + `onBeforeRouteLeave` (ClientInvoicesView, SupplierInvoicesView, ContactsView, EmployeesView, SalaryView)
- BIZ-096 : Feedback de validation champ par champ — parsing erreurs Pydantic 422 dans ClientInvoiceForm, SupplierInvoiceForm, ContactForm
- BIZ-097 : Accessibilité : `aria-label` sur tous les boutons icône, focus automatique sur le premier champ à l'ouverture des dialogs

### Performances

- TEC-105 : Fix N+1 dans `payment.list_payments()` — Invoice jointe dans la requête principale (1 query au lieu de N+1)
- TEC-105 : Dashboard — filtres `unpaid` et `overdue` déplacés en SQL (`WHERE total_amount > paid_amount`, `WHERE due_date < today`) au lieu d'un chargement en mémoire de toutes les factures
- TEC-105 : Index SQL ajouté sur `invoices.due_date` (migration 0028) — accélère les requêtes de factures en retard

### Sécurité

- TEC-091 : Logging serveur ajouté sur les routeurs `invoice`, `excel_import`, `settings` — les exceptions inattendues sont désormais tracées (`logger.exception`) avant relance
- TEC-092 : Validation du contenu réel des fichiers uploadés par magic bytes (PDF, JPEG, PNG, WebP) dans `upload_invoice_file` — le header `Content-Type` client ne suffit plus
- TEC-093 : Contraintes Pydantic sur les schémas `contact`, `invoice`, `salary`, `payment` — `max_length` sur tous les champs texte libres, `ge=0` sur les montants salaires, validation plage `hours` (0–744)
- `backend/models/contact.py` : enum `ContractType` (CDI/CDD) + 5 nouveaux champs sur `Contact` : `contract_type`, `base_gross`, `base_hours`, `hourly_rate`, `is_contractor` (BIZ-089)
- `backend/models/salary.py` : 3 champs CDD nullable : `brut_declared`, `conges_payes`, `precarite` (BIZ-089)
- `backend/models/invoice.py` : champ `hours` nullable (pour factures AE) (BIZ-089)
- `backend/alembic/versions/0025_add_employee_contract_fields.py` : migration des champs contrat sur la table `contacts` (BIZ-089)
- `backend/alembic/versions/0026_add_salary_cdd_fields.py` : migration des champs CDD sur la table `salaries` (BIZ-089)
- `backend/alembic/versions/0027_add_invoice_hours.py` : migration du champ `hours` sur la table `invoices` (BIZ-089)
- `backend/schemas/salary.py` : `SalaryPreviousRead` (données pré-CEA d'un salaire précédent) et `WorkforceCostRow` (vue coûts du personnel) (BIZ-089)
- `backend/services/salary_service.py` : `get_previous_salary` (dernier salaire d'un employé) et `get_workforce_cost` (consolide CDI + CDD + AE) (BIZ-089)
- `backend/routers/salary.py` : `GET /salaries/previous/{employee_id}` et `GET /salaries/workforce-cost` (BIZ-089)
- `frontend/src/api/contacts.ts` : champs contrat sur `Contact`, `ContactCreate`, `ContactUpdate` (BIZ-089)
- `frontend/src/api/accounting.ts` : champs CDD sur `SalaryRead`/`SalaryCreate` ; nouveaux types `SalaryPreviousRead` et `WorkforceCostRow` ; `getPreviousSalaryApi` et `getWorkforceCostApi` (BIZ-089)
- `frontend/src/views/EmployeesView.vue` : section « Contrat » dans le dialog — type CDI/CDD (conditionne les champs brut de base / taux horaire), flag auto-entrepreneur (BIZ-089)
- `frontend/src/views/SalaryView.vue` : formulaire restructuré en 3 étapes (calcul du brut, saisie CEA, notes) ; calcul automatique CDD (brut déclaré → CP → précarité → brut total) ; bouton « Reprendre le salaire précédent » ; panneau « Coûts du personnel » (CDI + CDD + AE) (BIZ-089)
- `backend/services/excel_import_types.py` : `NormalizedSalaryRow` étendu avec `brut_declared`, `conges_payes`, `precarite` (optionnels) (BIZ-090)
- `backend/services/excel_import_parsers.py` : `parse_salary_sheet` lit désormais les colonnes CDD (cols 2/3/4) du format détaillé de la feuille « Aide Salaires » — les lignes CDD obtiennent leurs 3 champs, les lignes CDI conservent `None` (BIZ-090)
- `backend/services/excel_import/_import_payments_salaries.py` : `_import_salaries_sheet` passe `brut_declared`, `conges_payes`, `precarite` au constructeur `Salary` lors de l'import (BIZ-090)
- `backend/models/invoice.py` : relation ORM `contact` ajoutée sur `Invoice` (nécessaire pour `selectinload` dans `get_workforce_cost`) (BIZ-089)
- `backend/routers/salary.py` : route `GET /salaries/workforce-cost` déplacée avant `GET /salaries/{salary_id}` — Starlette essayait de convertir "workforce-cost" en `int` → 422 (BIZ-089)
- `frontend/src/views/SalaryView.vue` : panneau « Coûts du personnel » refondu en tableau pivoté 5 colonnes (mois, CDI, CDD, Auto-E, total du mois) — agrégation `total_cost` par type par mois (BIZ-089)
- `frontend/src/components/ContactForm.vue` : toggle « Auto-entrepreneur / prestataire » (`is_contractor`) ajouté dans le formulaire contact — permet de marquer un fournisseur comme auto-E pour l'inclure dans la vue coûts du personnel (BIZ-089)
- `frontend/src/i18n/fr.ts` : clé `common.refresh` ajoutée ; `workforce_col_total` ajouté ; libellé `workforce_type_ae` abrégé en "Auto-E" (BIZ-089)
- `backend/models/contact.py` : valeur `EMPLOYE = "employe"` ajoutée à `ContactType` — les employés sont désormais des contacts d'un sous-type dédié (BIZ-088)
- `backend/alembic/versions/0024_add_employe_contact_type.py` : migration documentant la nouvelle valeur enum (colonne `VARCHAR(20)`, pas de DDL) (BIZ-088)
- `frontend/src/views/EmployeesView.vue` : nouvel écran de gestion des employés — liste (filtrable par nom/prénom/e-mail/téléphone, toggle actifs/inactifs), création, édition, activation/désactivation (BIZ-088)
- Route `/employees` ajoutée au router Vue, accessible aux rôles `tresorier` et `admin` (BIZ-088)
- Menu de navigation : entrée « Employés » dans la section Comptabilité, avant « Salaires » (BIZ-088)
- `frontend/src/views/SalaryView.vue` : `loadEmployees` filtre désormais sur `type=employe` — seuls les contacts de type employé apparaissent dans la liste de sélection (BIZ-088)

### Corrigé

- `backend/services/excel_import/_import_payments_salaries.py` et `import_reversible.py` : les contacts employés créés lors de l'import Excel utilisent désormais `ContactType.EMPLOYE` au lieu de `FOURNISSEUR` (BIZ-088)
- `doc/user/installation.md` : option A — image pré-construite depuis GHCR (`SOLDE_IMAGE=ghcr.io/davidp57/solde:latest`) et option B — build local ; sections FR + EN (CHR-019)
- `doc/dev/exploitation.md` : nouvelle section « Image deployment options » présentant GHCR vs build local + variable `SOLDE_IMAGE` ; `SWAGGER_ENABLED` ajouté au tableau de configuration (CHR-019, CHR-082)
- `backend/config.py` : paramètre `SWAGGER_ENABLED` — active Swagger UI (`/api/docs`) et ReDoc (`/api/redoc`) indépendamment de `DEBUG` (CHR-082)
- `.env.example` : entrée `SWAGGER_ENABLED=false` documentée (CHR-082)
- `backend/main.py` : `openapi_tags` avec descriptions pour les 12 groupes d'endpoints ; `/api/docs`, `/api/redoc` et `/api/openapi.json` activés si `debug` ou `swagger_enabled` est vrai (CHR-082)
- `.github/workflows/ci.yml` : workflow CI GitHub Actions (jobs `backend` + `frontend`) — ruff check + format, mypy, pytest sur toutes les branches actives ; ESLint, vue-tsc, vitest sur le frontend (CHR-086)
- `.github/workflows/docker.yml` : workflow Docker — build multi-stage + push image `ghcr.io/davidp57/solde` sur push `main` avec tags `latest` + `sha-<short>` et cache GitHub Actions (CHR-087)
- `docker-compose.yml` : commentaire indiquant comment substituer le `build:` par `image: ghcr.io/davidp57/solde:latest` pour déploiement NAS sans rebuild local (CHR-087)
- `frontend/src/views/ContactsView.vue` : onglets Tous / Clients / Fournisseurs via `Tabs` PrimeVue — filtrage frontend (`les_deux` visible dans les deux onglets), remplacement du `Select` type par les onglets (BIZ-035)
- `POST /api/contacts/import-emails` : endpoint d'import d'e-mails en masse pour enrichir les contacts existants par correspondance sur le nom (normalisation des accents, matching prénom+nom et nom seul) — schémas `ContactEmailImportRow` / `ContactEmailImportResult`, 9 nouveaux tests (BIZ-040)
- `frontend/src/views/ContactsView.vue` : bouton « Importer e-mails » + dialogue avec zone de texte collée (`Nom, email` par ligne) + affichage du bilan (mis à jour / non trouvés / déjà renseignés) (BIZ-040)
- `frontend/src/layouts/AppLayout.vue` : nom d'utilisateur (sidebar et topbar) cliquable via `RouterLink` vers `/profile` — suppression de l'entrée « Mon profil » du menu de navigation (BIZ-037)
- `frontend/src/layouts/AppLayout.vue` : numéro de version discret en bas de la sidebar, injecté depuis `package.json` via `vite.config.ts` `define.__APP_VERSION__` (CHR-038)
- `frontend/src/tests/composables/useDarkMode.spec.ts` : tests unitaires Vitest pour le composable `useDarkMode` — toggle, persistance dans localStorage, classe CSS `dark-mode` (TEC-079)
- `frontend/src/tests/composables/useTableFilter.spec.ts` : tests unitaires Vitest pour `applyFilter` et `useTableFilter` — filtrage par sous-chaîne insensible à la casse, réactivité, cas limites null/undefined (TEC-079)
- `frontend/src/tests/composables/activeFilterLabels.spec.ts` : tests unitaires Vitest pour `findSelectedFilterLabel` et `collectActiveFilterLabels` — matching, valeurs nulles, types numériques (TEC-079)
- `frontend/e2e/smoke.spec.ts` : smoke test E2E Playwright couvrant login → changement de mot de passe obligatoire → dashboard → contacts → factures clients → paiements (TEC-080)
- `frontend/playwright.config.ts` : configuration Playwright avec webServer auto-start (backend Uvicorn + frontend Vite) et DB E2E dédiée (TEC-080)
- `tests/integration/test_accounting_rules_api.py` : tests d'intégration complets pour l'API des règles comptables — CRUD, seed, auth, rôles (TEC-081)
- `tests/integration/test_fiscal_year_api.py` : tests d'intégration pour les endpoints pre-close-checks, open-next, close 404, auth/rôles (TEC-081)
- `tests/integration/test_salary_api.py` : tests complémentaires — get by id, update, delete not found, accès trésorier (TEC-081)
- `tests/integration/test_dashboard_api.py` : test d'authentification pour le graphique ressources (TEC-081)
- `frontend/src/components/ui/AppTableSkeleton.vue` : composant de skeleton réutilisable (grille de cellules PrimeVue `Skeleton`, props `rows`/`cols` avec valeurs par défaut 8×4) remplaçant les `ProgressSpinner` dans toutes les vues de liste au premier chargement (BIZ-071)
- `frontend/src/components/ui/AppAccountSelect.vue` : composant combo comptes comptables avec point coloré pour les 5 comptes de suivi (créances membres, fournisseurs, caisse, courant, chèques à déposer) via `AppAccountSelect` wrappant PrimeVue `Select` avec slots `#option` et `#value` (BIZ-043)
- `frontend/src/assets/main.css` : classes globales `.app-table-skeleton`, `.app-table-skeleton__row`, `.account-select-option`, `.account-select-dot` et variantes couleur par compte de suivi

### Modifié

- `frontend/src/views/DashboardView.vue` : remplacement du `ProgressSpinner` central par 7 `<Skeleton height="132px">` dans la grille KPI au chargement — cohérence visuelle avec le layout final (BIZ-071)
- `frontend/src/views/AccountingBilanView.vue` : remplacement du `ProgressSpinner` par `AppTableSkeleton :rows="10" :cols="3"` (BIZ-071)
- `frontend/src/views/ContactDetailView.vue` : remplacement du `ProgressSpinner` par une grille de 3 `Skeleton` de stat + `AppTableSkeleton` (BIZ-071)
- `frontend/src/views/ClientInvoicesView.vue` : skeleton sur la liste principale (`loading && !invoices.length`) et dans le dialogue historique (BIZ-071)
- `frontend/src/views/ContactsView.vue` + `PaymentsView.vue` : skeleton sur liste principale au premier chargement (`loading && !*.length`) (BIZ-071)
- `frontend/src/views/AccountingJournalView.vue` : skeleton liste + filtre compte remplacé par `AppAccountSelect` avec rechargement automatique à la sélection (BIZ-071, BIZ-043)
- `frontend/src/views/AccountingLedgerView.vue` : select compte remplacé par `AppAccountSelect` avec points colorés (BIZ-043)
- `frontend/src/composables/useKeyboardShortcuts.ts` : composable Vue 3 gérant les raccourcis clavier Ctrl/Cmd+N (nouveau), Ctrl/Cmd+S (sauvegarder) et Escape (fermer) avec gestion du focus (Ctrl+N ignoré dans les champs de saisie) et nettoyage automatique au démontage (BIZ-073)
- `frontend/src/components/ui/AppStatCard.vue` : prop optionnelle `to` (route Vue Router) rendant la carte KPI cliquable via `<RouterLink>` avec animation hover et focus-visible accessible (BIZ-075)
- `frontend/src/views/DashboardView.vue` : tous les KPI (solde banque, caisse, factures impayées/en retard, chèques non déposés, exercice courant, résultat) sont désormais cliquables vers les vues filtrées correspondantes (BIZ-075)
- `frontend/src/views/ClientInvoicesView.vue` + `PaymentsView.vue` : support des query params URL (`status=overdue`, `undeposited=1`) pour pré-filtrer les listes depuis le dashboard (BIZ-075)
- `frontend/src/views/ClientInvoicesView.vue` + `ContactsView.vue` : intégration de `useKeyboardShortcuts` pour Ctrl+N / Ctrl+S / Escape dans les vues avec dialogue (BIZ-073)
- `doc/user/migration.md` + `doc/user/migration.en.md` : guide de migration / montée de version bilingue FR + EN pour les déploiements Docker sur Synology NAS — couvre la préparation, la mise à jour, la vérification, le rollback et les bonnes pratiques (CHR-083)
- `frontend/src/assets/print.css` : styles `@media print` pour l'impression des vues comptables (journal, balance, grand livre, bilan, résultat) — masque la sidebar, les filtres et les boutons ; optimise les tables en noir et blanc A4 paysage pour impression AG (BIZ-076)
- `backend/main.py` : middleware ASGI `UnhandledExceptionMiddleware` interceptant toutes les exceptions non gérées pour renvoyer un JSON structuré `{"detail": ..., "code": "INTERNAL_SERVER_ERROR"}` au lieu d'un 500 HTML avec stack trace — log complet côté serveur (TEC-067)
- `backend/main.py` : `/api/docs`, `/api/redoc` et `/api/openapi.json` désormais désactivés quand `debug=False` — réduit la surface d'attaque en production (TEC-068)
- `backend/services/backup_service.py` + `POST /api/settings/backup` : endpoint admin de sauvegarde SQLite utilisant `sqlite3.backup()` avec rotation automatique (5 derniers backups), téléchargement direct du fichier en réponse (BIZ-069)
- `backend/schemas/auth.py` : politique de complexité de mot de passe — minimum 8 caractères, au moins une majuscule et un chiffre, appliquée sur la création utilisateur, le changement et le reset de mot de passe (TEC-085)

**Qualité / Sécurité (audit 2026-04-22)**

- `backend/routers/auth.py` : le refresh token est désormais transmis via un cookie `HttpOnly`, `Secure`, `SameSite=Strict` au lieu du corps JSON — `/auth/login` et `/auth/refresh` posent le cookie, nouvel endpoint `POST /auth/logout` (204) l'efface (TEC-046)
- Frontend : `refreshApi()` et `logoutApi()` utilisent le cookie automatiquement (`withCredentials: true`), le store auth ne stocke plus le refresh token en `localStorage` (TEC-046)
- `entrypoint.sh` : script d'entrée Docker dédié avec `set -e` — les migrations Alembic échouent explicitement au lieu d'être masquées par le `&&` shell (CHR-054)
- `GET /api/health` : endpoint de health check léger (200, `{"status": "ok"}`) + `HEALTHCHECK` Docker + `healthcheck:` docker-compose pour la supervision Synology (CHR-061)
- `backend/models/user.py` : champ `must_change_password` obligeant l'utilisateur à changer son mot de passe avant d'accéder à l'application — activé au bootstrap admin, à la réinitialisation de mot de passe par un administrateur, et désactivé automatiquement après changement effectif (BIZ-053)
- `backend/main.py` : middleware `MustChangePasswordMiddleware` bloquant (HTTP 403) toute requête API hors `/api/auth/` quand le JWT porte le flag `mcp=True` (BIZ-053)
- Frontend : redirection automatique vers la page Profil avec bannière d'avertissement lorsque `must_change_password` est actif ; le router guard empêche la navigation vers d'autres pages (BIZ-053)
- `backend/config.py` : `get_settings()` utilise désormais `@lru_cache` au lieu d'un pattern `global` mutable — plus idiomatique et thread-safe (TEC-066)
- `backend/main.py` : middleware `SecurityHeadersMiddleware` ajoutant `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security` et `Referrer-Policy` sur toutes les réponses (TEC-047)
- `backend/config.py` : paramètre `cors_allowed_origins` (liste, variable d'environnement `CORS_ALLOWED_ORIGINS`) permettant de configurer explicitement les origines CORS autorisées en production — wildcard `*` seulement en mode debug sans origines configurées (TEC-055)
- `frontend/public/dark-mode-init.js` : script d'initialisation du mode sombre extrait inline vers un fichier statique dédié pour respecter la politique `script-src 'self'` de la CSP (TEC-047)
- Endpoints de liste : paramètre `limit` désormais borné (`default=100`, `le=1000`) sur tous les routers de liste — caisse, banque, paiements, factures, contacts, salaires, écritures — pour limiter le volume de données retourné en une seule requête (TEC-059)
- `backend/models/types.py` : nouveau `TypeDecorator` `DecimalType` (wrapping `Numeric`) garantissant que SQLAlchemy renvoie toujours un `Decimal` pour les colonnes monétaires au lieu d'un `float` SQLite — élimine les quelque 60 casts `Decimal(str(obj.attr))` répartis dans les services (TEC-057)
- `backend/models/payment.py` : suppression de `__allow_unmapped__` et des attributs transients `invoice_number` / `invoice_type` — ces champs sont désormais calculés à la lecture dans `PaymentRead` via une requête ciblée sur `Invoice` (TEC-065)
- `backend/models/audit_log.py` : table `audit_logs` + service `record_audit` + enum `AuditAction` pour le journal d'audit structuré — traçabilité des connexions (succès/échec), déconnexions, changements de mot de passe, création/modification d'utilisateurs, réinitialisations de mot de passe admin, et opérations de reset base. Migration Alembic `0023` (BIZ-056)
- Tests : +44 tests unitaires (812 → 856) pour les services critiques — `fiscal_year_service` (pre_close_checks, report à nouveau), `contact` (historique, créance douteuse), `dashboard_service` (KPIs, alertes, graphiques), `salary_service` (update, filtre par mois), `accounting_rule_service` (CRUD, preview, template). Couverture globale backend ~71 % (TEC-049)

### Refactorisé

- `frontend/src/views/SettingsView.vue` → 24 lignes (depuis 1 077 L) : extraction de `SettingsAssociationSmtpPanel`, `SettingsSystemOpeningPanel`, `SettingsDangerZonePanel` dans `src/components/settings/` (TEC-077)
- `frontend/src/views/BankView.vue` → 917 lignes (depuis 2 215 L) : extraction de 7 composants de dialogue dans `src/components/bank/` — `BankNewTransactionDialog`, `BankImportStatementDialog`, `BankClientPaymentDialog`, `BankLinkClientPaymentDialog`, `BankSupplierPaymentDialog`, `BankLinkSupplierPaymentDialog`, `BankNewDepositDialog` — chaque dialogue est auto-suffisant (chargement interne, émet `@saved`) (TEC-077)
- `frontend/src/views/ImportExcelView.vue` → 1 191 lignes (depuis 2 873 L) : extraction de `ImportExcelFormPanel`, `ImportExcelShortcutsPanel`, `ImportExcelPreviewPanel`, `ImportExcelResultPanel` dans `src/components/import/` — la vue orchestre, les composants gèrent l'affichage et les opérations locales (TEC-077)

**Qualité / Sécurité (audit 2026-04-22)**

- `backend/services/excel_import.py` : monolith de 5 567 lignes éclaté en package `backend/services/excel_import/` avec 16 sous-modules thématiques (`_constants`, `_salary`, `_invoices`, `_loaders`, `_comparison`, `_comparison_loaders`, `_comparison_domains`, `_entry_groups`, `_sheet_wrappers`, `_orchestrator`, `_import_contacts_invoices`, `_import_payments_salaries`, `_import_cash_bank`, `_import_entries`, `_preview_existing`, `_preview_sheets`) — refactoring purement structurel, interfaces publiques inchangées, zéro dépendance circulaire (TEC-050)
- `backend/services/excel_import/_exceptions.py` : introduction de `ImportFileOpenError` et `ImportSheetError` en remplacement des `except Exception` généralisés — `_ImportSheetFailure(RuntimeError)` remplacé par alias vers `ImportSheetError`, orchestrateur avec catch séparés par type, routeur avec mapping HTTP typé (TEC-058)

### Corrigé

**Import — chèques inter-exercices (BIZ-033)**

- `backend/services/excel_import/excel_import_parsers.py` : parsing de la colonne « Encaissé » corrigé — `deposited_idx` ne se résolvait plus sur « Date encaissement » quand « encaisse » est sous-chaîne de ce libellé
- `backend/services/excel_import/_loaders.py` : nouvelle fonction `_load_existing_payments_deposit_map` pour retrouver le statut de remise des paiements existants
- `backend/services/import_reversible.py` : nouvelle opération `update_payment_deposit_status` — lors de l'import d'un fichier ultérieur, un paiement existant avec `deposited=False` est mis à jour vers `deposited=True` au lieu d'être silencieusement ignoré comme doublon exact

**Dashboard — corrections KPI et paiements non remis**

- `backend/services/dashboard_service.py` : KPI « chèques non remis » filtre désormais uniquement les paiements `CLIENT` en `chèque` ou `espèces`, excluant correctement les remises fournisseurs
- `frontend/src/views/ClientInvoicesView.vue` : filtre « en retard » calculé côté client ; limite portée à 1 000 ; `skipDateFilter` actif quand le paramètre URL `status=overdue` est présent
- `frontend/src/views/DashboardView.vue` : carte « Factures impayées » dirige désormais vers la liste avec `?unpaid=1`
- `frontend/src/views/PaymentsView.vue` : la liste des paiements non remis ignore le filtre de période exercice (un chèque inter-exercices peut s'étaler sur deux années)

**Import — bouton import séquentiel de test**

- `frontend/src/components/import/ImportExcelShortcutsPanel.vue` + `ImportExcelView.vue` : bouton « Tout importer dans l'ordre » dans le panneau de raccourcis de test — enchaîne `gestion-2024 → comptabilite-2024 → gestion-2025 → comptabilite-2025` avec fenêtre de comparaison auto-calculée par fichier, toast par étape et arrêt au premier échec

**Qualité / Sécurité (audit 2026-04-22)**

- `frontend/src/stores/counter.ts` : suppression du fichier de scaffolding Vue non utilisé (CHR-064)
- `frontend/package.json` : version alignée sur `0.1.0` pour correspondre au backend (CHR-062)
- `backend/models/accounting_account.py` : remplacement des noms de personnes réelles dans le plan comptable par défaut par des libellés génériques (`Client litigieux 1`, `Client litigieux 2`) — conformité RGPD (TEC-063)
- `tests/integration/test_import_api.py` : adaptation du test `test_test_import_shortcuts_list_and_run_configured_file` pour utiliser `unittest.mock.patch` au lieu d'accéder directement au singleton `_settings` supprimé (TEC-066)
- `backend/routers/settings.py` : endpoint `POST /settings/reset-db` désormais protégé — retourne HTTP 403 si `settings.debug` est `False`, évitant une remise à zéro accidentelle en production (TEC-052)
- `backend/database.py` : suppression de `Base.metadata.create_all` de `init_db()` — le schéma est exclusivement géré par les migrations Alembic ; `init_db()` ne configure plus que les PRAGMAs SQLite (TEC-060)
- `backend/services/accounting_engine.py` : `_next_entry_number` utilise désormais `SELECT MAX(entry_number)` au lieu de `SELECT COUNT(*)` pour éviter les collisions de numéros après suppressions ou imports partiels (TEC-051)

**Documentation projet**

- `README.md` recentré comme point d'entrée synthétique bilingue `FR + EN` avec renvoi vers les guides détaillés
- Nouvelle documentation technique `doc/dev/exploitation.md` rédigée en anglais pour l'exploitation Docker, la configuration, les volumes, les sauvegardes et les opérations courantes
- Nouvelle documentation développeur `doc/dev/contribuer.md` rédigée en anglais pour la mise en route locale, les commandes qualité, les conventions de développement et le workflow de contribution
- Nouvelle documentation utilisateur / installation disponible en `FR + EN` avec index bilingue `doc/user/README.md`, guide d'installation `doc/user/installation.md` et versions anglaises des guides utilisateur déjà rédigés

**Import Excel réversible**

- Journal d'import réversible persistant avec `import_runs`, `import_operations` et `import_effects`
- Nouveaux endpoints API pour préparer, exécuter, annuler et rejouer un import ou une opération unitaire
- Historique des imports dédié dans l'interface, séparé de l'écran de préparation
- Prévisualisation détaillée des opérations préparées, de leurs effets prévus et des données source Excel associées

**Gestion des utilisateurs**

- Documentation de cadrage `doc/dev/gestion-utilisateurs-et-permissions.md` pour clarifier la cible produit des rôles et la matrice simplifiée des permissions
- Administration des comptes réservée à l'administrateur avec liste, création, activation/désactivation et changement de rôle
- Espace `Mon profil` permettant à chaque utilisateur authentifié de consulter son compte, de mettre à jour son e-mail et de changer son mot de passe
- Procédure de réinitialisation d'accès par l'administrateur avec mot de passe temporaire pour le contexte auto-hébergé

**Administration des reprises d'import**

- Reset sélectif de reprise dans `Paramètres` avec prévisualisation puis suppression confirmée d'un périmètre `Gestion` ou `Comptabilite` borné à un exercice
- Plan de suppression construit à partir des traces d'import (`import_logs` legacy et `import_runs` réversibles) et enrichi, côté `Gestion`, par les dépendances métier dérivées créées ensuite dans Solde
- Documentation utilisateur consolidée pour expliquer la place respective de l'historique réversible, du reset sélectif et de la réinitialisation complète

**Frontend — filtre générique**

- Composable `useTableFilter` + `applyFilter` (`composables/useTableFilter.ts`) : filtre client-side fuzzy sur tous les champs d'un tableau
- Champ de recherche générique ajouté dans les 11 écrans avec DataTable : Paiements, Exercices, Règles comptables, Plan comptable, Journal, Balance, Salaires, Factures clients, Factures fournisseurs, Banque (transactions + remises), Caisse (journal + comptages)
- i18n : clé `common.filter_placeholder` → « Rechercher… »

**Frontend — mode sombre**

- `useDarkMode.ts` : watcher déplacé au niveau module (singleton) pour éviter les problèmes de lifecycle component
- `main.css` : `body` reçoit `background: var(--p-surface-ground)` et `color: var(--p-text-color)` avec transition douce
- `index.html` : script inline synchrone pour appliquer la classe `.dark-mode` avant le rendu (suppression du flash blanc au chargement)
- `index.html` : titre corrigé « Solde ⚖️ », `lang="fr"`

**Frontend — système d’interface partagé**

- `AppPage.vue`, `AppPageHeader.vue`, `AppPanel.vue`, `AppStatCard.vue` : primitives communes pour homogénéiser les pages, les en-têtes, les panneaux et les cartes de synthèse
- `main.css` : langage visuel partagé pour les mises en page, les métriques, les en-têtes de contenu et les dialogues de formulaire

### Modifié

**Édition métier des factures, paiements et imports**

- Une facture `sent` non réglée reste modifiable, mais toute modification régénère désormais ses écritures comptables auto-générées au lieu de laisser des écritures obsolètes en base
- Une facture déjà consommée (`paid`, ou plus généralement hors cas `draft` / `sent` non réglée) ne peut plus être modifiée directement via l'API
- Les paiements deviennent quasi immuables après création : seules les corrections mineures sans impact structurel (`référence`, `notes`, `n° de chèque`) restent éditables depuis l'écran `Paiements`, et la suppression standard est désormais bloquée en attendant un vrai flux d'annulation métier
- Le rejeu strict des imports réversibles reste désormais explicitement protégé même après retouche manuelle d'un objet importé via l'API, y compris quand l'instance SQLAlchemy a été expirée entre-temps

**Paiements et trésorerie**

- Les règlements clients en `chèque` et `espèces` se saisissent désormais depuis la facture client et son historique, avec un parcours dédié pour enregistrer date, montant, mode, référence et note
- Le journal `Caisse` affiche explicitement les mouvements issus d'un paiement client, et les bordereaux bancaires filtrent les paiements selon le type de remise choisi

**Authentification et permissions**

- Les rôles techniques existants restent inchangés côté API, mais leur présentation est clarifiée côté produit pour préparer l'administration des comptes sans casser les autorisations existantes

**Outillage**

- `dev.ps1` : remplacement de `Start-Process pwsh` (2 fenêtres séparées) par `Start-Job` — backend et frontend tournent dans la même session PowerShell, Ctrl+C arrête les deux proprement

**Frontend — modernisation de l’interface**

- Refonte des vues principales avec une présentation plus aérée et cohérente : tableau de bord, contacts, détail contact, factures clients et fournisseurs, paiements, banque, caisse, import Excel, exercices, salaires et écrans comptables (journal, balance, grand livre, résultat, bilan, règles, plan comptable)
- Harmonisation des dialogues et formulaires métier avec une structure commune (introduction, sections, aides contextuelles) pour les comptes comptables, contacts, factures, salaires, dépôts bancaires, imports, opérations de caisse et saisie manuelle d’écritures
- L'écran d'import Excel a été réorganisé autour d'une synthèse courte, d'onglets dédiés (`Détails`, `Synthèse complète`, `Avertissements`) et d'une table d'opérations filtrable

**Frontend — mode sombre (dark mode)**

- `AppLayout.vue`, `LoginView.vue`, `NavMenu.vue`, `SettingsView.vue` : fonds et couleurs rendus réactifs via `v-bind()` CSS couplé à des `computed` Vue (les tokens `--p-surface-N` du thème Aura sont absolus, non réactifs au mode)
- `AppLayout.vue` : suppression de l'en-tête de sidebar « ⚖️ Solde ⚖️ » (redondant avec le titre de la page)
- `NavMenu.vue` : couleur et fond de l'élément de navigation actif adoucis en dark mode (`rgba(52,211,153,0.12)` + texte `primary-300`)
- `SettingsView.vue` : fond de la « Zone de danger » adouci en dark mode (`rgba(239,68,68,0.08)`)

### Corrigé

**Paiements et trésorerie**

- Un règlement en `espèces` crée désormais immédiatement une entrée en caisse, tandis que la remise d'espèces en banque sort explicitement la somme de la caisse au moment du dépôt
- Un règlement par `chèque` reste en attente d'une remise manuelle en banque au lieu d'être assimilé à un dépôt automatique

**Backend**

- invalidation des anciens jetons JWT après changement ou réinitialisation de mot de passe pour éviter qu'une ancienne session reste active
- `excel_import.py` : support des feuilles Caisse (`caisse`/`cash`) et Banque (`banque`/`bank`/`relev`) dans l'import Excel de gestion ; déduplication des numéros de factures dans le même batch ; création automatique du contact si absent (plutôt que saut de ligne silencieux)
- sécurité et robustesse revues après commentaires de PR : secret JWT obligatoire hors dev/test, conversion propre des erreurs d'édition manuelle en réponses HTTP, metadata Alembic complétée pour l'autogénération
- factures clients mixtes `cs+a` : quand la feuille `Factures` expose des montants distincts `cours` et `adhésion`, l'import historique crée les lignes de facture correspondantes et la génération comptable ventile désormais les produits sur les comptes dédiés au lieu d'un seul produit global
- import réversible BIZ-004 stabilisé : un paiement préparé peut maintenant se rapprocher d'une facture du même classeur déjà planifiée dans le run, même si l'ordre des onglets est défavorable, et l'exécution facture/paiement ne déclenche plus d'erreurs async sur les snapshots enregistrés

**Frontend — bugfixes interface**

- `index.html` : correction de `<\/script>` → `</script>` (artefact d'échappement introduit lors de la création du fichier)
- `main.ts` : enregistrement de `ConfirmationService` manquant — toutes les views utilisant `useConfirm()` (Contacts, Factures, Paiements, Exercices, Salaires) crashaient au chargement
- `DashboardView.vue` : imports PrimeVue manquants (`Card`, `ProgressSpinner`, `Message`, `Select`) — la vue du tableau de bord était vide
- `AccountingBilanView.vue` : imports PrimeVue manquants (`Button`, `Card`, `Column`, `DataTable`, `ProgressSpinner`, `Select`) — la vue était vide
- `api/client.ts` : `baseURL` corrigé de `/api` à `''` — les appels API généraient des URLs en double (`/api/api/...`)
- `api/client.ts` : la file d'attente de refresh JWT propage désormais aussi les échecs, évitant des requêtes pendantes infiniment en cas de refresh refusé
- `api/bank.ts`, `api/cash.ts`, `api/payments.ts` : préfixe `/api/` ajouté aux chemins (cohérence avec le nouveau `baseURL`)
- `i18n/fr.ts` : clés `user.role.*` corrigées en minuscules (`admin`, `tresorier`, `secretaire`, `readonly`) pour correspondre aux valeurs renvoyées par le backend

### Ajouté

**Backend (Phase 7 — Complétion du plan)**

- `ContactHistory` schéma + `get_contact_history()` service + `GET /contacts/{id}/history`
- `POST /contacts/{id}/mark-douteux` : génère les écritures 411xxx → 416xxx pour créances douteuses
- `BilanRead` schéma + `get_bilan()` service + `GET /accounting/entries/bilan` : bilan simplifié actif/passif
- `export_service.py` : `export_journal_csv`, `export_balance_csv`, `export_resultat_csv`, `export_bilan_csv` (UTF-8 BOM, séparateur `;`, montants en format fr)
- 4 endpoints `GET /accounting/entries/{journal,balance,resultat,bilan}/export/csv`
- `PreviewResult` + `preview_gestion_file` + `preview_comptabilite_file` dans `excel_import.py` (dry-run sans DB)
- `POST /import/excel/{gestion,comptabilite}/preview` : estimation du nombre de lignes avant import
- `RulePreviewRequest/Entry` schémas + `preview_rule()` service (simulation sans commit)
- `POST /accounting/rules/{id}/preview` : prévisualisation des écritures générées par une règle
- `parse_ofx()` + `parse_qif()` dans `bank_import.py` (SGML/XML OFX, multi-format dates QIF)
- `POST /bank/transactions/import-ofx` + `import-qif`
- `Dockerfile` : ajout des bibliothèques WeasyPrint (pango, cairo, gdk-pixbuf)
- 19 nouveaux tests (5 fichiers) — 342 tests au total

**Frontend (Phase 7)**

- `accounting.ts` : types `BilanRead`, `ContactHistory`, `RulePreviewEntry`, `PreviewResult` + fonctions `getBilanApi`, `getExportCsvUrl`, `getContactHistoryApi`, `markCreanceDouteuse`, `previewRuleApi`, `previewGestionFileApi`, `previewComptabiliteFileApi`, `importOFXApi`, `importQIFApi`
- `AccountingBilanView.vue` : bilan actif/passif avec filtre exercice + bouton export CSV
- `ContactDetailView.vue` : fiche contact avec historique factures/paiements + action mark-douteux
- `ContactsView.vue` : bouton historique (pi-history) vers la fiche contact
- `AccountingJournalView.vue` : bouton export CSV journal
- `ImportExcelView.vue` : bouton preview (dry-run) avant import
- Router : routes `/accounting/bilan` et `/contacts/:id/history`
- NavMenu : entrée Bilan (pi-chart-line)
- i18n `fr.ts` : clés `bilan.*`, `contact_history.*`, `rule_preview.*`, `bank_import.*`, `import.preview*`

**Backend (Phase 6 — Fonctions avancées)**

- Modèle `Salary` + migration `0010` : salaire mensuel par employé (brut, charges salariales/patronales, PAS, net, total_cost)
- Schémas `SalaryCreate/Update/Read` (validateur YYYY-MM) + `SalarySummaryRow`
- `salary_service.py` : CRUD + `get_monthly_summary` + hook `generate_entries_for_salary`
- Router `/api/salaries` : GET / POST /{id} PUT /{id} DELETE /{id} GET /summary
- `TriggerType` enrichi : `SALARY_GROSS`, `SALARY_EMPLOYER_CHARGES`, `SALARY_PAYMENT` ; 3 règles par défaut ajoutées (641000/421000, 645100/431100, 421000/512100)
- `generate_entries_for_salary` dans `accounting_engine.py` : 3 jeux d'écritures automatiques
- `fiscal_year_service.py` enrichi : `pre_close_checks` (balance, orphelins) et `open_new_fiscal_year` avec report à nouveau (comptes actif/passif à solde non nul)
- Endpoints `/pre-close-checks` (GET) et `/open-next` (POST 201) sur le router fiscal_year
- `dashboard_service.py` : `get_dashboard` (solde banque/caisse, factures impayées/en retard, paiements à remettre, exercice courant, résultat, alertes) et `get_monthly_chart`
- Router `/api/dashboard` : GET / et GET /chart/monthly
- `excel_import.py` service : parseur openpyxl flexible pour `Gestion YYYY.xlsx` (contacts, factures, paiements) et `Comptabilité YYYY.xlsx` (écritures) — détection auto des colonnes, idempotence
- Router `/api/import/excel/gestion` et `/api/import/excel/comptabilite` (limite 10 Mo)
- `main.py` + `database.py` + `conftest.py` : enregistrement des nouveaux modèles et routers
- 22 nouveaux tests (4 fichiers) — 323 tests au total, 78 % couverture

**Frontend (Phase 6)**

- `DashboardView.vue` : KPIs temps réel (cards PrimeVue) + tableau mensuel charges/produits
- `SalaryView.vue` : liste CRUD des salaires + résumé mensuel agrégé + dialog de saisie
- `ImportExcelView.vue` : upload fichier Excel (gestion ou comptabilité) + affichage du rapport d'import
- `api/accounting.ts` : types et fonctions pour salary, dashboard, import Excel, pre-close-checks, open-next
- i18n `fr.ts` : clés `salary.*`, `dashboard.*`, `import.*` + `accounting.fiscalYear.pre_close_*`, `open_next_*`
- Router : routes `/salaries` et `/import/excel`
- NavMenu : entrées Salaires (pi-id-card) et Import Excel (pi-file-excel)

**Backend (Phase 5 — Comptabilité)**

- Modèle `FiscalYear` : exercice comptable avec statuts `open/closing/closed`
- Modèle `AccountingEntry` : écriture en partie double (numéro, date, compte, libellé, débit, crédit, exercice, source)
- Modèle `AccountingRule` + `AccountingRuleEntry` : règles configurables par déclencheur (`TriggerType` — 14 valeurs), libellés avec templates `{{key}}`
- Migrations Alembic `0007` (fiscal_years), `0008` (accounting_entries), `0009` (accounting_rules)
- Schémas Pydantic v2 : `FiscalYearCreate/Read`, `AccountingEntryRead`, `ManualEntryCreate`, `BalanceRow`, `LedgerEntry/Read`, `ResultatRead`, `AccountingRuleRead/Update`
- `accounting_engine.py` : moteur de génération d'écritures basé sur les règles — `generate_entries_for_invoice/payment/deposit`, `seed_default_rules` (13 règles par défaut issues du plan.md)
- `fiscal_year_service.py` : CRUD exercices, clôture (calcul résultat → écriture CLOTURE → statut CLOSED)
- `accounting_entry_service.py` : journal (filtres date/compte/source/exercice), balance, grand livre avec solde glissant, compte de résultat, saisie manuelle équilibrée
- `accounting_rule_service.py` : liste, lecture et mise à jour des règles
- Hooks automatiques dans `invoice.py` (status → SENT), `payment.py` (create_payment) et `bank_service.py` (create_deposit)
- Routeurs `/api/accounting/entries/*`, `/api/accounting/rules/*`, `/api/accounting/fiscal-years/*` enregistrés dans `main.py`
- 93 nouveaux tests (3 fichiers unitaires + 1 intégration) — 87 % couverture globale (301 tests au total)

**Frontend (Phase 5)**

- Types et fonctions API dans `accounting.ts` : journal, balance, grand livre, résultat, saisie manuelle, règles, exercices
- `AccountingJournalView.vue` : journal filtrable + dialog saisie manuelle
- `AccountingBalanceView.vue` : balance agrégée par compte avec totaux débit/crédit/solde
- `AccountingLedgerView.vue` : grand livre par compte avec solde glissant
- `AccountingResultatView.vue` : compte de résultat charges/produits, excédent ou déficit
- `AccountingRulesView.vue` : liste des règles avec activation/désactivation, pré-remplissage
- `FiscalYearView.vue` : liste des exercices, création, clôture avec confirmation
- Routes `/accounting/journal`, `/balance`, `/ledger`, `/resultat`, `/rules`, `/fiscal-years`
- Clés i18n `accounting.journal.*`, `accounting.balance.*`, `accounting.ledger.*`, `accounting.resultat.*`, `accounting.rules.*`, `accounting.fiscalYear.*` dans `fr.ts`
- NavMenu mis à jour avec les 7 nouvelles entrées comptabilité

---

## [0.4.0] — Phase 4 — Paiements & Trésorerie

- Modèle `Payment` : paiement par facture, méthode (espèces/chèque/virement), suivi dépôt en banque
- Modèle `CashRegister` + `CashCount` : journal de caisse avec solde glissant, comptage physique par coupure
- Modèle `BankTransaction` + `Deposit` + table d'association `deposit_payments`
- Migrations Alembic `0005` (payments) et `0006` (caisse + banque)
- Schémas Pydantic v2 : `PaymentCreate/Update/Read`, `CashEntryCreate/Read`, `CashCountCreate/Read`, `BankTransactionCreate/Update/Read`, `DepositCreate/Read`
- Service `payment.py` : CRUD complet, refresh automatique du statut facture (PARTIAL/PAID) à chaque opération
- Service `cash_service.py` : ajout écriture caisse avec solde recalculé, comptage physique, solde actuel
- Service `bank_service.py` : transactions bancaires, rapprochement, bordereaux de remise multi-paiements
- Service `bank_import.py` : import CSV Crédit Mutuel (séparateur `;`, montants en locale française)
- Routeurs `/api/payments/`, `/api/cash/`, `/api/bank/` enregistrés dans `main.py`
- 208 tests (12 nouveaux fichiers de tests) — 84 % de couverture globale

**Frontend (Phase 4)**

- `api/payments.ts`, `api/cash.ts`, `api/bank.ts` : clients API typés
- `PaymentsView.vue` : liste globale des paiements, filtre "à remettre en banque"
- `CashView.vue` : journal de caisse + interface comptage par coupure (onglets)
- `BankView.vue` : relevé bancaire, import CSV, bordereaux de remise, bouton de lettrage
- Routes `/payments`, `/cash`, `/bank` enregistrées dans le router
- Clés i18n `payments.*`, `cash.*`, `bank.*` ajoutées dans `fr.ts`
- Modèle `Invoice` + `InvoiceLine` : numéro `YYYY-C-NNNN` / `YYYY-F-NNNN`, type (`client` | `fournisseur`), label, statuts (draft→sent→paid/partial/overdue/disputed), lignes multi
- Migration Alembic `0004` : tables `invoices` + `invoice_lines`
- Service factures : numérotation auto séquentielle par type et année, calcul total, transitions de statut avec validation, duplication, soft-delete (draft uniquement)
- Exceptions typées : `InvoiceStatusError`, `InvoiceDeleteError`
- Routeur `/api/invoices/` : CRUD REST, `PATCH /{id}/status`, `POST /{id}/duplicate`, `DELETE /{id}`, `GET /{id}/pdf`, `POST /{id}/send-email`, `POST /{id}/file` (upload)
- Upload fichier facture fournisseur : validation MIME (PDF/JPEG/PNG/WebP), limite 10 MB, nom UUID (anti-path-traversal)
- Service `pdf_service.py` : WeasyPrint (import paresseux), template Jinja2 `invoice.html` (logo, coordonnées, lignes, mention Loi 1901)
- Service `email_service.py` : smtplib STARTTLS/SSL-SSL, PDF en pièce jointe, transition draft→sent automatique
- 145 tests pytest (unitaires + intégration) — 79 % de couverture

**Frontend (Phase 3)**

- `api/invoices.ts` : toutes les fonctions CRUD + status + duplicate + pdf + email + upload
- `ClientInvoicesView.vue` : liste filtrée (statut, année), actions PDF/email/dupliquer/supprimer
- `ClientInvoiceForm.vue` : formulaire avec lignes dynamiques et total calculé
- `SupplierInvoicesView.vue` : liste avec dialog upload fichier joint
- `SupplierInvoiceForm.vue` : formulaire montant direct + référence fournisseur
- Routes `/invoices/client` et `/invoices/supplier`
- Clés i18n complètes : `invoices.*` (statuts, labels, actions)
- Menu navigation : Factures clients (`pi-file`) + Factures fournisseurs (`pi-file-import`)

---

**Backend (Phase 2)**

- Migration Alembic `0002` : table `contacts`
- Service contacts : CRUD complet, recherche insensible à la casse sur nom/prénom/email, filtrage par type, pagination
- Routeur `/api/contacts/` : CRUD REST avec guards rôle (`SECRETAIRE+`)
- Modèle `AccountingAccount` : numéro (unique), label, type (`actif` | `passif` | `charge` | `produit`), soft-delete
- 24 comptes comptables associatifs pré-configurés (`DEFAULT_ACCOUNTS`) + seed idempotent
- Migration Alembic `0003` : table `accounting_accounts`
- Service plan comptable : CRUD, seed idempotent, filtre par type
- Routeur `/api/accounting/accounts/` : CRUD REST + `POST /seed` avec guards rôle (`TRESORIER+`)
- 103 tests pytest (unitaires + intégration) — 89 % de couverture

**Frontend**

- `api/contacts.ts` : fonctions CRUD vers `/api/contacts/`
- `api/accounting.ts` : fonctions CRUD vers `/api/accounting/accounts/` + seed
- `ContactsView.vue` : DataTable PrimeVue avec recherche (debounce 300 ms) et filtre par type, Dialog création/édition, suppression avec confirmation
- `AccountingAccountsView.vue` : DataTable avec filtre par type (boutons), bouton Seed, Dialog création/édition
- `ContactForm.vue` : formulaire de création/édition de contact
- `AccountForm.vue` : formulaire de création/édition de compte comptable (numéro désactivé en édition)
- Routes `/contacts` et `/accounting/accounts` ajoutées au Vue Router
- Entrées de navigation contacts (`pi-users`) et plan comptable (`pi-list`) dans `NavMenu.vue`
- Clés i18n supplémentaires : `contacts.*`, `accounting.*`, `common.all`, `common.actions`

---

**Backend (Phase 1)**

- Fabrique d'application FastAPI (`create_app()`) avec lifespan, CORS, service des fichiers statiques Vue.js
- Configuration Pydantic Settings avec validation : `JWT_SECRET_KEY` (min 32 caractères), `FISCAL_YEAR_START_MONTH` (défaut 8 = août), paramètres SMTP optionnels
- Moteur SQLAlchemy 2 async avec SQLite en mode WAL et contrôle des clés étrangères
- Modèle `User` avec enum `UserRole` : `READONLY`, `SECRETAIRE`, `TRESORIER`, `ADMIN`
- Service d'authentification : hachage bcrypt (direct, compatible Python 3.13), tokens JWT accès + rafraîchissement
- Routeur auth : `POST /api/auth/login`, `POST /api/auth/refresh`, `GET /api/auth/me`, `POST /api/auth/users` (admin uniquement)
- Dépendance `get_current_user` et fabrique `require_role(*roles)` pour l'autorisation des routes
- **Alembic** : `alembic.ini`, `backend/alembic/env.py` (async), `script.py.mako`, migration `0001` (tables `users` + `app_settings`)
- **Modèle `AppSettings`** : table single-row (id=1) pour les paramètres de l'association et SMTP
- **API Settings** : `GET /api/settings/` et `PUT /api/settings/` avec mise à jour partielle (admin uniquement) — `smtp_password` exclu de la réponse
- **Service settings** : `get_settings()` (création automatique si absente) et `update_settings()` (partial update)
- 44 tests pytest (unitaires + intégration) — 88 % de couverture

**Frontend**

- Scaffold Vue.js 3 avec TypeScript, Vue Router, Pinia, Vitest, ESLint + Prettier
- PrimeVue 4 avec preset Aura (`@primeuix/themes`) et primeicons
- `vue-i18n` v11 avec locale française (auth, navigation, paramètres, rôles utilisateurs)
- Client API axios avec injection du header `Authorization` et rafraîchissement automatique du token sur 401
- `useAuthStore` (Pinia) : connexion/déconnexion/rafraîchissement, persistance localStorage, computed `isAdmin`/`isTresorier`
- `LoginView.vue` : formulaire PrimeVue avec messages d'erreur i18n
- `AppLayout.vue` : layout responsive — barre latérale desktop + tiroir mobile
- `NavMenu.vue` : menu de navigation adapté au rôle
- Vue Router avec guards `requiresAuth` et `requiresAdmin`, chargement paresseux des routes protégées
- **`api/settings.ts`** : `getSettingsApi()` et `updateSettingsApi()`
- **`SettingsView.vue`** : formulaire PrimeVue complet — infos association (nom, SIRET, adresse, mois début exercice) + configuration SMTP (host, port, user, from, TLS toggle) avec messages de succès/erreur
- 11 tests Vitest unitaires pour le store auth — tous verts

**Infra**

- `Dockerfile` multi-stage : `node:22-alpine` pour le build Vue.js, `python:3.13-slim` pour le runtime, utilisateur non-root `solde`
- `docker-compose.yml` : 1 service, 1 volume `./data`, port 8000
- `.dockerignore`
- `.env.example` documenté (JWT_SECRET_KEY, DATABASE_URL, SMTP optionnel)
- README mis à jour avec les instructions d'installation dev et Docker

### Modifié

- Remplacement de `passlib[bcrypt]` par `bcrypt` en import direct (compatibilité Python 3.13 + bcrypt ≥ 4.0)
- `UserRole` migré de `(str, Enum)` vers `StrEnum` (Python 3.11+)
- Annotations de type ajoutées sur `_build_engine()`, `lifespan()`, `require_role()` et `do_run_migrations()` (mypy strict)

---

[Non publié]: https://github.com/davidp57/solde/commits/feature/phase1-foundations
