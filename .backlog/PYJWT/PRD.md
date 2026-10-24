# Lot PYJWT — Remplacer python-jose par PyJWT

Status: ✅ done
Branch: chore/pyjwt → PR → develop

## Problem Statement

Les jetons de connexion étaient signés et vérifiés par python-jose, presque plus maintenu.
L'analyse de sécurité de la PR #179 a relevé deux alertes sur la chaîne : une confusion d'algorithme avec une clé publique encodée en DER (python-jose jusqu'à 3.5.0) et l'attaque Minerva sur `ecdsa`, sans correctif publié.

Aucune n'est exploitable dans Solde : signature HS256 avec un secret partagé, un seul algorithme accepté au décodage, pas de courbe elliptique.
Mais elles reviennent à chaque analyse, et la bibliothèque ne recevra plus de correctif.

## Solution

PyJWT, maintenu, fournit la même API pour l'usage de Solde (`encode`, `decode` avec liste d'algorithmes).
Le format des jetons est un standard : ceux émis avant la mise à jour restent valides.

## Tickets

| Ticket | Titre | Statut |
|---|---|---|
| [TEC-264](tickets/01-pyjwt.md) | Signature et vérification des jetons avec PyJWT | ✅ |
