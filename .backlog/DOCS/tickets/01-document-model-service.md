# BIZ-240 — Modèle, migration et service de documents

Status: ✅ done
Type: feature
Files: `backend/models/document.py`, `backend/schemas/document.py`,
`backend/services/document_service.py`, `backend/alembic/versions/NNNN_add_documents.py`,
`tests/unit/test_document_service.py`

## What to build

- **Modèle** `Document` (table `documents`) :
  `id`, `title` (255, non nul), `filename` (255, non nul), `stored_path` (500, non nul),
  `mime_type` (100), `size_bytes` (int), `fiscal_year_id` (FK `fiscal_years.id`,
  nullable, `ondelete=SET NULL`), `tags` (JSON, défaut `[]`), `notes` (Text, nullable),
  `uploaded_at` (DateTime, `server_default=now()`), `uploaded_by` (100, nullable —
  identifiant de l'utilisateur déposant).
  Index sur `fiscal_year_id` et sur `uploaded_at`.
- **Migration Alembic** créant la table. Numérotation à la suite de la dernière révision.
- **Service** `document_service` :
  - `normalize_tags(raw: list[str]) -> list[str]` — minuscules, espaces réduits, vides
    écartés, doublons supprimés, ordre d'apparition conservé.
  - `store_document(db, *, title, filename, content, mime_type, fiscal_year_id, tags,
    notes, uploaded_by)` — valide le type, écrit le fichier sous
    `data/documents/<uuid>-<nom-assaini>`, persiste la ligne, renvoie le DTO.
  - `list_documents(db, *, fiscal_year_id, tag, search, limit, offset)` — tri par
    `uploaded_at` décroissant ; `search` porte sur titre, notes et nom de fichier.
  - `list_tags(db)` — étiquettes distinctes, triées, avec leur nombre d'occurrences.
  - `update_document(db, document_id, payload)` — titre, exercice, étiquettes, notes.
    Le fichier lui-même n'est pas remplaçable.
  - `delete_document(db, document_id)` — supprime la ligne **et** le fichier ; l'absence
    du fichier sur le disque ne doit pas faire échouer la suppression de la ligne.
  - `get_document_file(db, document_id)` — renvoie `(chemin, nom d'origine, mime)`.
- **Validation de type** dans un helper dédié : liste blanche vérifiée sur les octets
  d'en-tête (`%PDF`, `\xff\xd8\xff`, `\x89PNG`, `RIFF….WEBP`, `PK\x03\x04`,
  `\xd0\xcf\x11\xe0`) ; `.csv` et `.txt` acceptés sur extension si le contenu se décode.
  Type refusé → `DocumentTypeError`. Fichier vide → refus également.
- **Assainissement du nom** : caractères non alphanumériques (hors `-`, `_`, `.`)
  remplacés, longueur bornée, aucun séparateur de chemin ne doit survivre.

## Acceptance criteria

- [ ] Un PDF déposé crée la ligne et le fichier ; `stored_path` pointe un fichier
      existant sous `data/documents/`.
- [ ] Deux dépôts du même nom de fichier produisent deux fichiers distincts.
- [ ] Un nom de fichier contenant `../` ou un séparateur de chemin ne peut pas écrire
      hors de `data/documents/`.
- [ ] Un fichier dont l'extension est autorisée mais dont l'en-tête ne correspond pas
      (un exécutable renommé `.pdf`) est refusé, et **aucun fichier n'est écrit**.
- [ ] Un fichier vide est refusé.
- [ ] `normalize_tags(["AG", "ag", " Assemblée  Générale ", ""])` renvoie
      `["ag", "assemblée générale"]`.
- [ ] `list_documents` filtre par exercice, par étiquette et par recherche textuelle ;
      les documents sans exercice ressortent quand aucun filtre d'exercice n'est posé.
- [ ] `list_tags` renvoie les étiquettes distinctes avec leur nombre d'occurrences.
- [ ] La suppression retire la ligne et le fichier ; si le fichier a déjà disparu du
      disque, la ligne est tout de même supprimée.
- [ ] La suppression d'un exercice met `fiscal_year_id` à NULL sans supprimer le
      document.

## Blocked by

None — socle du lot.
