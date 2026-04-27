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
12. [Mon profil](#12-mon-profil)

---

## 1. Connexion et mot de passe

### Se connecter

1. Ouvrir l'URL de l'application dans un navigateur.
2. Saisir l'identifiant et le mot de passe.
3. Cliquer sur **Se connecter**.

La session reste active 24 heures. Elle est stockée dans un cookie sécurisé — aucun stockage local des identifiants.

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
- **Raccourcis** : bouton **Nouvelle facture** accessible directement depuis le tableau de bord.

Cliquer sur une facture impayée dans le tableau de bord ouvre directement la fiche facture.

---

## 3. Contacts

### Consulter la liste des contacts

**Contacts** → la liste s'affiche avec nom, prénom, e-mail, et la dernière facture émise.

Utilisez la barre de recherche pour filtrer par nom ou e-mail.

### Créer un contact

1. Cliquer sur **Nouveau contact**.
2. Renseigner le **nom** (obligatoire), le prénom (optionnel) et l'e-mail (optionnel).
3. Optionnel : renseigner l'adresse, le téléphone, les notes.
4. Cliquer sur **Enregistrer**.

### Modifier un contact

1. Cliquer sur le contact dans la liste.
2. Modifier les champs souhaités.
3. Cliquer sur **Enregistrer**.

### Historique d'un contact

Sur la fiche contact, l'onglet **Historique** affiche toutes les factures et paiements liés à ce contact.

---

## 4. Factures clients

### Consulter la liste des factures

**Factures** → liste filtrée par exercice. Colonnes : numéro, contact, date, montant, montant payé, statut.

Statuts possibles :
- **Brouillon** : facture non validée.
- **Validée** : facture envoyée ou confirmée, en attente de paiement.
- **Payée** : entièrement réglée.
- **Partiellement payée** : un ou plusieurs paiements reçus, solde restant.
- **En retard** : échéance dépassée, non réglée.
- **Irrécouvrable** : passée en perte.

### Créer une facture

1. Cliquer sur **Nouvelle facture**.
2. Sélectionner le **contact** (obligatoire).
3. Renseigner la **date** (obligatoire).
4. La **date d'échéance** est calculée automatiquement d'après le délai par défaut configuré. Elle peut être modifiée manuellement.
5. Ajouter des **lignes de facturation** :
   - Choisir le type : **cours**, **adhésion**, **autre**.
   - Saisir la description, la quantité, le prix unitaire.
   - Le prix unitaire est pré-rempli d'après les prix par défaut configurés dans les paramètres.
6. Optionnel : ajouter un commentaire interne.
7. Cliquer sur **Enregistrer** pour sauvegarder en brouillon, ou **Valider** pour finaliser la facture.

> La numérotation est attribuée automatiquement à la validation.

### Modifier une facture

Une facture en **brouillon** peut être modifiée librement.

Une facture **validée** peut être modifiée dans certaines limites (ajout de notes, modification de l'échéance) mais ses lignes ne peuvent plus être changées.

### Supprimer une facture

Seules les factures en **brouillon** sans paiement associé peuvent être supprimées.

### Envoyer une facture par e-mail

1. Ouvrir la fiche facture.
2. Cliquer sur **Envoyer par e-mail**.
3. Vérifier l'adresse du destinataire (pré-remplie depuis le contact).
4. Optionnel : modifier l'objet et le corps du message.
5. Cliquer sur **Envoyer**.

Le PDF est joint automatiquement. Un envoi réussi est tracé dans l'historique de la facture.

> Pour que l'envoi fonctionne, le SMTP doit être configuré dans les paramètres (rôle administrateur).

### Télécharger le PDF

Sur la fiche facture, cliquer sur **Télécharger PDF**.

### Passer une facture en irrécouvrable

1. Ouvrir la fiche facture.
2. Cliquer sur **Passer en irrécouvrable**.
3. Confirmer l'action.

La facture est marquée irrécouvrable. Elle disparaît des listes de factures impayées et une écriture comptable de perte peut être générée selon la configuration des règles.

### Numérotation automatique

Le format de numérotation est configurable par l'administrateur (ex. `2026-001`, `F2026-0001`). La séquence est incrémentée automatiquement à chaque facture validée.

---

## 5. Paiements

### Consulter les paiements

**Paiements** → liste des paiements reçus, filtrés par exercice.

### Encoder un paiement

1. Cliquer sur **Nouveau paiement**.
2. Sélectionner le **contact** (optionnel si la facture est connue).
3. Saisir le **montant** et la **date**.
4. Optionnel : lier le paiement à une ou plusieurs factures existantes.
5. Saisir la référence (numéro de virement, de chèque, etc.).
6. Cliquer sur **Enregistrer**.

Si le paiement est lié à une facture, le statut de la facture est mis à jour automatiquement.

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

### Consulter les transactions

**Banque** → liste des transactions du compte bancaire.

### Importer des transactions

Les transactions bancaires peuvent être importées depuis un fichier OFX exporté depuis votre banque :

1. Cliquer sur **Importer**.
2. Sélectionner le fichier OFX.
3. Vérifier la prévisualisation.
4. Confirmer l'import.

Les doublons exacts sont automatiquement ignorés.

### Rapprochement bancaire

Le rapprochement permet de vérifier que les transactions bancaires correspondent aux paiements enregistrés dans Solde.

1. Aller dans l'onglet **Rapprochement**.
2. Cocher les transactions rapprochées avec les paiements correspondants.
3. Confirmer le rapprochement.

### Remises en banque

Une remise en banque regroupe plusieurs paiements remis ensemble à la banque (chèques, virements groupés).

1. Aller dans **Banque → Remises en banque**.
2. Cliquer sur **Nouvelle remise**.
3. Ajouter les paiements concernés.
4. Saisir la date de remise et le montant total.
5. Enregistrer.

---

## 9. Salaires et employés

### Gérer les employés

**Salaires → Employés** → liste des employés.

Pour créer un employé :
1. Cliquer sur **Nouvel employé**.
2. Renseigner le nom, le prénom, le numéro de sécurité sociale (optionnel), les données de contrat.
3. Enregistrer.

### Saisir une fiche de salaire

1. Aller dans **Salaires → Fiches de salaire**.
2. Cliquer sur **Nouvelle fiche de salaire**.
3. Sélectionner l'employé, la période (mois/année).
4. Saisir le salaire brut, les cotisations patronales, les cotisations salariales, le net à payer.
5. Enregistrer.

### Valider une fiche de salaire

Une fiche validée génère automatiquement les écritures comptables correspondantes (selon les règles configurées).

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

**Comptabilité → Bilan** → vue synthétique des actifs et passifs.

**Comptabilité → Résultat** → recettes vs dépenses sur l'exercice.

---

## 11. Exercices comptables

**Comptabilité → Exercices** ou **Paramètres → Exercices**.

### Créer un exercice

1. Cliquer sur **Nouvel exercice**.
2. Saisir le nom, la date de début et la date de fin.
3. Enregistrer.

### Clôturer un exercice

La clôture est irréversible. N'effectuez cette opération que lorsque toutes les écritures de la période sont finalisées.

1. Ouvrir la fiche de l'exercice.
2. Cliquer sur **Clôturer l'exercice**.
3. Confirmer.

Après clôture, l'exercice passe à l'état **Clôturé** et les écritures ne peuvent plus être modifiées.

---

## 12. Mon profil

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
