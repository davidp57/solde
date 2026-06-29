# BIZ-216 — Miroir backup : n'inclure que les PDFs non régénérables

Status: ✅ done
Type: feat
Files: `backend/services/backup_destination_service.py` (miroir TEC-209), `backend/models/`, `backend/services/settings.py`, `frontend/src/views/` (Paramètres › Sauvegardes), `frontend/src/i18n/fr.ts`, `tests/`

## What to build

Réduire le volume du miroir distant en ne sauvegardant que ce qui n'est **pas**
régénérable : PDFs de factures **archivées** (`status=ARCHIVED`, valeur légale) +
`data/uploads/` (.docx importés). Les PDFs de factures non archivées sont régénérables
à la demande (garantie par TEC-211).

- Au moment du miroir (`mirror_dir_incremental`, TEC-209), filtrer `data/pdfs` selon le
  statut de la facture liée — ne garder que les archivées. `data/uploads/` toujours inclus.
- Réglage **« Sauvegarder uniquement les PDFs non régénérables »** dans
  Paramètres › Sauvegardes, **off par défaut**. Toutes les chaînes via i18n (`fr.ts`).

## Acceptance criteria

- [ ] Avec le réglage activé : seuls les PDFs de factures archivées + `data/uploads/`
      sont inclus dans le miroir ; les non-archivés sont exclus.
- [ ] Avec le réglage désactivé (défaut) : comportement BK2 inchangé (tous les PDFs).
- [ ] Le réglage est persistant et exposé dans Paramètres › Sauvegardes.
- [ ] Risque documenté côté utilisateur : un PDF non archivé régénéré peut diverger
      visuellement si le template a changé (sans valeur légale).

## Blocked by

- TEC-211 (garde-fou de régénération si le fichier est manquant) — sans ce garde-fou,
  ne pas activer le filtre.
