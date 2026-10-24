# BIZ-259 — Signaler les doublons probables au retour d'un import bancaire

Status: ✅ done
Type: feature
Files: `backend/services/bank_service.py`, `backend/routers/bank_import.py`,
`backend/schemas/bank.py`, `frontend/src/api/bank.ts`,
`frontend/src/components/bank/BankImportStatementDialog.vue`,
`frontend/src/i18n/fr.ts`, `tests/integration/test_bank_api.py`, `CHANGELOG.md`

## What to build

Un import qui ramène une opération ressemblant à une opération déjà enregistrée doit le
**dire**. La dédup existante ne compare que les références bancaires, donc elle est
aveugle à une ligne saisie à la main.

- **Service** — `find_probable_duplicate(db, tx)` : renvoie la première opération de même
  compte et de même montant, dans une fenêtre de ± 3 jours
  (`_DUPLICATE_DATE_TOLERANCE`), **sans référence** et de **source différente**.
  Ces deux dernières conditions écartent le bruit : une ligne importée qui portait déjà
  une référence a été traitée en amont par la dédup, et comparer deux lignes de même
  source revient à suspecter le fichier.
- **Import** — dans `_import_rows`, la ligne est **importée** puis appariée. Le résultat
  d'import porte une liste `duplicates` de paires `{imported, existing}`
  (`BankImportDuplicate`). Le compte est journalisé et ajouté au détail d'audit des trois
  formats.
- **Frontend** — quand des doublons sont signalés, le dialogue d'import **reste ouvert**
  sur un panneau « Doublons probables » : chaque paire affiche ses deux lignes (date,
  libellé, montant, source) avec un bouton « Supprimer » par ligne, désactivé et
  expliqué quand la ligne n'est pas supprimable (rapprochée, ou import Excel). La paire
  quitte la liste dès qu'un côté est supprimé. Le toast de fin passe en avertissement et
  annonce le nombre de doublons. Toutes les chaînes via i18n.

## Acceptance criteria

- [x] Saisie manuelle + import du même mouvement (même date, même montant) → une paire
      signalée, la ligne importée est bien créée.
- [x] Écart de date de 2 jours → signalée ; de 11 jours → non signalée.
- [x] Montant différent → non signalée.
- [x] Réimport du même fichier → `skipped` par référence, aucune paire à arbitrer.
- [x] Une ligne signalée peut être supprimée immédiatement.
- [x] Aucune ligne n'est écartée automatiquement au titre d'un doublon probable.

## Blocked by

BIZ-258 — la suppression proposée dans le panneau en dépend.
