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
