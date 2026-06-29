# BIZ-219 — Templates de relance dédiés (1ère / suivante) + moteur de composition

Status: ⬜ ready
Type: feat
Files: `backend/models/app_settings.py`, `backend/schemas/settings.py`, `backend/services/email_service.py`, `backend/routers/settings.py`, `frontend/src/views/` (Paramètres), `frontend/src/i18n/fr.ts`, `tests/unit/`, `tests/integration/`

## What to build

Deux templates de relance configurables, **distincts** du template d'envoi initial.

1. Ajouter à `app_settings` deux jeux sujet + corps :
   - **1ère relance** (`reminder_first_subject_template`, `reminder_first_body_template`)
   - **relance suivante** (`reminder_next_subject_template`, `reminder_next_body_template`)
   String nullable ; `null` ⇒ defaults intégrés (texte FR à fournir, ton courtois pour la
   1ère, plus ferme + ancienneté pour la suivante). Schémas Pydantic + endpoint settings.
2. Section dédiée dans l'écran **Paramètres › ...** pour éditer ces 4 champs (strings via
   i18n). Documenter les variables disponibles dans l'UI.
3. Étendre `email_service` (`compose_subject` / `compose_body`) pour :
   - **sélectionner** le template selon l'état : `reminder_dates` vide ⇒ 1ère relance,
     sinon ⇒ relance suivante ;
   - résoudre les variables de relance : existantes (`{invoice_number}`, `{description}`,
     `{association_name}`, `{invoice_ref}`) + `{derniere_relance}` (date de la dernière
     relance, vide à la 1ère), `{montant_du}` (`total_amount − paid_amount`), `{echeance}`
     (`due_date`), `{nombre_de_relances}` (= `len(reminder_dates)`, `0` à la 1ère).
   Dates formatées en FR (`JJ/MM/AAAA`). Conserver le « safe format » existant (clés
   inconnues laissées telles quelles).

## Acceptance criteria

- [ ] 4 nouveaux champs de template dans `app_settings` + migration + schémas + endpoint.
- [ ] `null` ⇒ defaults intégrés (1ère / suivante) ; valeurs persistées éditables en Paramètres.
- [ ] Sélection correcte du template selon `reminder_dates` (vide ⇒ 1ère, sinon suivante).
- [ ] Toutes les variables de relance résolues, dates au format FR ; clés inconnues intactes.
- [ ] Strings UI via i18n (`fr.ts`), aucune chaîne en dur.
- [ ] Tests unitaires (composition + sélection) + intégration (settings API).

## Blocked by

BIZ-218 (a besoin de `reminder_dates` pour sélectionner le template et résoudre les variables).
