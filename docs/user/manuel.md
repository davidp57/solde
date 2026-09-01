# Manuel utilisateur — Solde ⚖️

Ce manuel décrit toutes les fonctionnalités de Solde à travers des cas d'usage concrets.
Il est destiné aux utilisateurs disposant d'un rôle **Gestionnaire**, **Comptable** ou **Administrateur**.

---

## Sommaire

1. [Connexion et mot de passe](#1-connexion-et-mot-de-passe)
2. [Navigation et tableau de bord](#2-navigation-et-tableau-de-bord)
3. [Contacts](#3-contacts)
4. [Factures clients](#4-factures-clients)
5. [Paiements](#5-paiements)
6. [Factures fournisseurs](#6-factures-fournisseurs)
7. [Caisse](#7-caisse)
8. [Banque](#8-banque)
9. [Salaires et employés](#9-salaires-et-employés)
10. [Comptabilité](#10-comptabilité)
11. [Exercices comptables](#11-exercices-comptables)
12. [Documents](#12-documents)
13. [Mon profil](#13-mon-profil)
14. [Paramètres (administrateur)](#14-paramètres-administrateur)
15. [Guide par rôle — « Je veux… »](#guide-par-rôle-je-veux)

---

## 1. Connexion et mot de passe

### Se connecter

1. Ouvrir l'URL de l'application dans un navigateur.
2. Saisir l'identifiant et le mot de passe.
3. Cliquer sur **Se connecter**.

La session reste active automatiquement grâce à un mécanisme de renouvellement silencieux. Le jeton d'accès expire au bout de 60 minutes, mais est renouvelé en arrière-plan pendant 30 jours sans que l'utilisateur ait à se reconnecter. Les identifiants ne sont jamais stockés localement.

### Changement de mot de passe forcé

Si un administrateur a créé ou réinitialisé votre compte, un changement de mot de passe est exigé à la première connexion.

1. L'application affiche automatiquement la page de changement de mot de passe.
2. Saisir le mot de passe temporaire, puis le nouveau mot de passe (deux fois).
3. Le nouveau mot de passe doit contenir **au moins 8 caractères**, **une majuscule** et **un chiffre**.
4. Cliquer sur **Changer le mot de passe**.
5. Vous êtes redirigé vers le tableau de bord.

### Se déconnecter

Cliquer sur votre nom d'utilisateur en haut à droite → **Se déconnecter**.

---

## 2. Navigation et tableau de bord

### Menu principal

Le menu latéral donne accès aux modules de l'application. Les modules visibles dépendent de votre rôle :

| Module | Gestionnaire | Comptable | Administrateur |
|---|---|---|---|
| Tableau de bord | ✅ | ✅ | ✅ |
| Contacts | ✅ | ✅ | ✅ |
| Factures | ✅ | ✅ | ✅ |
| Paiements | ✅ | ✅ | ✅ |
| Banque | ✅ | ✅ | ✅ |
| Caisse | ✅ | ✅ | ✅ |
| Salaires | ✅ | ✅ | ✅ |
| Comptabilité | — | ✅ | ✅ |
| Paramètres | — | — | ✅ |
| Administration | — | — | ✅ |

### Tableau de bord

Le tableau de bord affiche une synthèse en temps réel :

- **Solde en cours** : encaissements vs dépenses de l'exercice en cours.
- **Factures impayées** : liste des factures dont l'échéance est dépassée ou proche.
- **Tuiles d'accès rapide** : trois boutons d'action directe disponibles depuis le tableau de bord :
  - **Nouvelle facture client** — ouvre le dialogue de création de facture
  - **Nouveau paiement** — ouvre le dialogue d'enregistrement d'un paiement
  - **Nouvelle entrée de caisse** — ouvre le dialogue d'ajout d'une entrée caisse

Cliquer sur une facture impayée dans le tableau de bord ouvre directement la fiche facture.

---

## 3. Contacts

### Consulter la liste des contacts

**Contacts** → la liste affiche les colonnes suivantes :

| Colonne | Description |
|---|---|
| Nom | Nom de famille |
| Prénom | Prénom |
| Type | Client, Fournisseur, Les deux, ou Employé |
| E-mail | Adresse e-mail |
| Téléphone | Numéro de téléphone |
| Dernière facture | Référence et date de la dernière facture émise |

Toutes les colonnes sont **triables** : cliquer sur l'en-tête de colonne pour trier en ordre croissant, recliquer pour l'ordre décroissant. Un troisième clic supprime le tri.

**Filtrer la liste**

Deux mécanismes de filtrage sont disponibles, cumulables :

1. **Recherche globale** (barre au-dessus du tableau) — filtre simultanément sur le nom, le prénom, le type, l'e-mail et le téléphone.
2. **Filtres par colonne** — cliquer sur l'icône de filtre dans chaque en-tête de colonne :
   - Nom, Prénom, E-mail, Téléphone : saisie de texte libre.
   - Type : liste de cases à cocher (Client, Fournisseur, Les deux, Employé).

Les filtres actifs sont affichés sous forme de libellés au-dessus du tableau. Le bouton **Réinitialiser les filtres** efface tous les filtres en un clic.

Un onglet rapide permet aussi de basculer entre **Tous**, **Clients** et **Fournisseurs** sans saisir de filtre.

### Créer un contact

1. Cliquer sur **Nouveau contact**.
2. Renseigner le **nom** (obligatoire), le prénom (optionnel) et l'e-mail principal (optionnel).
3. Optionnel : renseigner l'adresse, le téléphone, les notes.
4. Optionnel : dans la section **Adresses e-mail supplémentaires**, ajouter jusqu'à 2 adresses additionnelles avec un libellé libre (ex. : « Comptabilité », « Direction »). Ces adresses apparaîtront comme destinataires lors de l'envoi de factures.
5. Cliquer sur **Enregistrer**.

> L'e-mail (principal ou supplémentaire) est nécessaire pour pouvoir envoyer des factures par e-mail à ce contact.

### Modifier un contact

1. Cliquer sur le contact dans la liste.
2. Modifier les champs souhaités.
3. Pour ajouter, modifier ou supprimer des adresses e-mail supplémentaires, utiliser la section **Adresses e-mail supplémentaires**.
4. Cliquer sur **Enregistrer**.

### Fusionner deux contacts

La fusion permet de regrouper deux fiches en double en conservant un seul contact final.

1. Ouvrir la fiche du contact principal à conserver.
2. Cliquer sur **Fusionner**.
3. Sélectionner le contact source à fusionner.
4. Vérifier le récapitulatif et confirmer.

Après fusion, les factures et paiements du contact source sont rattachés au contact conservé.

### Marquer un client comme indésirable

Cette fonctionnalité s'applique aux contacts de type **Client** ou **Les deux**. Elle permet de bloquer la création de nouvelles factures pour un client en litige ou en défaut de paiement.

1. Ouvrir la fiche du contact.
2. Activer le toggle **Client indésirable**.
3. Cliquer sur **Enregistrer**.

Un badge rouge **Indésirable** s'affiche alors dans la liste des contacts. Toute tentative de créer une facture pour ce contact sera bloquée avec un message d'erreur explicite.

Pour lever le blocage : désactiver le toggle et enregistrer.

### Historique d'un contact

Sur la fiche contact, l'onglet **Historique** affiche toutes les factures et paiements liés à ce contact. Cliquer sur une facture pour l'ouvrir en prévisualisation inline, avec navigation ‹ précédent / suivant ›.

---

## 4. Factures clients

### Workflow type : émettre et encaisser une facture

Voici le cycle complet d'une facture client, de la création au paiement :

1. **Créer** la facture (formulaire complet ou wizard rapide — voir ci-dessous).
2. **Valider** pour lui attribuer un numéro définitif.
3. **Envoyer par e-mail** au client (bouton dans la fiche ou directement depuis le wizard).
4. Quand le règlement arrive, **enregistrer un paiement** et le lier à la facture — le statut passe automatiquement à *Payée* ou *Partiellement payée*.
5. Si la facture est réglée par chèque ou espèces, **créer une remise en banque** pour tracer le dépôt.

---

### Consulter la liste des factures

**Factures** → liste filtrée par exercice. Colonnes : numéro, contact, date, montant, montant payé, statut.

Statuts possibles :

| Statut | Signification |
|---|---|
| **Brouillon** | Facture en cours de saisie, non validée. Modifiable librement. |
| **Validée** | Facture finalisée, numéro attribué. En attente de paiement. |
| **Payée** | Entièrement réglée. |
| **Partiellement payée** | Un ou plusieurs paiements reçus, solde restant dû. |
| **En retard** | Échéance dépassée, non réglée. |
| **Irrécouvrable** | Passée en perte (créance douteuse). |
| **Archivée** | Facture payée gelée pour historique, non modifiable. |

---

### Créer une facture rapidement (wizard)

Le wizard permet de créer et valider une facture client en quelques clics depuis le **tableau de bord** ou le bouton **+ Facture rapide** :

1. **Étape 1 — Contact** : sélectionner le client. Si le contact est marqué *Indésirable*, la création est bloquée à cette étape.
2. **Étape 2 — Lignes** : ajouter les lignes de facturation (type, description, quantité, prix). Les prix sont pré-remplis depuis les paramètres.
3. **Étape 3 — Confirmation** : la facture est créée et validée automatiquement. L'écran affiche le numéro et le nom du client.
   - Bouton **Envoyer par e-mail** : ouvre le dialogue d'envoi sans fermer le wizard.
   - Bouton **Nouvelle facture** : recommence le wizard pour un autre client.
   - Bouton **Voir la facture** : ouvre la fiche complète.

> Le wizard crée la facture directement en statut *Validée* — il n'y a pas d'étape brouillon.

---

### Créer une facture (formulaire complet)

1. Cliquer sur **Nouvelle facture**.
2. Sélectionner le **contact** (obligatoire). Si le contact est *Indésirable*, le bouton **Valider** est désactivé.
3. Renseigner la **date** (obligatoire).
4. La **date d'échéance** est calculée automatiquement d'après le délai par défaut configuré. Elle peut être modifiée manuellement.
5. Ajouter des **lignes de facturation** :
   - Choisir le type : **cours**, **adhésion**, **autre**.
   - Saisir la description, la quantité, le prix unitaire.
   - Le prix unitaire est pré-rempli d'après les prix par défaut configurés dans les paramètres.
6. Optionnel : ajouter un commentaire interne.
7. Cliquer sur **Enregistrer** pour sauvegarder en brouillon, ou **Valider** pour finaliser la facture.

> La numérotation est attribuée automatiquement à la validation. Elle ne peut pas être modifiée manuellement.

### Modifier une facture

Une facture en **brouillon** peut être modifiée librement.

Une facture **validée** reste modifiable — **lignes comprises** — tant qu'**aucun règlement n'y est enregistré**. Les écritures comptables sont alors régénérées automatiquement, et le PDF est reconstruit à la prochaine consultation ou au prochain envoi. Le **numéro de facture ne change jamais**.

Dès qu'un règlement est saisi, la facture est verrouillée. Pour la corriger, il faut d'abord **annuler le règlement** (voir [Annuler un règlement saisi par erreur](#annuler-un-règlement-saisi-par-erreur)), modifier la facture, puis ressaisir le règlement.

> **Facture erronée déjà envoyée au client ?** La corriger, puis la **renvoyer par e-mail** en précisant dans le message qu'elle annule et remplace la précédente : le PDF joint reflète automatiquement la correction. Pour une remise oubliée, ajouter une ligne de facturation à **prix unitaire négatif** (le total de la facture doit rester positif).

### Supprimer une facture

Seules les factures en **brouillon** sans paiement associé peuvent être supprimées.

### Envoyer une facture par e-mail

1. Ouvrir la fiche facture (ou cliquer sur **Envoyer par e-mail** depuis la confirmation du wizard).
2. Cliquer sur **Envoyer par e-mail**.
3. **Destinataires** :
   - Si le contact n'a qu'une adresse e-mail → le champ est en lecture seule, pré-rempli.
   - Si le contact a plusieurs adresses → des cases à cocher apparaissent, toutes pré-cochées. Décocher les destinataires à exclure. L'envoi est bloqué si aucune case n'est cochée.
4. Optionnel : modifier l'objet et le corps du message.
5. Un aperçu PDF de la facture est affiché à droite.
6. Cliquer sur **Envoyer**.

Le PDF est joint automatiquement. Un envoi réussi est tracé dans l'historique de la facture.

> Pour que l'envoi fonctionne, le SMTP doit être configuré dans les paramètres (rôle administrateur).
> Un contact sans aucune adresse e-mail ne peut pas recevoir de facture par e-mail.

### Télécharger le PDF

Sur la fiche facture, cliquer sur **Télécharger PDF**.

Le PDF d'une facture **entièrement réglée** affiche un filigrane **« PAYÉ »** en rouge en diagonale sur chaque page. Les factures partiellement payées ou en attente n'ont pas de filigrane.

### L'aperçu PDF ne s'affiche pas dans Chrome

Si l'aperçu PDF reste vide dans Chrome (dialogue de facture, envoi par e-mail, historique contact), vérifier le réglage suivant dans Chrome :

1. Dans la barre d'adresse, saisir `chrome://settings/content/pdfDocuments`
2. S'assurer que l'option **« Ouvrir les PDF dans Chrome »** est sélectionnée (et non « Télécharger les PDF »).
3. Relancer la page.

Si le paramètre est correct et que l'aperçu ne fonctionne toujours pas, vérifier l'absence d'extensions Chrome qui interceptent les PDF (ex. Adobe Acrobat, PDF Viewer tiers). Les désactiver temporairement pour tester.

> Ce paramètre est propre à chaque navigateur. Il n'affecte pas le téléchargement du PDF (bouton **Télécharger PDF**).

### Passer une facture en irrécouvrable

1. Ouvrir la fiche facture.
2. Cliquer sur **Passer en irrécouvrable**.
3. Confirmer l'action.

La facture est marquée irrécouvrable. Elle disparaît des listes de factures impayées et une écriture comptable de perte peut être générée selon la configuration des règles.

### Archiver des factures payées

Depuis la liste des factures client, le bouton **Archiver la sélection** permet d'archiver en lot les factures déjà payées affichées après filtrage.

- Une facture **archivée** devient en lecture seule.
- Le bouton de téléchargement du document d'origine reste disponible si un fichier est attaché.
- L'archivage est irréversible depuis l'interface.

### Numérotation automatique

Le format de numérotation est configurable par l'administrateur (ex. `2026-001`, `F2026-0001`). La séquence est incrémentée automatiquement à chaque facture validée.

---

## 5. Paiements

### Workflow type : enregistrer un règlement client

1. Recevoir le règlement (virement, chèque, espèces).
2. Créer le paiement (**Nouveau paiement**) et le lier à la ou les factures concernées → le statut des factures se met à jour automatiquement.
3. Si le règlement est en **chèque ou espèces** : associer le paiement à une remise en banque (voir section Banque).

### Consulter les paiements

**Paiements** → liste des paiements reçus, filtrés par exercice.

### Encoder un paiement

1. Cliquer sur **Nouveau paiement**.
2. Sélectionner le **contact** (optionnel si la facture est connue).
3. Saisir le **montant** et la **date**.
4. Optionnel : lier le paiement à une ou plusieurs factures existantes (section **Factures liées**). Si non lié, la facture reste au statut *Validée*.
5. Saisir la référence (numéro de virement, de chèque, etc.).
6. Cliquer sur **Enregistrer**.

### Règlement en espèces : le montant est à saisir

Quand on enregistre un règlement depuis une **fiche facture** ou depuis la **facture rapide**, le montant est proposé d'office : c'est le solde restant dû. Pratique pour un chèque, dont le montant est écrit dessus — mais risqué pour les **espèces**, où rien d'autre que le comptage ne dit ce qui a été reçu.

Aussi, dès que le mode **Espèces** est choisi, le champ **Montant** se vide : il faut y saisir ce qui a réellement été compté. Deux repères sont affichés juste en dessous :

- un bouton **Reporter le solde dû (X €)** — à utiliser quand le montant compté correspond bien au solde de la facture ;
- l'effet sur la caisse : **Caisse après ce règlement : … → …**, pour rapprocher la saisie de l'argent qu'on a sous les yeux.

Repasser en **Chèque** repropose automatiquement le solde dû.

> Cette précaution évite le cas typique où un montant erroné est enregistré d'un simple clic — par exemple une facture émise à 310 € réglée par 270 € en espèces : sans elle, la caisse théorique et la caisse réelle divergent, et l'écart n'apparaît qu'au comptage suivant.

> **Astuce** : si une facture reste affichée comme impayée après l'enregistrement d'un paiement, vérifier que la facture est bien sélectionnée dans la section **Factures liées** du paiement.

### Annuler un règlement saisi par erreur

Un règlement enregistré ne se modifie plus (montant, date et mode sont figés) : en cas d'erreur de saisie, on **annule** le règlement puis on ressaisit le ou les bons.

**Qui** : cette opération est réservée à l'**administrateur**.

**Jusqu'à quand** : tant que l'argent n'est **pas arrivé sur le compte bancaire**. Concrètement :

- un **chèque** reçu d'un client reste annulable tant que sa remise n'a pas été confirmée ;
- un règlement en **espèces** reste annulable : l'argent est en caisse, pas à la banque. L'annulation retire aussi le mouvement de caisse correspondant, et le solde de caisse est recalculé.

En revanche, un virement reçu, un règlement déjà rapproché avec une opération bancaire ou appartenant à un exercice clôturé ne peuvent plus être annulés — dans ces cas, il faut passer par une écriture comptable de correction.

**Comment** :

1. Aller dans **Paiements** et retrouver la ligne concernée.
2. Ouvrir le menu **⋯** de la ligne, puis **Annuler ce règlement**.
3. Une fenêtre récapitule ce qui va se passer : le montant supprimé et, si le chèque figure déjà dans un bordereau de remise, l'effet sur ce bordereau — son total est recalculé, ou le bordereau est supprimé s'il ne contenait que ce chèque. Si l'annulation est impossible, la fenêtre en indique la raison.
4. Confirmer. Le règlement et ses écritures comptables sont supprimés, et la facture repasse en attente de règlement.
5. Ressaisir le ou les règlements corrects, puis reconstituer la remise en banque si nécessaire.

> **Exemple** : une famille règle une facture avec deux chèques, saisis par erreur comme un seul règlement. Tant que la remise n'est pas confirmée, l'administrateur annule le règlement unique, puis deux règlements sont saisis, un par chèque.

### Remises en banque

Un paiement par chèque ou espèces peut être associé à une remise en banque :
1. Créer le paiement.
2. Dans l'onglet **Remises en banque**, associer le paiement à une remise existante ou créer une nouvelle remise.

---

## 6. Factures fournisseurs

### Créer une facture fournisseur

1. Aller dans **Factures → Fournisseurs**.
2. Cliquer sur **Nouvelle facture fournisseur**.
3. Renseigner le fournisseur (contact ou nom libre), la date, le montant total.
4. Optionnel : joindre le fichier PDF de la facture reçue.
5. Cliquer sur **Enregistrer**.

### Valider et payer une facture fournisseur

La procédure est similaire aux factures clients : la facture fournisseur est validée puis associée à un ou plusieurs paiements.

---

## 7. Caisse

### Consulter les mouvements de caisse

**Caisse** → liste des entrées et sorties de la caisse physique.

### Enregistrer un mouvement

1. Cliquer sur **Nouveau mouvement**.
2. Indiquer la **date**, le **montant** (positif = entrée, négatif = sortie), la **description**.
3. Optionnel : lier à un contact.
4. Cliquer sur **Enregistrer**.

### Comptage de caisse

Le comptage de caisse permet de vérifier que le solde théorique correspond au solde réel.

1. Cliquer sur **Comptage**.
2. Saisir le montant réel compté.
3. L'écart est calculé automatiquement et affiché.
4. Valider le comptage pour l'enregistrer.

### Supprimer un mouvement

Un mouvement de caisse peut être supprimé s'il n'est associé à aucune écriture comptable validée.

---

## 8. Banque

### Workflow type : traiter un relevé bancaire mensuel

1. **Importer** le fichier OFX exporté depuis votre banque.
2. **Vérifier les catégories** détectées automatiquement sur chaque transaction ; les corriger si besoin (icône crayon dans la colonne Catégorie).
3. **Rapprocher** chaque transaction avec le paiement ou la remise en banque correspondant — soit ligne par ligne, soit en masse.
4. Vérifier que le **solde** affiché dans Solde correspond au relevé papier.

---

### Consulter les transactions

**Banque** → liste des transactions du compte bancaire. Filtrables par période, statut (rapprochées / non rapprochées), catégorie.

La colonne **Référence** affiche la référence comptable (numéro de facture ou de remise) quand la transaction est rapprochée.

### Importer des transactions (OFX)

1. Cliquer sur **Importer**.
2. Sélectionner le fichier OFX exporté depuis votre banque.
3. Confirmer l'import.

Les transactions déjà présentes (même référence bancaire) sont automatiquement ignorées — aucun doublon n'est créé.

> Seuls les fichiers OFX contenant **un seul compte** sont acceptés. Si votre fichier contient plusieurs comptes, contactez votre administrateur.

#### Doublons probables

Cette détection automatique ne fonctionne que sur la **référence bancaire**. Une opération que vous avez saisie à la main n'en porte aucune : quand la banque apporte ensuite le même mouvement, rien ne peut les rapprocher, et vous vous retrouvez avec deux lignes pour un seul mouvement — le solde affiché s'écarte alors de celui de votre banque, sans rien pour vous alerter.

L'application compare donc aussi chaque opération importée à ce qui est déjà enregistré : **même compte, même montant, à trois jours près**. Quand elle trouve une correspondance, la fenêtre d'import **reste ouverte** sur un panneau *Doublons probables* qui affiche les deux lignes côte à côte, avec un bouton **Supprimer** sur chacune.

L'application n'écarte jamais une ligne d'elle-même : les deux sont importées, et c'est vous qui décidez. Supprimez celle qui est en trop — en règle générale, gardez la ligne venue du relevé, qui porte la référence et le libellé de la banque — ou laissez les deux s'il s'agit bien de deux mouvements distincts du même montant.

> Le bouton est grisé sur une ligne qui ne peut pas être supprimée : une opération **rapprochée** (il faut alors supprimer l'autre côté de la paire) ou une opération issue d'un **import Excel**.

### Supprimer une opération

Une opération peut être supprimée tant qu'elle n'est pas **rapprochée** : les opérations saisies à la main, et celles venues d'un import de relevé (OFX, CSV, QIF). Ouvrez le menu **…** de la ligne et choisissez **Supprimer l'opération**.

Restent protégées : les opérations **rapprochées** (leurs écritures comptables en dépendent) et les opérations issues d'un **import Excel** (l'annulation d'import a besoin d'elles). Une opération importée peut être supprimée, mais jamais **modifiée** — elle reflète ce que la banque a communiqué.

### Corriger la catégorie d'une transaction

Solde détecte automatiquement la catégorie de chaque transaction (frais bancaires, cotisation sociale, subvention, virement interne…). Pour corriger :

1. Cliquer sur l'icône **crayon** dans la colonne Catégorie de la transaction.
2. Sélectionner la catégorie correcte dans la liste déroulante.
3. Enregistrer.

La catégorie détermine les écritures comptables générées lors du rapprochement.

> **Catégorie « Sans écriture »** — Si une transaction doit apparaître sur le relevé bancaire mais ne doit générer aucune écriture comptable (par exemple un virement vers un compte extérieur à Solde), assigner la catégorie **Sans écriture**. Lors du rapprochement, aucune écriture ne sera créée, quelle que soit la configuration des règles.

### Rapprochement bancaire

Le rapprochement lie une transaction bancaire à un paiement ou une remise enregistrés dans Solde, et génère les écritures comptables correspondantes.

#### Rapprocher une transaction individuellement

1. Repérer la transaction dans la liste (filtrer sur « Non rapprochées » pour aller vite).
2. Cliquer sur le bouton **Rapprocher** dans la colonne Rapp.
3. Sélectionner le paiement ou la remise correspondant.
4. Confirmer.

La transaction passe en statut **Rapproché** (tag vert) et disparaît du filtre « Non rapprochées ».

#### Rapprocher en masse

Deux boutons de rapprochement en masse sont disponibles dans la barre d'outils :

- **Tout rapprocher** : rapproche automatiquement toutes les transactions chargées dans la liste selon les règles configurées.
- **Rapprocher avant…** : ouvre un sélecteur de date ; toutes les transactions antérieures à cette date sont rapprochées en masse.

> Le rapprochement en masse n'écrase pas les transactions déjà rapprochées.

### Remises en banque

Une remise en banque regroupe plusieurs paiements remis ensemble à la banque (lot de chèques, virements groupés).

1. Aller dans **Banque → Remises en banque**.
2. Cliquer sur **Nouvelle remise**.
3. Ajouter les paiements concernés.
4. Saisir la date de remise et le montant total.
5. Enregistrer.

**Confirmer la remise** (quand le bordereau part à la banque) crédite immédiatement le compte : une opération est ajoutée au journal bancaire, sans attendre le relevé. Si le relevé a déjà été importé et contient ce mouvement, l'application **reprend cette opération** au lieu d'en créer une seconde : elle la renomme du nom du bordereau et la marque rapprochée. Rien à nettoyer, et le solde ne monte jamais à tort. Cette opération porte **la date du bordereau**, celle à laquelle vous avez porté les chèques ou les espèces à la banque — et non la date du jour où vous confirmez, qui peut arriver plusieurs jours plus tard.

Quand vous importerez ensuite le relevé, la banque apportera ce même mouvement avec sa propre référence. L'application le **reconnaît et complète l'opération existante** au lieu d'en créer une seconde — le message de fin d'import indique combien de remises ont été rapprochées de cette façon. Vous n'avez donc rien à supprimer.

> Dans un cas ambigu — deux remises du même montant à quelques jours d'intervalle — l'application ne choisit pas à votre place : les deux lignes sont importées, à vous d'indiquer laquelle correspond (voir ci-dessous).

**Si le rapprochement automatique n'a pas eu lieu** (bordereau confirmé longtemps après le crédit, ou plusieurs remises du même montant), vous vous retrouvez avec deux lignes pour un seul mouvement. Ne supprimez rien : sur la ligne venue du relevé, ouvrez le menu **…** et choisissez **Rattacher à un bordereau enregistré**. Sélectionnez le bordereau concerné : les deux lignes n'en font plus qu'une, qui garde le nom du bordereau, prend la date et la référence de la banque, et est **rapprochée d'office** — la correspondance est établie, il n'y a plus rien à confirmer. La colonne *Réf. comptable* affiche alors le bordereau.

> Un bordereau **non confirmé** ne crée aucune opération : il n'y a donc rien à rattacher tant que vous ne l'avez pas confirmé. Le dialogue vous le signale et vous indique le bordereau en attente plutôt que de vous laisser sans explication.

---

## 9. Salaires et employés

### Workflow type : saisir les salaires du mois

1. Récupérer les bulletins de salaire du mois depuis la plateforme CEA (ou équivalent).
2. Pour chaque intervenant, **créer une fiche de salaire** (**Salaires → Fiches de salaire → Nouvelle fiche**).
3. Vérifier le **Net calculé** affiché en lecture seule — il doit correspondre au net figurant sur le bulletin. Tout écart signale une erreur de saisie.
4. Enregistrer — les écritures comptables sont générées automatiquement.
5. Consulter le **Récapitulatif mensuel** pour vérifier les totaux du mois (brut, net, cotisations, coût total).

---

### Gérer les employés

**Salaires → Employés** → liste des employés actifs. Le bouton **Afficher les inactifs** permet d'afficher également les employés désactivés.

Les colonnes (Nom, Prénom, E-mail, Téléphone, Statut) sont toutes **triables et filtrables** (cliquer sur l'icône de filtre dans chaque en-tête de colonne).

#### Créer un employé

1. Cliquer sur **Nouvel employé**.
2. Renseigner le **nom** (obligatoire), le prénom, l'e-mail, le téléphone, l'adresse et les notes.
3. Dans la section **Contrat** :
   - **Type de contrat** : CDI, CDD, ou aucun.
   - **Auto-entrepreneur** : activer ce toggle si l'intervenant facture en tant qu'auto-entrepreneur (il apparaîtra dans le récapitulatif coût de la main d'œuvre à la colonne AE).
   - Si CDI : renseigner le **brut de base mensuel** (optionnel) et les **heures mensuelles de base** (optionnel) — servent de référence mais ne pré-remplissent pas automatiquement les fiches.
   - Si CDD : renseigner le **taux horaire** (€/h) — utilisé pour le calcul automatique du brut dans les fiches de salaire.
4. Cliquer sur **Enregistrer**.

#### Désactiver / réactiver un employé

Un employé ne peut pas être supprimé s'il a des fiches de salaire. Utilisez le bouton **Désactiver** (icône interdiction) pour le masquer de la liste par défaut. Le bouton **Réactiver** (icône coche) permet de le remettre en service.

---

### Fiches de salaire

**Salaires → Fiches de salaire** → la page regroupe trois sections :

1. **Liste des fiches** — le tableau principal des fiches du mois ou de la période sélectionnée.
2. **Récapitulatif mensuel** — total des salaires par mois (nombre de fiches, brut total, cotisations patronales totales, net total, coût total).
3. **Coût de la main d'œuvre** — synthèse mensuelle par type de contrat (CDI, CDD, auto-entrepreneurs) avec filtrage par période.

En haut de page, quatre indicateurs affichent en temps réel le nombre de fiches affichées, le brut total, le net total et le coût total employeur.

#### Filtrer la liste des fiches

- **Filtre employé** : sélectionner un employé dans le menu déroulant.
- **Filtre mois** : saisir une période au format `YYYY-MM` (ex. `2026-04`).
- **Recherche libre** : filtre sur toutes les colonnes visibles.
- Les colonnes Employé, Mois, Heures, Brut, Net à payer, Coût total sont **triables** et disposent chacune d'un **filtre par colonne** (cliquer sur l'icône de filtre dans l'en-tête).

#### Créer une fiche de salaire

Les données à saisir proviennent de la fiche de paie éditée par la plateforme CEA (ou équivalent).

1. Cliquer sur **Nouvelle fiche de salaire**.
2. Sélectionner l'**employé** dans la liste déroulante.
3. Saisir la **période** au format `YYYY-MM` (ex. `2026-04`).
4. **Section Brut** :
   - **Pour un employé en CDD** : saisir les **heures travaillées** — le brut déclaré (heures × taux horaire), les congés payés (10 %) et l'indemnité de précarité (10 %) sont calculés automatiquement. Le brut total est affiché en lecture seule.
   - **Pour un employé en CDI** : saisir les **heures travaillées** et le **salaire brut** manuellement.
5. **Section CEA** (données issues du bulletin de salaire) :
   - **Cotisations salariales** : retenues sur le brut à la charge de l'employé.
   - **Cotisations patronales** : charges sociales à la charge de l'employeur.
   - **Prélèvement à la source** : impôt retenu à la source.
   - **Net à payer** : montant net versé à l'employé (tel qu'il figure sur le bulletin).
   - Un champ **Net calculé** (lecture seule) affiche `brut − cotisations salariales − prélèvement à la source` pour vérification.
6. Optionnel : saisir des **notes** libres.
7. Bouton **Copier la fiche précédente** : pré-remplit les cotisations (salariales, patronales, PAS) à partir de la dernière fiche enregistrée pour cet employé, pour gagner du temps entre deux mois similaires.
8. Cliquer sur **Enregistrer**.

Une fiche de salaire enregistrée génère automatiquement les écritures comptables correspondantes selon les règles configurées.

#### Modifier ou supprimer une fiche

- **Modifier** : cliquer sur l'icône crayon dans la colonne Actions.
- **Supprimer** : cliquer sur l'icône corbeille, puis confirmer. La suppression annule les écritures comptables associées.

---

## 10. Comptabilité

*Disponible pour les rôles Comptable et Administrateur.*

### Journal comptable

**Comptabilité → Journal** → liste des écritures comptables, filtrées par exercice.

Les écritures peuvent être générées automatiquement (depuis les factures, paiements, caisse, banque, salaires) ou saisies manuellement.

#### Créer une écriture manuelle

1. Cliquer sur **Nouvelle écriture**.
2. Saisir la date, le libellé, les lignes de débit et crédit.
3. L'écriture doit être équilibrée (total débit = total crédit).
4. Enregistrer.

### Plan comptable

**Comptabilité → Plan comptable** → liste de tous les comptes.

#### Créer un compte

1. Cliquer sur **Nouveau compte**.
2. Saisir le numéro de compte (ex. `707000`), le libellé, le type.
3. Enregistrer.

### Règles comptables

Les règles comptables automatisent la génération des écritures lors de la création ou validation de factures, paiements, etc.

**Comptabilité → Règles** → liste des règles actives.

#### Créer une règle

1. Cliquer sur **Nouvelle règle**.
2. Définir le déclencheur (type d'objet et événement).
3. Définir les lignes de débit et crédit générées automatiquement.
4. Enregistrer.

### Grand livre

**Comptabilité → Grand livre** → solde de chaque compte avec le détail des mouvements.

Filtrer par compte, période, exercice.

### Bilan et compte de résultat

**Comptabilité → Bilan** → vue synthétique des actifs et passifs. Les deux colonnes se lisent en positif et leurs totaux doivent être égaux.

**Comptabilité → Résultat** → recettes vs dépenses sur l'exercice.

### Archiver le bilan et le compte de résultat

Chaque écran propose trois exports, pour l'exercice sélectionné :

| Bouton | Usage |
|---|---|
| **Exporter PDF** | Document mis en page, en-tête de l'association et date d'édition — c'est celui à ranger dans les archives comptables ou à transmettre. |
| **Exporter CSV** | Données brutes séparées par des points-virgules. |
| **Exporter Excel** | Le tableau tel qu'il est affiché à l'écran. |

Le PDF indique si l'exercice est **clôturé** ou **en cours**, et prend le nom de l'exercice comme nom de fichier (par exemple `bilan_2025.pdf`).

> Sur un exercice clôturé, le bilan n'affiche plus de ligne « résultat de l'exercice » séparée : le résultat a été affecté aux comptes 120000 (excédent) ou 129000 (déficit), qui figurent au passif. Le compte de résultat, lui, continue d'afficher le détail des charges et des produits de l'exercice.

---

## 11. Exercices comptables

**Comptabilité → Exercices** ou **Paramètres → Exercices**.

### Créer un exercice

1. Cliquer sur **Nouvel exercice**.
2. Saisir le nom, la date de début et la date de fin.
3. Enregistrer.

### Clôturer un exercice

La clôture est irréversible. N'effectuez cette opération que lorsque toutes les écritures de la période sont finalisées.

1. Sur la ligne de l'exercice, cliquer sur **Clôturer l'exercice**.
2. La fenêtre affiche d'abord les **vérifications avant clôture** : balance débit/crédit et écritures sans exercice associé. Ces avertissements ne bloquent pas la clôture, mais ce qu'ils signalent sera figé — traitez-les d'abord.
3. Confirmer.

L'exercice passe à l'état **Clôturé**, et une écriture de résultat est générée automatiquement (compte 120000 en cas d'excédent, 129000 en cas de déficit).

### Passer à l'exercice suivant

> **Important** : ne créez pas le nouvel exercice avec **Nouvel exercice**. Ce bouton crée une période vide, **sans reprise des soldes** : banque, caisse, créances clients et dettes fournisseurs repartiraient à zéro.

Une fois l'exercice précédent clôturé, sa ligne propose **Ouvrir le prochain exercice**. C'est cette action qui génère les **reports à nouveau** — le solde de chaque compte de bilan est repris à l'ouverture du nouvel exercice.

1. Sur la ligne de l'exercice clôturé, cliquer sur **Ouvrir le prochain exercice**.
2. Le nom et les dates sont pré-remplis dans la continuité : le nouvel exercice commence le lendemain de la fin du précédent et couvre douze mois. Ajuster si besoin.
3. Cliquer sur **Créer l'exercice et reporter les soldes**.

Le bouton n'apparaît plus dès qu'un exercice postérieur existe, pour éviter les doublons. Deux exercices ne peuvent pas se chevaucher : la création est refusée si les dates empiètent sur une période existante.

### Ordre à respecter en fin d'exercice

1. Terminer la saisie du dernier mois (factures, règlements, remises en banque, salaires).
2. Vérifier qu'aucun règlement en attente ne traîne : un règlement saisi **après** la fin de l'exercice mais avant la création du nouveau se retrouve **sans exercice** et n'apparaît plus dans les écrans filtrés par exercice. Si c'est déjà arrivé, l'administrateur peut annuler ces règlements (voir *Annuler un règlement saisi par erreur*) et les ressaisir une fois le nouvel exercice ouvert.
3. Clôturer l'exercice.
4. Ouvrir le prochain exercice depuis la ligne de l'exercice clôturé.
5. Sélectionner le nouvel exercice dans le sélecteur en haut de l'application pour retrouver les écrans à jour.

---

## 11 bis. Séance de comptabilité (checklist mensuelle)

La tenue mensuelle enchaîne une vingtaine de gestes répartis sur quatre écrans, entrecoupés de passages sur le site de la paie et sur celui de la banque. La **séance de comptabilité** les réunit en une liste ordonnée que l'on coche au fur et à mesure, à la manière d'une checklist d'aéronautique : l'état est conservé, vous le retrouvez d'un poste à l'autre, et une séance interrompue reprend là où vous l'aviez laissée.

Le bouton se trouve dans le bandeau, présent sur **tous les écrans** : il affiche la progression (« 7 / 17 ») et ouvre la liste dans un **panneau latéral, à droite**. Ce panneau n'est pas bloquant : il peut rester ouvert pendant que vous travaillez dans l'application, et vous cochez au fil des gestes sans le fermer. Réservé au trésorier et à l'administrateur.

### Démarrer une séance

Le mois proposé dépend de la date : avant le 15, c'est le mois précédent ; à partir du 15, le mois en cours. Un mois déjà traité n'est jamais proposé deux fois. Vous pouvez corriger le mois avant de démarrer.

Une seule séance est ouverte à la fois : pour passer au mois suivant, il faut clôturer celle en cours.

### L'ordre des étapes

La liste suit un principe : **regrouper tout ce qui se fait dans l'application avant chaque sortie vers l'extérieur**, pour ne faire qu'un aller-retour par destination.

1. **Saisie** — factures fournisseurs reçues.
2. **Paies** — faire les paies sur la plateforme, puis saisir les fiches.
3. **Passage à la banque en ligne** — un seul : virements de salaires, virements fournisseurs, puis téléchargement du relevé.
4. **Relevé** — importer, vérifier les catégories, créer les règlements clients depuis les virements reçus, rapprocher, comparer le solde.
5. **Caisse** — encoder les règlements fournisseurs payés en espèces, enregistrer les mouvements divers, **puis** compter la caisse. Le comptage vient en dernier : compter avant d'avoir tout saisi reviendrait à comparer le tiroir à un total périmé.
6. **Bordereaux de remise** — bordereau d'espèces, bordereau de chèques. Ils se préparent dans l'écran **Banque**, pas dans l'écran Caisse ; le dépôt lui-même se fait plus tard.
7. **Clôture** — vérifier la sauvegarde, clôturer la séance.

Les étapes précédées d'une flèche **⇢** se font **hors de l'application** : rien ici ne peut les constater, c'est à vous de les cocher.

> Les virements lancés à l'étape 3 n'apparaîtront pas sur le relevé téléchargé dans la foulée : ils se rapprocheront à la séance suivante.

### Les indications sous les étapes

Certaines étapes affichent un fait observé : « Dernier import le 01/09/2026, 12 opérations enregistrées », « Chèques à remettre : 2, soit 234,00 € ». Ces indications **ne cochent rien** — elles vous aident à répondre, elles ne répondent pas à votre place. Une case cochée sans que vous ayez regardé n'aurait pas été vérifiée, et c'est précisément l'étape sautée qui coûte cher.

### Clôturer une séance

Le bouton **Clôturer la séance** affiche d'abord ce qui n'a pas été coché et demande confirmation. Une séance incomplète peut être clôturée : une étape qui ne dépend pas de vous — un chèque qu'on ne vous a pas remis — ne doit pas bloquer tout le mois. Les étapes laissées de côté sont **signalées sur la séance suivante**, avec la mention « En retard ».

Une séance clôturée ne peut plus être modifiée ; elle reste consultable.

---

## 12. Documents

**Accueil → Documents.** Un espace pour les pièces qui n'appartiennent à aucune facture : statuts, procès-verbaux d'assemblée générale, attestations d'assurance, conventions, bilans et comptes de résultat signés.

Tout le monde peut consulter et télécharger. Le dépôt, la modification et la suppression sont réservés aux gestionnaires, trésoriers et administrateurs.

### Déposer un document

1. Cliquer sur **Déposer un document**.
2. Choisir le fichier — PDF, image, Excel, Word, CSV, Markdown ou texte, **20 Mo maximum**.
3. Donner un **titre** : c'est lui qu'on lira dans la liste, pas le nom du fichier. Le titre se pré-remplit avec le nom du fichier, à corriger si besoin (« scan_0042 » ne se retrouve pas, « PV assemblée générale 2026 » si).
4. Facultatif : rattacher un **exercice**, poser des **étiquettes** séparées par des virgules, ajouter des **notes**.
5. Valider.

> Les étiquettes déjà utilisées sont rappelées sous le champ : les reprendre plutôt que d'en inventer une variante évite de se retrouver avec « AG » d'un côté et « assemblée générale » de l'autre. La casse et les espaces sont normalisés automatiquement.

### Consulter un document sans le télécharger

L'icône **œil** ouvre un aperçu dans l'application, pour les formats que le navigateur sait afficher :

| Format | Aperçu |
|---|---|
| PDF | Le document, dans une visionneuse intégrée |
| Images (JPEG, PNG, WebP) | L'image |
| Markdown (`.md`) | Le texte mis en forme — titres, listes, tableaux |
| Texte, CSV, JSON, XML | Le contenu brut |
| Word, Excel, archives | Pas d'aperçu — l'icône n'apparaît pas, seul le téléchargement est proposé |

Sur mobile, l'aperçu d'un PDF s'ouvre dans un onglet, les navigateurs mobiles l'affichant mal en fenêtre.

### Retrouver un document

Trois filtres se combinent : la **recherche** (titre, notes, nom de fichier), l'**exercice** — dont « Sans exercice » pour les pièces intemporelles comme les statuts — et l'**étiquette**.

### Modifier ou supprimer

Le crayon permet de corriger le titre, l'exercice, les étiquettes et les notes. **Le fichier lui-même ne se remplace pas** : pour une nouvelle version, déposer un nouveau document.

La corbeille supprime la fiche **et le fichier**, après confirmation. L'opération est définitive.

> **Sauvegarde** : les fichiers déposés vivent dans le volume de données, aux côtés des PDF de factures. La sauvegarde intégrée à l'application ne couvre que la base ; c'est la sauvegarde du NAS qui protège les fichiers.

---

## 13. Mon profil

### Modifier ses informations

1. Cliquer sur votre nom en haut à droite → **Mon profil**.
2. Modifier le prénom, nom ou adresse e-mail.
3. Enregistrer.

### Changer son mot de passe

1. Aller dans **Mon profil → Changer le mot de passe**.
2. Saisir le mot de passe actuel.
3. Saisir le nouveau mot de passe (deux fois).
4. Cliquer sur **Enregistrer**.

Le nouveau mot de passe doit respecter la politique : minimum 8 caractères, au moins une majuscule et un chiffre.

---

## 14. Paramètres (administrateur)

*Cette section est réservée aux utilisateurs ayant le rôle **Administrateur**.*

Les paramètres sont accessibles via le menu **Paramètres** dans la barre latérale.

### Association

Permet de renseigner les informations de l'association (nom, adresse, SIRET, numéro RNA, e-mail de contact) qui apparaissent sur les documents PDF (factures, fiches de salaire).

Le paramètre **Limite d'affichage par défaut** définit le nombre maximum d'éléments chargés par liste.

- Valeur recommandée : `500`.
- Valeur `0` : charge jusqu'au plafond API (5 000 éléments par requête).

### SMTP — Envoi d'e-mails

Permet de configurer le serveur d'envoi d'e-mails utilisé pour envoyer les factures par mail et les notifications.

- Hôte, port, identifiant et mot de passe du serveur SMTP.
- Option TLS.
- Un bouton **Tester** permet de vérifier la configuration avant de l'enregistrer.

> Sans configuration SMTP valide, l'envoi de factures par e-mail et les notifications automatiques (ex. échec de sauvegarde) sont désactivés.

### Sauvegarde automatique

Permet de programmer des sauvegardes automatiques de la base de données.

#### Activer et planifier les sauvegardes

1. Activer le toggle **Activer les sauvegardes automatiques**.
2. Choisir le mode de planification :
   - **Quotidien (heure fixe)** : saisir l'heure au format HH:MM (ex. `02:00` pour 2 h du matin chaque nuit).
   - **Toutes les N heures** : saisir l'intervalle souhaité (ex. toutes les 24 h).
   - **Expression cron** : saisir une expression cron personnalisée (ex. `0 2 * * *` pour chaque nuit à 2 h).
3. Cocher **Inclure les fichiers joints** pour inclure les pièces jointes (factures fournisseurs importées) dans la sauvegarde.
4. Cocher **Inclure tous les fichiers de sauvegarde précédents** pour envoyer l'intégralité du dossier de sauvegardes vers la destination. Si cette option est désactivée (comportement par défaut), seul le dernier snapshot est envoyé.
5. Cocher **Notifier en cas d'échec** pour recevoir un e-mail si une sauvegarde échoue (nécessite un SMTP configuré).
6. Cliquer sur **Enregistrer la planification**.

Le bouton **Lancer maintenant** déclenche une sauvegarde immédiate sans attendre l'heure planifiée.

> Le spinner de progression s'affiche dans les 10 secondes suivant le démarrage d'une sauvegarde automatique, même si la page était déjà ouverte au moment du déclenchement.

#### Statut du dernier enregistrement

Le panneau affiche la date, l'heure et le résultat (succès ou échec) de la dernière sauvegarde effectuée.

#### Destinations de sauvegarde

Les sauvegardes peuvent être envoyées vers une ou plusieurs destinations. Cliquer sur **Ajouter une destination** et choisir le type :

| Type | Description |
|---|---|
| **Local** | Dossier sur le serveur hébergeant l'application (chemin absolu). |
| **SMB (réseau)** | Partage réseau (NAS, serveur de fichiers) accessible via le protocole SMB. Renseigner l'hôte, le partage, l'identifiant et le mot de passe. |
| **OneDrive** | Compte Microsoft OneDrive. Cliquer sur **Autoriser OneDrive** et suivre la procédure d'authentification dans l'onglet qui s'ouvre. |

Chaque destination peut être **activée ou désactivée** individuellement. Le bouton **Tester** vérifie que la connexion à la destination est opérationnelle sans effectuer de sauvegarde.

#### Restauration

La liste des sauvegardes disponibles s'affiche en bas du panneau.

- **Tester la restauration** : vérifie l'intégrité du fichier de sauvegarde (contrôle SQLite + présence des tables attendues) sans toucher aux données en production. Un rapport s'affiche.
- **Restaurer** : remplace la base de données en production par la sauvegarde sélectionnée. Une confirmation est demandée. **Cette action est irréversible.**

> Il est conseillé de toujours **Tester la restauration** avant de lancer une restauration effective.

### Prix par défaut

Permet de définir les prix unitaires préremplis lors de la création de factures clients.

### Règles d'import OFX

Permet de configurer les règles de catégorisation automatique des transactions bancaires lors de l'import d'un relevé OFX.

### Utilisateurs

Permet de gérer les comptes utilisateurs : créer un compte, modifier le rôle, réinitialiser le mot de passe, désactiver un compte.

---

## 15. Guide par rôle — « Je veux… »

Ce guide recense les actions courantes par rôle et renvoie vers la section correspondante du manuel.

### Secrétaire

| Je veux… | Section |
|---|---|
| Me connecter ou changer mon mot de passe | [1. Connexion et mot de passe](#1-connexion-et-mot-de-passe) |
| Créer ou modifier un contact | [3. Contacts — Créer un contact](#créer-un-contact) |
| Voir l'historique d'un contact | [3. Contacts — Historique d'un contact](#historique-dun-contact) |
| Marquer un client comme indésirable | [3. Contacts — Marquer un client comme indésirable](#marquer-un-client-comme-indésirable) |
| Créer une facture client rapidement | [4. Factures clients — Créer une facture rapidement (wizard)](#créer-une-facture-rapidement-wizard) |
| Créer une facture client (formulaire complet) | [4. Factures clients — Créer une facture (formulaire complet)](#créer-une-facture-formulaire-complet) |
| Envoyer une facture par e-mail | [4. Factures clients — Envoyer une facture par e-mail](#envoyer-une-facture-par-e-mail) |
| Télécharger le PDF d'une facture | [4. Factures clients — Télécharger le PDF](#télécharger-le-pdf) |
| Modifier ou supprimer une facture | [4. Factures clients — Modifier une facture](#modifier-une-facture) |
| Créer un avoir (note de crédit) | [4. Factures clients](#4-factures-clients) |
| Modifier mon profil ou mon mot de passe | [13. Mon profil](#13-mon-profil) |

### Trésorier

| Je veux… | Section |
|---|---|
| Enregistrer un paiement client | [5. Paiements — Encoder un paiement](#encoder-un-paiement) |
| Préparer et confirmer une remise en banque (chèques ou espèces) | [5. Paiements — Remises en banque](#remises-en-banque) |
| Créer ou payer une facture fournisseur | [6. Factures fournisseurs](#6-factures-fournisseurs) |
| Enregistrer une entrée ou sortie de caisse | [7. Caisse — Enregistrer un mouvement](#enregistrer-un-mouvement) |
| Faire un comptage de caisse | [7. Caisse — Comptage de caisse](#comptage-de-caisse) |
| Importer un relevé bancaire (OFX) | [8. Banque — Importer des transactions (OFX)](#importer-des-transactions-ofx) |
| Corriger la catégorie d'une transaction | [8. Banque — Corriger la catégorie d'une transaction](#corriger-la-catégorie-dune-transaction) |
| Rapprocher des transactions bancaires | [8. Banque — Rapprochement bancaire](#rapprochement-bancaire) |
| Confirmer une remise en banque | [8. Banque — Remises en banque](#remises-en-banque-1) |
| Saisir une fiche de salaire | [9. Salaires et employés — Fiches de salaire](#fiches-de-salaire) |
| Consulter le journal comptable | [10. Comptabilité — Journal comptable](#journal-comptable) |
| Consulter le grand livre, le bilan ou le compte de résultat | [10. Comptabilité](#10-comptabilité) |
| Clôturer un exercice comptable | [11. Exercices comptables — Clôturer un exercice](#clôturer-un-exercice) |

### Administrateur

| Je veux… | Section |
|---|---|
| Gérer les employés | [9. Salaires et employés — Gérer les employés](#gérer-les-employés) |
| Configurer les règles comptables | [10. Comptabilité — Règles comptables](#règles-comptables) |
| Créer un exercice comptable | [11. Exercices comptables — Créer un exercice](#créer-un-exercice) |
| Configurer l'envoi d'e-mails (SMTP) | [13. Paramètres — SMTP](#smtp--envoi-de-mails) |
| Programmer des sauvegardes automatiques | [13. Paramètres — Sauvegarde automatique](#sauvegarde-automatique) |
| Ajouter une destination de sauvegarde | [13. Paramètres — Destinations de sauvegarde](#destinations-de-sauvegarde) |
| Restaurer une sauvegarde | [13. Paramètres — Restauration](#restauration) |
| Gérer les comptes utilisateurs | [13. Paramètres — Utilisateurs](#utilisateurs) |
| Toutes les actions Secrétaire et Trésorier | Voir les sections ci-dessus |
