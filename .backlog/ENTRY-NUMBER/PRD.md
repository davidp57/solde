# Lot ENTRY-NUMBER — Une seule façon honnête d'attribuer un numéro d'écriture

Status: ⬜ ready
Branch: fix/entry-number → PR → develop

## Problem Statement

L'unicité des numéros d'écriture est garantie par la base (index unique
`ix_accounting_entries_entry_number_unique`, migration 0052). Le code qui attribue ces
numéros, lui, dit autre chose que ce qu'il fait, et un de ses chemins se trompe.

1. **`next_entry_number` annonce une boucle de nouvelle tentative qui n'existe pas.**
   Sa docstring promet « a retry loop to handle IntegrityError from the UNIQUE constraint
   in case of concurrent requests ». En réalité la boucle `for attempt in
   range(_ENTRY_NUMBER_MAX_RETRIES)` renvoie le candidat dès `attempt == 0` : aucune
   `IntegrityError` n'est jamais attrapée, la branche de journalisation est inatteignable.
   Deux requêtes concurrentes qui lisent le même `max()` produisent le même numéro ; la
   seconde échoue au flush (refusée par l'index, donc pas de doublon en base) et remonte en
   **500** sans nouvelle tentative. Constat lors du lot SCHEMA-DRIFT (PR #169).
2. **L'import des écritures Excel calcule son numéro de départ sans filtrer les numéros
   non numériques.** `_import_entries.py` fait `max(entry_number)` sur toute la table, là où
   `next_entry_number` filtre par `GLOB '[0-9]{6}'`. Mesuré le 2026-10-02 sur la base locale
   (copie de dev) : `max()` brut = `SAL-2026-03-pay-08`, `max()` numérique = `002423`. Le
   `int()` échoue, le `except ValueError` remet le compteur à **1**, et `000001` existe
   déjà : un import Comptabilité sur cette base échouerait sur l'index unique. Non observé
   en prod (à confirmer), déduit du code et de la mesure.

## Solution

Un seul allocateur de numéros, dont la docstring décrit le comportement réel, utilisé par
tous les chemins d'écriture ; et décider explicitement de ce qui se passe en cas de
collision concurrente (voir TEC-258).

## User Stories

1. En tant que trésorier, je veux qu'un import Comptabilité sur une base qui contient déjà
   des écritures `SAL-…` ou `RUN-…` numérote à la suite des écritures existantes, pour que
   l'import aboutisse.
2. En tant que développeur, je veux que la docstring de l'allocateur décrive ce qu'il fait,
   pour ne pas croire à une protection qui n'existe pas.
3. En tant que trésorier, je veux qu'une double soumission concurrente produise soit une
   écriture correctement numérotée, soit un message clair, jamais une erreur 500 opaque.

## Implementation Decisions

- Une PR pour les deux tickets.
- Les migrations ne sont pas touchées : l'index de 0052 reste le garde-fou.

## Testing Decisions

- TEC-259 : test d'import d'écritures Excel sur une base contenant déjà une écriture de
  numéro non numérique (`SAL-…`) et une écriture numérique : les numéros importés suivent
  le plus grand numéro numérique. Rouge avant correctif.
- TEC-258 : selon l'option retenue, test de collision (deux allocations sur le même `max()`)
  qui vérifie la nouvelle tentative effective ou l'erreur métier.

## Out of Scope

- Renuméroter les écritures existantes.
