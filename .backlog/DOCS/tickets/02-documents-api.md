# BIZ-241 — API REST des documents

Status: ✅ done
Type: feature
Files: `backend/routers/document.py`, `backend/main.py`,
`tests/integration/test_documents_api.py`

## What to build

Routeur `documents`, monté sous `/api` :

| Méthode | Route | Rôle | Objet |
|---|---|---|---|
| `POST` | `/api/documents/` | secretaire+ | Dépôt `multipart/form-data` : `file`, `title`, `fiscal_year_id?`, `tags?` (CSV), `notes?` |
| `GET` | `/api/documents/` | connecté | Liste filtrée : `fiscal_year_id`, `tag`, `search`, `limit`, `offset` ; en-tête `X-Total-Count` |
| `GET` | `/api/documents/tags` | connecté | Étiquettes distinctes et leurs occurrences |
| `GET` | `/api/documents/{id}` | connecté | Métadonnées d'un document |
| `GET` | `/api/documents/{id}/download` | connecté | Le fichier, en pièce jointe |
| `PATCH` | `/api/documents/{id}` | secretaire+ | Titre, exercice, étiquettes, notes |
| `DELETE` | `/api/documents/{id}` | secretaire+ | Suppression, ligne et fichier |

- **Plafond de taille** : 20 Mo, refus en `413` avec le code `FILE_TOO_LARGE`.
- **Type refusé** : `422`, code `DOCUMENT_INVALID_TYPE`, message français nommant les
  formats acceptés.
- **Téléchargement** : `FileResponse` avec `Content-Disposition: attachment` portant le
  nom d'origine, assaini pour l'en-tête (guillemets et sauts de ligne écartés).
- **Traçabilité** : dépôt et suppression enregistrés dans `audit_logs`, avec le titre et
  l'identifiant du document.
- `uploaded_by` renseigné depuis l'utilisateur authentifié.

## Acceptance criteria

- [ ] Dépôt d'un PDF par la secrétaire : `201`, métadonnées renvoyées, fichier
      téléchargeable dans la foulée.
- [ ] `403` au dépôt, à la modification et à la suppression pour `readonly` ; `200` en
      lecture pour ce même rôle.
- [ ] Fichier de plus de 20 Mo : `413`, aucun fichier écrit.
- [ ] Fichier de type non autorisé : `422`, aucun fichier écrit.
- [ ] Liste filtrable par exercice, par étiquette et par recherche ; `X-Total-Count`
      reflète le total avant pagination.
- [ ] Téléchargement : le nom d'origine se retrouve dans `Content-Disposition`, un nom
      contenant un guillemet ou un saut de ligne ne casse pas l'en-tête.
- [ ] `404` sur un identifiant inexistant, pour chacune des routes concernées.
- [ ] Dépôt et suppression apparaissent dans `audit_logs`.

## Blocked by

01-document-model-service
