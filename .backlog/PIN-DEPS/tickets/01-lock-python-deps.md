# TEC-263 — Fichiers de versions figées, branchés sur la CI et Docker

Status: ✅ done
Type: chore
Files: `requirements.txt`, `requirements-dev.txt`, `docker-requirements.txt` (supprimé), `Dockerfile`, `.github/workflows/ci.yml`, `.github/dependabot.yml`, `docs/dev/README.md`, `docs/dev/contributing.md`, `.github/copilot-instructions.md`

## Acceptance criteria

- [x] La CI et l'image installent les mêmes versions exactes, quelles que soient les publications en amont.
- [x] Les deux fichiers sont générés, jamais édités à la main, et portent la commande qui les régénère.
- [x] La porte de qualité backend est verte en Python 3.11 sur les versions figées.
- [x] La doc de dev explique l'installation et la mise à jour.
