# Lot AUDIT-LOG — Journal d'audit lisible et cherchable

Status: 🔄 in-progress
Branch: feature/audit-log → PR → develop

## Problem Statement

Retour de David (04/10/2026) : l'écran « Journal d'audit » manque de détails (« Rapprochement bancaire effectué | bank_transaction #447 ») et n'est pas cherchable.

Mesuré dans le code :

- l'écran appelle `GET /api/settings/audit-logs` sans paramètre, plafonné à 50 lignes : rien de plus ancien n'est visible ;
- l'API sait filtrer par action, utilisateur et période, l'écran n'en expose rien ;
- la cible est un couple `type #id`, illisible et perdu quand l'élément est supprimé ;
- le détail est un JSON brut en 0,6 em, et une trentaine d'actions n'ont pas de nom français ;
- « Tout rapprocher » n'enregistre qu'un nombre.

## Solution

- **TEC-261** — Libellé de cible figé à l'écriture (`audit_logs.target_label`), calculé en lot par `audit_labels.describe_targets`. Capturé avant chaque suppression ; entrées antérieures libellées au démarrage. Rapprochement en masse : liste des opérations ; rapprochement par règlement : facture(s).
- **TEC-262** — Recherche côté serveur : texte libre (`q`, `q_actions` pour les noms d'action traduits, `#id`), domaine (préfixe d'action), période, pagination avec total.
- **BIZ-264** — Écran : composant `AuditLogPanel`, recherche et filtres, pagination serveur, détail en clair, toutes les actions nommées.

## Out of Scope

- Ouvrir l'élément concerné depuis une entrée (une route par type de cible) : à rouvrir si le besoin se confirme.
- Libeller les entrées dont la cible a été supprimée avant ce lot : l'information n'existe plus.
