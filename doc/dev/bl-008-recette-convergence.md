# BL-008 — Recette locale de convergence Excel/Solde

## Objectif

Rejouer, sans rien persister, les previews de convergence BL-008 sur les classeurs historiques locaux afin de répondre rapidement à trois questions :

- qu'est-ce qui manque encore dans Solde ;
- qu'est-ce qui existe en trop dans Solde ;
- est-ce que le fichier est encore importable ou déjà rebloqué par l'idempotence.

## Commande de recette

Depuis la racine du dépôt :

```bash
d:/dev/_misc/solde/.venv/Scripts/python.exe scripts/run_excel_convergence_preview.py
```

Pour conserver le rapport JSON :

```bash
d:/dev/_misc/solde/.venv/Scripts/python.exe scripts/run_excel_convergence_preview.py --output data/logs/bl-008-convergence-preview.json
```

## Comportement du script

- utilise la base pointée par `database_url` ; par défaut ici `data/solde.db` ;
- utilise en priorité les chemins configurés dans `test_import_*_path` si présents ;
- sinon détecte automatiquement les quatre classeurs historiques sous `data/` ;
- exécute les previews existantes `Gestion` et `Comptabilite`, sans import ;
- retourne un JSON avec les compteurs globaux, les compteurs par domaine, et quelques exemples d'avertissements et d'erreurs.

## Constat local du 2026-04-18

Commande exécutée sur la base locale courante `data/solde.db`.

| Fichier | Mode | Importable | Lecture rapide |
| --- | --- | --- | --- |
| `data/Gestion 2024.xlsx` | `gestion-excel-to-solde` | Non | Blocage par hash déjà importé ; `already_in_solde=329`, `missing_in_solde=579`, `extra_in_solde=0`. |
| `data/Gestion 2025.xlsx` | `gestion-excel-to-solde` | Oui | Delta encore important ; `missing_in_solde=602`, `extra_in_solde=492`. |
| `data/Comptabilité 2024.xlsx` | `global-convergence` | Non | Blocage par hash déjà importé ; `already_in_solde=1385`, `missing_in_solde=0`, `extra_in_solde=1384`. |
| `data/Comptabilité 2025.xlsx` | `global-convergence` | Oui | Delta lisible sans écriture ; `missing_in_solde=930`, `extra_in_solde=879`. |

## Interprétation minimale

- La recette locale confirme que la preview BL-008 remonte maintenant les deux sens de l'écart sur des fichiers réels : ce qui manque dans Solde et ce qui y existe en trop.
- Les fichiers déjà importés restent naturellement bloqués par l'idempotence par hash, mais le rapport de comparaison reste exploitable pour lire l'état courant.
- Les fichiers 2025 restent prévisualisables et donnent un premier diagnostic chiffré exploitable avant tout import ou toute analyse métier plus fine.
