# BIZ-265 — Messages laissés au trésorier, affichés en tête de séance

Status: ✅ done
Type: feature
Files: `backend/models/checklist.py`, `backend/alembic/versions/20261024_add_checklist_messages.py`, `backend/services/checklist_service.py`, `backend/schemas/checklist.py`, `backend/routers/checklist.py`, `frontend/src/api/checklist.ts`, `frontend/src/stores/checklist.ts`, `frontend/src/components/checklist/ChecklistMessageDialog.vue`, `frontend/src/components/checklist/ChecklistPanel.vue`, `frontend/src/layouts/AppLayout.vue`, `frontend/src/i18n/fr.ts`

## What to build

Table `checklist_messages` (texte, auteur, date, `session_id` posé au moment où le message est coché).
API : `POST /api/checklist/messages`, `GET /api/checklist/messages/mine`, `DELETE /api/checklist/messages/{id}` ouverts à tout utilisateur connecté ; `PUT /api/checklist/sessions/{id}/messages/{message_id}` réservé au trésorier et à l'administrateur.
Le détail d'une séance porte `messages`, et `/api/checklist/current` le nombre de messages en attente.

## Acceptance criteria

- [x] Tout rôle laisse un message depuis le bandeau et voit ses messages en attente.
- [x] La séance ouverte affiche en premier bloc tous les messages non cochés, puis ceux cochés pendant cette séance.
- [x] Un message non coché à la clôture réapparaît sur la séance suivante, marqué « En retard ».
- [x] Une séance clôturée liste les messages qu'elle a traités, et ceux-là seulement.
- [x] Seul l'auteur retire un message, et seulement tant qu'il n'est pas coché.
- [x] Seuls le trésorier et l'administrateur cochent un message.
