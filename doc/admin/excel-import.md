# Import Excel — Solde ⚖️

---

## Français

### Vue d'ensemble

L'import Excel permet de reprendre des données historiques depuis les classeurs Excel utilisés avant la migration vers Solde. C'est une fonctionnalité réservée aux **administrateurs**.

Solde reconnaît deux types de classeurs :

| Type | Contenu traité | Usage |
|---|---|---|
| **Gestion** | Contacts, factures, paiements, caisse, banque, écritures comptables générées | Reprise de la gestion courante historique |
| **Comptabilité** | Journal comptable uniquement | Reprise des écritures saisies directement dans Excel |

---

### Structure attendue des fichiers Excel

#### Classeur Gestion (`Gestion AAAA.xlsx`)

| Feuille | Colonnes clés | Notes |
|---|---|---|
| `Contacts` | `Nom`, `Prénom` (opt.), `Email` (opt.) | Créée si absente de la base |
| `Factures` | Date, client, montant, numéro (opt.) | Le numéro est généré si absent |
| `Paiements` | Montant, référence facture (opt.), contact (opt.) | La référence doit correspondre à une facture connue |
| `Caisse` | Date, montant | Les lignes de bilan d'ouverture ou non datées sont ignorées |
| `Banque` | Date, montant | Les lignes descriptives sans mouvement sont ignorées |

**Colonnes ignorées :** feuilles de reporting (`Grand Livre`, `Balance`, `Bilan`), `Journal (saisie)`, lignes de totaux.

**Lignes bloquantes :**
- Nom de contact manquant
- Montant invalide, nul ou absent
- Date invalide ou absente
- Paiement sans correspondance facture identifiable

**Cas ambigus bloquants :**
- Plusieurs contacts correspondent exactement au même nom normalisé
- Plusieurs factures candidates pour un même paiement

#### Classeur Comptabilité (`Comptabilite AAAA.xlsx`)

| Feuille | Colonnes clés | Notes |
|---|---|---|
| `Journal` | Date, compte, libellé, débit, crédit | Feuilles de reporting ignorées |

**Lignes ignorées :**
- Lignes où débit et crédit sont tous les deux nuls
- Doublons exacts déjà présents en base (même date, compte, libellé normalisé, débit, crédit)
- Réimport exact d'un fichier déjà importé avec succès (safeguard par hash)

---

### Prérequis avant import

Avant tout import historique, vérifier et préparer dans l'ordre :

1. **Sauvegarder la base de données** (voir [administration.md](./administration.md)).
2. **Créer les exercices comptables** couvrant toutes les dates présentes dans les fichiers.
   - Exemple : si les fichiers couvrent 2022 à 2026, créer les 5 exercices correspondants.
   - L'import ne crée pas les exercices automatiquement.
