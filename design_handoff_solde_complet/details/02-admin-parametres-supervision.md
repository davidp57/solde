# Handoff — Admin Solde : Paramètres + Supervision système (mode sombre)

## Overview
Ce paquet étend le lot « Refonte UI/UX » (RF) aux **deux derniers écrans d'administration** de **Solde** (Vue 3 `<script setup>` + PrimeVue thème Aura + Pinia), qui avaient accumulé des panneaux « truc après truc » sans réorganisation.

**Décision d'architecture (déjà tranchée, à respecter)** : garder **2 écrans séparés** (Paramètres et Supervision système) — **ne pas les fusionner** — mais réorganiser chacun en **onglets internes**.

1. **Paramètres** — 5 panneaux empilés → **4 onglets** : Organisation · Comptabilité · Communication · Zone dangereuse.
2. **Supervision système** — flux vertical mélangé → **2 onglets** : État & surveillance vs Sauvegardes & restauration.

Nouveau motif transverse : la **ligne de réglage** (libellé + description courte + contrôle à droite) et une **barre d'enregistrement par section**.

## About the Design Files
`references/Solde - Admin (Parametres + Supervision).dc.html` est une **maquette de référence HTML** (prototype) en mode sombre — pas du code à copier. Ouvre-la dans un navigateur (CDN Manrope + PrimeIcons requis ; `support.js` = runtime du prototype, à ignorer).

La tâche est de **recréer ces intentions dans le codebase existant**, en **réutilisant impérativement** les composants maison et tokens (voir ci-dessous). Pas d'inline-styles : tout via tokens du thème.

## Fidelity
**Hi-fi**, mode sombre montré (la **parité clair/sombre est requise** — utiliser les tokens, pas les hex en dur). Reproduire la structure en onglets, le motif ligne de réglage et les barres d'enregistrement. Layout et hiérarchie définitifs.

