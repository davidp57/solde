# Nouveautés de Solde ⚖️

Ce document présente les changements visibles dans l'application, version par version.

---

## Version 1.7.2 — 12 mai 2026

### Tous les utilisateurs

#### Listes — limite d'affichage configurable
- Par défaut, chaque grande liste (factures, paiements, contacts, salaires, transactions bancaires) n'affiche désormais que les **500 premiers éléments**.
- Une **bannière d'avertissement** apparaît en haut de la liste quand des éléments sont masqués, avec un lien **« Désactiver la limite »** pour tout charger d'un clic.
- Une fois la limite désactivée, une **notice discrète** indique qu'un chargement jusqu'à **5 000 éléments** est appliqué, avec la possibilité de **réactiver la limite**.
- Ce réglage est **propre à chaque navigateur / onglet** : il s'efface à la fermeture de l'onglet.

#### Contacts — fusion des doublons
- Un dialogue de **fusion de contacts** permet de regrouper deux fiches en une seule quand un doublon est détecté.
- Les informations utiles sont conservées sur la fiche finale et l'historique (factures/paiements) reste rattaché au contact conservé.

### Administrateur

#### Paramètres — limite d'affichage
- La **valeur de la limite** est configurable dans Paramètres > Association (champ *Limite d'affichage par défaut*).
- Valeur **0** = chargement jusqu'à **5 000 éléments** par requête.
- La modification s'applique immédiatement pour tous les utilisateurs dès leur prochaine visite.

#### Sauvegarde OneDrive
- L'autorisation OneDrive repose désormais sur un **code d'appareil** (device code), mieux adaptée aux déploiements Docker/NAS sans navigateur intégré.
- Le transfert vers OneDrive est géré directement via l'API Microsoft, avec un suivi d'état plus fiable dans l'interface.

---

## Version 1.7.1 *(à venir)*

### Secrétaire

#### Factures historiques (import Word) et archivées
- Nouveau script d'import des factures historiques depuis des documents Word (`.docx`), avec reprise des factures déjà payées.
- Les factures historiques importées depuis Word reprennent correctement le montant déjà réglé : le reste dû est affiché à **0 €** quand la facture était déjà payée.
- Quand un PDF existe déjà pour une facture importée, il est réutilisé directement pour l'aperçu au lieu de repasser par le document Word.
- L'aperçu PDF masque désormais le volet latéral des pages quand le navigateur autorise ce réglage.

### Tous les utilisateurs

#### Export Excel
- Un bouton **« Exporter Excel »** est disponible dans toutes les grandes listes : factures fournisseur, paiements, contacts, employés, salaires, mouvements de caisse, transactions bancaires, exercices comptables, plan comptable, règles comptables, journal, grand livre, balance, bilan, compte de résultat.
- L'export télécharge uniquement les **lignes affichées après filtrage**, au format `.xlsx` directement lisible dans Excel ou LibreOffice Calc.

### Secrétaire

#### Factures client — Archivage
- Un nouveau statut **« Archivée »** est disponible pour les factures intégralement réglées. Une facture archivée ne peut plus être modifiée.
- Bouton **« Archiver la sélection »** dans la barre d'outils de la liste des factures client : archive d'un coup toutes les factures payées actuellement visibles.
- Sur une facture archivée, un bouton **« Télécharger le document »** permet de récupérer le fichier Word d'origine (si disponible).

---

## Version 1.7.0 *(à venir)*

### Administrateur

#### Paramètres — Sauvegarde automatique (nouvelle fonctionnalité)
- Nouveau panneau **« Sauvegarde automatique »** dans les paramètres (visible uniquement par les administrateurs).
- Il est possible d'**activer ou désactiver** les sauvegardes automatiques et de choisir leur fréquence :
  - **Quotidien (heure fixe)** : la sauvegarde se déclenche chaque jour à l'heure choisie (format HH:MM).
  - **Toutes les N heures** : sauvegarde répétée selon un intervalle en heures.
  - **Expression cron** : planning avancé personnalisé.
- Par défaut, seul le **dernier fichier de sauvegarde** (snapshot de la base) est envoyé vers la destination. L'option **« Inclure tous les fichiers de sauvegarde précédents »** permet d'envoyer l'intégralité des sauvegardes disponibles.
- Le **statut du dernier enregistrement** (date, heure, succès ou échec) est visible en temps réel, y compris lorsque la sauvegarde a été déclenchée automatiquement — le spinner apparaît dans les 10 secondes suivant le démarrage.
- Il est possible d'ajouter plusieurs **destinations de sauvegarde** : dossier local sur le serveur, partage réseau (SMB/NAS), ou OneDrive.
- Chaque destination peut être **testée** (connexion vérifiée) avant d'être activée.
- La liste des sauvegardes disponibles permet de **tester la restauration** (vérification de l'intégrité du fichier) ou de **restaurer** une sauvegarde précédente.
- Une **notification par e-mail** peut être activée pour prévenir en cas d'échec de sauvegarde.

---

## Version 1.6.0 — 5 mai 2026

### Tous les utilisateurs

#### Factures — vue sur téléphone
- Les **tuiles de factures client** sont allégées : la ligne de catégorie est retirée pour éviter les cartes trop hautes.
- Les **tuiles de factures fournisseur** regroupent la référence et le trombone sur une seule ligne.
- La **fenêtre de prévisualisation d'une facture fournisseur** s'affiche mieux sur mobile : date, échéance et référence sur lignes séparées ; boutons réduits aux icônes ; totaux non tronqués.

### Trésorier

#### Banque — Dépôts en attente
- Le bouton **« Confirmer le dépôt »** est remplacé par un bouton **« Actions »** qui ouvre une fenêtre de gestion complète.
- Depuis cette fenêtre, il est possible de **retirer des chèques** d'un bordereau existant, ou de **modifier les coupures** d'un dépôt espèces.
- Quatre actions disponibles : annuler les changements, enregistrer les changements sans confirmer, **annuler le dépôt** (les règlements sont libérés), ou **confirmer le dépôt**.
- Une confirmation est demandée avant d'annuler ou de valider définitivement un dépôt.
- Le total d'un dépôt espèces est désormais **calculé automatiquement** depuis les coupures saisies — il n'est plus possible de saisir un montant total incohérent avec le détail.

### Administrateur

#### Supervision — Cohérence des données
- Nouveau panneau **« Paiements chèques incohérents »** : liste les chèques marqués comme remis mais sans date de remise (état pouvant résulter d'un import Excel ancien).
- Pour chaque ligne, il suffit de choisir la date de remise et de cliquer **« Corriger »** pour mettre les données en ordre.

---

## Version 1.5.1 — 4 mai 2026

### Tous les utilisateurs

#### Mode téléphone
- Les principales listes (factures client et fournisseur, contacts, transactions bancaires, dépôts, règlements, caisse) s'affichent en **vue cartes** sur les petits écrans, plus lisibles que les tableaux.
- Les fenêtres de dialogue s'adaptent automatiquement à la largeur de l'écran sur mobile.
- Les **cartes de synthèse** (indicateurs chiffrés) s'affichent sur **2 colonnes** sur mobile.

#### Saisie des règlements
- Lorsque le mode de paiement **chèque** est sélectionné, le numéro de chèque est **suggéré automatiquement** au format `AAAAMMJJ.NN` (exemple : `20260504.01`). Le numéro reste modifiable avant validation.

#### Navigation dans les dialogues
- Les dialogues d'historique factures client et les prévisualisations de factures fournisseur disposent d'une barre **Précédent / Suivant** en haut et en bas de la fenêtre pour naviguer entre les éléments sans fermer le dialogue.

### Secrétaire

#### Contacts
- L'onglet **Clients** est désormais actif par défaut dans la vue Contacts.
- Les contacts ayant une facture récente (moins de 6 mois) apparaissent **en tête de liste**, puis par ordre alphabétique.

### Trésorier

#### Banque — Relevé
- Les transactions du relevé peuvent être filtrées par compte : **Tous / Courant / Épargne**.
- Nouvelle catégorie **« Sans écriture »** : une transaction avec cette catégorie ne génère aucune écriture comptable lors du rapprochement. Utile pour les virements extérieurs ou les ajustements techniques.

#### Tableau de bord
- Les détails du contenu d'un dépôt espèces (coupures) sont affichés directement sur chaque dépôt en attente.
- Nouvelle carte **« Solde épargne »** affichant le solde du compte Livret A en complément du solde courant.

#### Factures fournisseur
- La barre de navigation Précédent / Suivant est également disponible **en bas** de la fenêtre de prévisualisation, pour faciliter la consultation du document joint.

#### Contacts
- Le bouton **« Passer en créance douteuse »** n'apparaît plus pour les contacts de type Fournisseur.

### Administrateur

#### Paramètres — Banque
- Deux nouveaux champs : **identifiant ACCTID OFX** pour le compte courant et pour le compte épargne. Une fois renseignés, les fichiers OFX contenant les deux comptes sont automatiquement attribués au bon compte, sans sélection manuelle à l'import.

#### Paramètres — Règlements
- Le **modèle de numérotation des chèques** est configurable. Par défaut : `{date}.{seq}` — les variables `{date}` et `{seq}` sont décrites dans l'aide en ligne.

---

## Version 1.4.0 — 3 mai 2026

### Tous les utilisateurs

#### Confort de navigation
- Les listes affichent désormais **50 lignes par défaut** (au lieu de 20) — moins de clics pour parcourir les données.
- Un message d'avertissement s'affiche quand une liste dépasse 1 000 résultats, pour signaler qu'il faut affiner les filtres.

### Secrétaire

#### Saisie des factures
- Dans les lignes d'une facture, la **virgule est acceptée** comme séparateur décimal (elle est automatiquement convertie en point).
- La **première lettre** d'un libellé de prestation est **mise en majuscule automatiquement** dès qu'on passe au champ suivant.

---

## Version 1.3.0 — 2 mai 2026

### Tous les utilisateurs

#### Tableau de bord
- Les **bordereaux de dépôt en attente** sont désormais visibles directement depuis le tableau de bord, sans avoir à ouvrir la vue Banque.

### Secrétaire

#### Contacts
- Possibilité d'enregistrer **jusqu'à 2 adresses e-mail supplémentaires** par contact, avec un libellé libre (ex. « autre parent »).
- La recherche de contacts porte maintenant sur les noms de l'enfant et de l'autre parent.
- Marquage **« client indésirable »** : badge rouge dans la liste, et blocage de la création de facture tant que le marquage est actif.

#### Assistant de création de facture rapide
- L'étape de confirmation affiche maintenant le **nom complet du contact** concerné.
- Un bouton **« Envoyer par e-mail »** est disponible directement dans la confirmation, avec un badge « E-mail envoyé » après envoi.
- Lors de l'envoi d'une facture, les **adresses e-mail secondaires** du contact apparaissent avec des cases à cocher pour choisir les destinataires.

### Trésorier

#### Paiements et remises en banque
- La colonne « Remis en banque » distingue maintenant **trois états** : ✓ remis / ⏱ en cours de dépôt (orange) / ✗ à remettre.
- Un bouton **« Tout sélectionner / Tout désélectionner »** facilite la création d'un bordereau de chèques.
- Nouveau panneau **« Dépôts en attente »** dans la vue Banque : liste les bordereaux préparés mais pas encore confirmés, avec un bouton « Confirmer » par bordereau.
- Le tableau des dépôts affiche une colonne **Statut** (en attente / confirmé) avec filtre.
- Le total d'un bordereau d'espèces ne compte plus les pièces (seuls les billets sont déposables).

#### Factures fournisseur
- Nouveau **dialogue de prévisualisation** : historique des règlements, aperçu du PDF ou de l'image jointe, navigation entre factures précédente/suivante. Accessible aussi depuis l'historique d'un contact.
- Bouton **« Enregistrer un règlement »** disponible dans la liste des factures fournisseur et dans la prévisualisation.
- Un règlement fournisseur en espèces génère automatiquement une **sortie de caisse** correspondante.
- Les factures fournisseur créées manuellement démarrent avec le statut **« Envoyée »** (au lieu de « Brouillon »).

#### Caisse
- Comptage de caisse : le total des pièces se saisit dans un **champ unique** « Pièces (ferraille) » au lieu de chaque coupure.
- Les paiements en espèces reçus entrent **immédiatement** dans la caisse. La sortie caisse (vers la banque) n'est générée qu'à la confirmation du bordereau.

#### Banque et relevés
- Une **icône crayon** sur chaque transaction du relevé permet de corriger la catégorie détectée automatiquement.
- Deux nouveaux boutons sur le relevé : **« Tout rapprocher »** et **« Rapprocher avant le… »** pour valider plusieurs transactions en une fois.
- Le rapprochement génère désormais automatiquement les **écritures comptables** correspondantes selon la catégorie (frais bancaires, charges sociales, subventions, virements internes).
- La colonne Référence du relevé affiche la référence comptable lisible (plus jamais un code technique interne).
- La source d'un import bancaire est maintenant précise : Excel, CSV, OFX ou QIF.
- Les transactions déjà importées sont silencieusement ignorées (pas de doublons).
- Un fichier OFX contenant plusieurs comptes bancaires est refusé avec un message d'erreur clair.

#### Salaires
- Les écritures comptables de salaires sont désormais datées au **dernier jour du mois** (correction d'une erreur de date).

### Administrateur

#### Sauvegardes
- Le libellé d'une sauvegarde peut contenir jusqu'à **100 caractères** (au lieu de 50).
- Un message de confirmation s'affiche dans l'interface après chaque sauvegarde réussie.

---

## Version 1.2.1 — 2 mai 2026

### Tous les utilisateurs

#### Aperçus PDF
- L'aperçu des factures PDF fonctionne maintenant correctement dans Chrome et Firefox.

---

## Version 1.1.0 — 28 avril 2026

### Secrétaire / Trésorier

#### Paramètres
- Les gestionnaires (trésorier) peuvent désormais **consulter les paramètres** de l'association en lecture seule (modification réservée aux administrateurs).

#### Contacts
- Nouvelles informations sur la fiche contact : **prénom/nom de l'enfant** et **prénom/nom de l'autre parent**.
- La recherche de contacts porte sur ces nouveaux champs.

#### Factures client
- La **date du jour est pré-remplie** à la création d'une nouvelle facture.
- L'édition d'une facture est **bloquée** si elle a déjà été envoyée avec un paiement partiel, ou si elle est entièrement payée.
- Le dialogue de paiement affiche le **nom du client, la description, le montant total et l'échéance** de la facture.

#### PDF des factures
- Les **instructions de règlement** (IBAN, BIC, numéro de chèque à l'ordre de) sont ajoutées en pied de facture.

#### Notes internes
- Tous les utilisateurs peuvent saisir des **notes internes** via la page Aide (bouton « Ajouter une note »).

### Trésorier

#### Paiements et remises en banque
- Nouveau statut intermédiaire pour les chèques : **« en bordereau »** (entre la création du bordereau et sa confirmation).
- Bouton **« Tout sélectionner / Tout désélectionner »** dans le dialogue de création de bordereau.
- La colonne « Remis en banque » distingue les trois états.
- Le compteur de paiements non remis sur le tableau de bord exclut les chèques déjà en bordereau.

#### Dépôts et caisse
- Nouveau bouton **« Confirmer »** pour valider un bordereau de dépôt.
- Panneau **« Dépôts en attente »** dans la vue Banque.

### Administrateur

#### Notes internes
- Les administrateurs voient **tous les commentaires** de tous les utilisateurs depuis la section Administration.
- Possibilité de **marquer une note comme résolue** ou de la supprimer.