3. **Importer ou créer le plan comptable** (l'import Excel ne crée pas les comptes).
4. **Créer les règles comptables** si le classeur Gestion doit générer des écritures automatiques.
5. **Vérifier que le fichier source n'a pas été modifié** depuis le dernier essai (le mécanisme de hash détecte les réimports exacts).

---

### Ordre d'import recommandé

```
Gestion 2022.xlsx   ← en premier si disponible
Gestion 2023.xlsx
Gestion 2024.xlsx
Gestion 2025.xlsx
Comptabilite 2024.xlsx   ← après le Gestion de la même année
Comptabilite 2025.xlsx
```

**Règles :**
- Toujours importer les fichiers Gestion dans l'ordre chronologique.
- Importer Comptabilité **après** le Gestion de la même année : les doublons exacts d'écritures déjà générées par Gestion seront automatiquement ignorés.
- Si des paiements d'une année N pointent vers des factures de l'année N-1, importer d'abord le Gestion N-1.

---

### Procédure d'import pas à pas

#### Étape 1 — Prévisualisation

La prévisualisation est **obligatoire** avant chaque import.

1. Aller dans **Administration → Import Excel**.
2. Sélectionner le type de fichier : **Gestion** ou **Comptabilité**.
3. Choisir le fichier Excel.
4. Cliquer sur **Prévisualiser**.
5. Analyser le résultat :
   - **Peut s'exécuter** : l'import est possible dans l'état actuel.
   - **Bloqué** : une ou plusieurs erreurs empêchent l'import — ne pas forcer.
6. Vérifier feuille par feuille :
   - Compteurs d'objets qui seront créés
   - Lignes ignorées (normales) et lignes bloquantes (à corriger)
   - Avertissements

**Si la prévisualisation est bloquée :** corriger le fichier source ou la stratégie d'import. Ne jamais lancer l'import sur un état bloqué.

#### Étape 2 — Exécution

Si la prévisualisation est verte :

1. Cliquer sur **Exécuter l'import**.
2. Attendre la fin de l'exécution.
3. Analyser le résumé : objets créés, lignes ignorées, lignes bloquantes, avertissements.

#### Étape 3 — Vérification post-import

1. Vérifier que les contacts, factures, paiements et mouvements attendus sont bien présents.
2. Contrôler que les écritures comptables sont rattachées aux bons exercices.
3. Pour un import Gestion, vérifier qu'aucune erreur comptable n'est signalée en avertissement.

---

### Historique d'import et annulation

Solde conserve un journal réversible de chaque import.

- **Annuler un import** : aller dans l'historique d'import, sélectionner le run et utiliser **Annuler** (`undo`).
- **Rejouer après annulation** : utiliser **Rejouer** (`redo`).

**Limites de l'annulation :**
- Si un objet créé par l'import a été modifié manuellement par la suite, l'annulation est bloquée pour éviter une incohérence.
- Dans ce cas, restaurer une sauvegarde de la base effectuée avant l'import.

---

### Reset sélectif

Le reset sélectif supprime les données importées depuis un fichier spécifique sans toucher au reste.

Il est disponible dans **Administration → Import Excel → Historique**.

Un reset sélectif identifie le périmètre à supprimer en cherchant si le nom de l'exercice comptable apparaît dans le nom du fichier importé. Vérifier que les exercices sont bien nommés avant d'utiliser cette fonctionnalité.

---

### Réinitialisation complète

La réinitialisation complète supprime **toutes** les données métier de la base (contacts, factures, paiements, écritures, etc.) mais conserve les paramètres, les utilisateurs et le plan comptable.

Elle est accessible dans **Paramètres → Zone de danger → Recréer le socle comptable**.

**À n'utiliser qu'en cas de rejeu complet** (tests ou reprise initiale). Cette action est irréversible sans restauration de sauvegarde.

---

### Règles de coexistence Gestion / Comptabilité

| Cas | Comportement |
|---|---|
| Fichier déjà importé (même hash) | Rejet automatique |
| Objet Gestion déjà présent en base | Ligne ignorée |
| Écriture comptable déjà présente (doublon exact) | Ligne ignorée |
| Correspondance ambiguë (plusieurs candidats) | Import bloqué |
| Écritures manuelles dans la période | Autorisées si pas de doublon exact |

---

### Résultats constatés sur les fichiers réels (référence)

| Fichier | Créés | Ignorés | Bloqués |
|---|---|---|---|
| Gestion 2024.xlsx | 64 contacts, 303 factures, 308 paiements, 1 222 écritures, 102 mouvements caisse, 210 transactions banque | 2 | 0 |
| Gestion 2025.xlsx | 18 contacts, 211 factures, 211 paiements, 844 écritures, 75 mouvements caisse, 145 transactions banque | 12 | 0 |
| Comptabilite 2024.xlsx | 1 367 écritures | 23 | 0 |
| Comptabilite 2025.xlsx | 928 écritures | 12 | 0 |

---

---

## English

### Overview

The Excel import feature allows importing historical data from Excel workbooks used before migrating to Solde. It is restricted to **administrators**.

Solde recognises two types of workbooks:

| Type | Processed content | Use |
|---|---|---|
| **Gestion** | Contacts, invoices, payments, cash, bank transactions, auto-generated accounting entries | Historical management data migration |
| **Comptabilite** | Accounting journal only | Historical journal entries migration |

---

### Expected Excel file structure

#### Gestion workbook

| Sheet | Key columns | Notes |
|---|---|---|
| `Contacts` | `Nom`, `Prénom` (opt.), `Email` (opt.) | Created if not already in the database |
| `Factures` | Date, client, amount, number (opt.) | Number is auto-generated if missing |
| `Paiements` | Amount, invoice reference (opt.), contact (opt.) | Reference must match a known invoice |
| `Caisse` | Date, amount | Opening balance or undated rows ignored |
| `Banque` | Date, amount | Descriptive rows without movement ignored |

**Blocking rows:** missing contact name, invalid/zero/missing amount, invalid/missing date, payment with no matchable invoice.

**Blocking ambiguities:** multiple contacts match the same normalized name; multiple invoice candidates for a payment.

#### Comptabilite workbook

| Sheet | Key columns | Notes |
|---|---|---|
| `Journal` | Date, account, label, debit, credit | Reporting sheets ignored |

**Ignored rows:** both debit and credit zero; exact duplicates already in the database; exact re-import of a previously imported file.

---

### Prerequisites

Before any historical import:

1. **Back up the database** (see [administration.md](./administration.md)).
2. **Create fiscal years** covering all dates in the files.
3. **Set up the chart of accounts** (the import does not create accounts).
4. **Create accounting rules** if the Gestion workbook should auto-generate entries.
5. **Do not modify the source file** between attempts (the hash safeguard detects exact re-imports).

---

### Recommended import order

```
Gestion 2022.xlsx
Gestion 2023.xlsx
Gestion 2024.xlsx
Gestion 2025.xlsx
Comptabilite 2024.xlsx   ← after the matching Gestion year
Comptabilite 2025.xlsx
```

---

### Step-by-step procedure

#### Step 1 — Preview

Preview is **mandatory** before every import.

1. Go to **Administration → Excel Import**.
2. Select the file type: **Gestion** or **Comptabilite**.
3. Choose the Excel file.
4. Click **Preview**.
5. Read the result:
   - **Can execute**: the import can proceed.
   - **Blocked**: one or more errors prevent the import — do not force it.
6. Review sheet by sheet: creation counters, ignored rows, blocking rows, warnings.

**If the preview is blocked:** fix the source file or the import strategy. Never run an import on a blocked state.

#### Step 2 — Execute

If the preview is green, click **Execute import** and wait for completion.

#### Step 3 — Post-import checks

1. Verify that the expected contacts, invoices, payments, and entries are present.
2. Confirm that accounting entries are attached to the correct fiscal years.
3. For a Gestion import, check that no accounting error is surfaced as a warning.

---

### Import history and undo

Solde keeps a reversible log for each import run.

- **Undo an import**: go to import history, select the run, and click **Undo**.
- **Redo after undo**: click **Redo**.

**Undo limitations:** if an imported object was subsequently modified through the application, undo is blocked to prevent inconsistency. In that case, restore a database backup taken before the import.