## Réutiliser impérativement (pas de réinvention)
- **Composants maison** : `AppPage`, `AppPageHeader`, `AppPanel`, `AppWorklist` (file d'actions/anomalies), `AppFilterSegments`/segments, `AppStatCard`, `AppMobileCardList`, `AppDatePicker`.
- **Composants PrimeVue déjà en place** : `InputText`, `InputNumber` (`show-buttons`), `Textarea`, `Select`, `Password` (`toggle-mask`), `ToggleSwitch`, `Tag`, `Button`, `Message`, `ConfirmDialog` + `useConfirm`.
- **Tokens du thème** (clair/sombre), **Manrope**, **emerald**, rayons **16/12 px**.
- **UI strings en FR via i18n** (`i18n/fr.ts`) — les clés `settings.*` existent déjà (réutiliser).

## Déjà fait — à CONSERVER, ne pas redéfaire
Sur **Supervision** : le **bandeau d'état** (Opérationnel + version / taille BDD / démarré le), la **file d'anomalies** `AppWorklist`, et la **restauration sécurisée** par saisie de « RESTAURER ». Ces éléments sont repris à l'identique dans la maquette.

---

## Fichiers du codebase concernés
Relatifs à `frontend/src/` du repo `davidp57/solde` :

| Sujet | Fichier(s) |
|---|---|
| Coquille Paramètres | `views/SettingsView.vue` *(passe d'un empilement de 5 panels à un conteneur d'onglets)* |
| Panneaux Paramètres existants | `components/settings/SettingsAssociationPanel.vue`, `SettingsSmtpPanel.vue`, `SettingsSystemOpeningPanel.vue`, `SettingsChatPanel.vue`, `SettingsDangerZonePanel.vue`, `SettingsBackupPanel.vue` *(à re-répartir dans les onglets)* |
| Supervision | `views/SystemView.vue` |
| **Nouveau** motif réglage | `components/ui/AppSettingRow.vue` *(à créer)* |
| **Nouveau** conteneur d'onglets | `components/ui/AppTabbedPage.vue` ou PrimeVue `Tabs` *(au choix)* |
| i18n | `i18n/fr.ts` *(clés `settings.*` existantes + nouvelles clés d'onglet)* |

---

## Écran 1 — Paramètres

**Constat** : 5 gros panneaux empilés (`SettingsView.vue` rend `Association` → `Smtp` → `SystemOpening` → `Chat` → `DangerZone`) → scroll interminable, aucun regroupement logique.

**Cible** : conteneur d'onglets internes (PrimeVue `Tabs`/`TabPanel` ou `AppTabbedPage`), **chaque onglet portant sa propre barre d'enregistrement collante**.

### Onglet « Organisation »
Depuis `SettingsAssociationPanel` (partie identité + paiement) :
- **Panel Identité** : Nom de l'association (`association_name`), SIRET (`association_siret`), Adresse (`association_address`, `Textarea`).
- **Panel Coordonnées de paiement** : IBAN (`payment_iban`), BIC (`payment_bic`), Ordre des chèques (`payment_check_payee`).

### Onglet « Comptabilité »
Regroupe numérotation + ouverture + tarifs :
- **Panel Numérotation des pièces** : modèle n° facture client (`client_invoice_number_template`, **avec aperçu résolu en direct** → `2024-013`), chiffres séquence (`client_invoice_seq_digits`, `InputNumber show-buttons`, **avertissement inline** « impacte la numérotation future »), modèle n° facture fournisseur (`supplier_invoice_number_template`), modèle n° chèque (`cheque_number_template`). Champs de template en police mono.
- **Panel Exercice & ouverture** : mois de début d'exercice (`fiscal_year_start_month`, `Select`), délai de paiement par défaut (`default_invoice_due_days`). Puis **soldes d'ouverture** = les 2 cartes de `SettingsSystemOpeningPanel` (Banque / Caisse, chacune date `AppDatePicker` + montant `InputNumber` + `Tag` Configuré/À configurer).
- **Panel Tarifs par défaut** : Cours / Adhésion / Autres (`default_price_*`).

### Onglet « Communication »
Fusionne SMTP + modèles + Chat :
- **Panel Serveur SMTP** (`SettingsSmtpPanel`) : hôte, port, utilisateur, mot de passe (`Password`), expéditeur, BCC, `ToggleSwitch` TLS.
- **Panel Modèles d'e-mail** : sujet (`email_subject_template`) + corps (`email_body_template`, `Textarea auto-resize`) + aide sur les variables `{invoice_number} {description} {association_name} {invoice_ref}`.
- **Panel Assistant IA** (`SettingsChatPanel`) : fournisseur (`Select` gemini/openai), modèle, clé API (`Password`) avec état configuré/non configuré.

### Onglet « Zone dangereuse »
`SettingsDangerZonePanel` isolé dans son propre onglet (en-tête rouge déjà géré par `danger-panel`) : Bootstrap comptabilité, Réinitialiser la base, et Réinitialisation sélective (type + exercice + aperçu). Tous les `ConfirmDialog` conservés.

### Motif « ligne de réglage » (`AppSettingRow`)
```
AppSettingRow
  props: label, description?, warning?, htmlFor?
  slot: #control  (le contrôle PrimeVue)
  desktop : flex row, label/description à gauche (max ~46ch), contrôle aligné à droite (largeur fixe ~160–300px)
  mobile  : flex column, contrôle pleine largeur sous le libellé
  séparateur : border-bottom subtil entre lignes
```

### Barre d'enregistrement par section
Collante en bas de l'onglet (`position: sticky; bottom: 0`), avec **état** : « modifications non enregistrées » (point ambre) / « à jour » (✓ vert), boutons Annuler + Enregistrer (désactivés si pas de changement). Chaque onglet sauvegarde **sa** portion via l'`updateSettingsApi` existant.

---

## Écran 2 — Supervision système (`SystemView.vue`)

**Constat** : 3 préoccupations mélangées dans un flux vertical — configuration (backup auto), surveillance (statut, anomalies, logs, audit), maintenance (sauvegardes/restauration).

**Cible** : 2 onglets internes.

### Onglet « État & surveillance »
- **Bandeau d'état** (CONSERVÉ) : Opérationnel + version / taille BDD / démarré le.
- **File d'anomalies** `AppWorklist` (CONSERVÉ) : « chèques sans date de dépôt » + compteur + action Corriger.
- **Journaux applicatifs** : terminal mono (fond `#060c18` même en clair), filtres INFO/WARN/ERROR colorés, `overflow-x:auto`.
- **Journal d'audit** : table Horodatage / Acteur / Action / Cible.

### Onglet « Sauvegardes & restauration »
Depuis `SettingsBackupPanel` + la partie restauration de `SystemView` :
- **Panel Sauvegarde automatique** (config **sortie du flux de surveillance**) : `ToggleSwitch` planifiée, fréquence (`Select`), heure, rétention — en lignes de réglage.
- **Panel Sauvegardes disponibles** : table (Fichier mono, Libellé, Taille, Date) + libellé + « Télécharger maintenant » + par ligne : Valider / Restaurer.
- **Panel Restauration** (CONSERVÉ, en-tête danger rouge) : saisie obligatoire de **RESTAURER** pour activer le bouton ; sauvegarde auto de l'état courant avant l'opération.

---

## Responsive (parité)
- **Onglets internes** → chips **scrollables** horizontalement (`overflow-x:auto`, `flex:none`).
- **Panneaux** → **sections repliables** (accordéon) sur mobile, une ouverte à la fois.
- **Ligne de réglage** → bascule `flex-direction: row → column` sous le breakpoint (contrôle pleine largeur).
- **Barre d'enregistrement** collée en bas ; cibles **≥ 44px**.
- Cartes d'ouverture banque/caisse → **empilées** (déjà géré en `@media (max-width:767px)` dans `SettingsSystemOpeningPanel`).

## Design Tokens (rappel)
Mode sombre (Aura dark) : fond `#020617`, panneau `#0e1a30`→`#13203a`, carte interne `#0c1730`, bordure `#2a3a55`/`#1f2c44`, champ `#0b1424` bordure `#25344e`, texte `#f1f5f9`/`#94a3b8`, primaire **#34d399** (texte dessus `#04231a`), sémantiques `#4ade80`/`#fcd34d`/`#f87171`/`#60a5fa`. Danger : en-tête `rgba(239,68,68,.08)`, bordure `rgba(239,68,68,.25)`, titre `#f87171`. **Tout via tokens** — ces hex ne sont qu'une référence visuelle.

## Screenshots (`screenshots/`)
Les icônes « tofu » dans les captures sont un artefact d'export (PrimeIcons cross-origin) — réelles dans l'app.

| Fichier | Vue |
|---|---|
| `01-settings-organisation.png` | Paramètres — onglet Organisation + lignes de réglage |
| `02-settings-comptabilite.png` | Paramètres — onglet Comptabilité (numérotation + ouverture) |
| `03-supervision-surveillance.png` | Supervision — onglet État & surveillance |
| `04-supervision-sauvegardes.png` | Supervision — onglet Sauvegardes (backup auto + restauration) |
| `05-mobile-accordion.png` | Mobile — onglets scrollables + accordéon + barre d'enregistrement |

## Files
- `references/Solde - Admin (Parametres + Supervision).dc.html` — maquette des 2 écrans (4 vues desktop + mobile) + recommandations.
- `references/support.js` — runtime du prototype (ignorer).
