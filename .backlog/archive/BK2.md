# Lot BK2 — Optimisation de l'espace des backups (OneDrive)

Status: ✅ done
Version: v1.8.1 — released 2026-06-23
Branch(es): feat/backup-retention-mirror → develop

**Problème prod** : OneDrive (destination des backups) saturait. À chaque run, le job de
backup créait un dossier distant **horodaté** et y ré-envoyait **tout `data/pdfs`**, sans
purge distante → accumulation. Mesuré 2026-06-22 : 32 backups quotidiens jamais purgés,
**3,94 Go** dont **3,42 Go (87 %) de PDFs** (21 340 fichiers).

**Portée de la rétention** : la purge ne vise **que** les snapshots horodatés
`solde/backups/<timestamp>/`. Les dossiers miroirs stables (`solde/pdfs/`,
`solde/uploads/`) introduits par TEC-209 sont **append-only**, jamais purgés.

| Ticket | Titre | Prio | Statut |
|--------|-------|------|--------|
| TEC-208 | Rétention distante des backups — purger les snapshots horodatés au-delà de 5 (OneDrive/SMB) | P1 | ✅ |
| TEC-209 | Miroir PDF/uploads incrémental — dossier distant stable, « upload si absent » (fin de la duplication) | P1 | ✅ |
| BIZ-216 | N'inclure que les PDFs non régénérables | P2 | ➡️ reporté → lot [BK3](../BK3/PRD.md) |

## Notes de clôture

- **TEC-208** : `prune_remote_backups(dest, keep=5)` — tri lexicographique des snapshots
  ISO, suppression au-delà des 5 plus récents, jamais le run courant ni les miroirs.
- **TEC-209** : `mirror_dir_incremental` vers `solde/pdfs/` + `solde/uploads/` (envoi des
  fichiers absents uniquement, comparaison par nom + taille). `data/pdfs`/`data/uploads`
  retirés du snapshot horodaté. Restauration adaptée pour récupérer depuis les miroirs.
- **BIZ-216** : reporté hors PR BK2 faute d'un garde-fou de régénération à la demande →
  repris dans le lot actif **BK3**.
