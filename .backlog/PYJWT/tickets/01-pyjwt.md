# TEC-264 — Signature et vérification des jetons avec PyJWT

Status: ✅ done
Type: chore
Files: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `backend/services/auth.py`, `tests/unit/test_auth_service.py`, `tests/integration/test_auth_api.py`, `docs/dev/architecture.md`, `docs/plan.md`

## Acceptance criteria

- [x] `python-jose`, `ecdsa` et `types-python-jose` ne sont plus installés.
- [x] Un jeton signé par python-jose est accepté par PyJWT (vérifié à la main) : personne n'est déconnecté par la mise à jour.
- [x] Un jeton signé avec une autre clé, ou non signé (`alg: none`), est refusé.
- [x] Aucune autre version figée ne change.
