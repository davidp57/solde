# Lot PIN-DEPS — Figer les versions des dépendances Python

Status: ✅ done
Branch: chore/pin-python-deps → PR → develop

## Problem Statement

`pyproject.toml` et `docker-requirements.txt` ne déclaraient que des minimums (`fastapi>=0.115`).
La CI installait donc la dernière version publiée le jour de chaque run, et l'image Docker celle du jour où sa couche de dépendances avait été reconstruite.

Le 24/10/2026, Starlette 1.9, sortie entre deux PR, a fait échouer six tests sur la PR #178, qui n'y touchait pas.
En local, le venv était resté en Starlette 1.0 : les tests passaient.
Même famille que l'écart SQLAlchemy 2.0/2.1 qui avait masqué le bug de la PR #173.

## Solution

- `requirements.txt` : tous les paquets d'exécution à une version exacte, générés par `uv pip compile` depuis `pyproject.toml`, en mode universel (Python 3.11+, toutes plateformes). Utilisé par l'image Docker ; remplace `docker-requirements.txt`, qui était tenu à la main.
- `requirements-dev.txt` : la même chose plus les outils de dev, contraint par `requirements.txt` pour que la CI teste exactement les versions de l'image.
- CI : `pip install -r requirements-dev.txt` puis `pip install --no-deps -e .`.
- Dependabot : une PR groupée par mois vers `develop`.
- `pyproject.toml` garde les plages acceptées : c'est la source de la génération.

## Tickets

| Ticket | Titre | Statut |
|---|---|---|
| [TEC-263](tickets/01-lock-python-deps.md) | Fichiers de versions figées, branchés sur la CI et Docker | ✅ |
