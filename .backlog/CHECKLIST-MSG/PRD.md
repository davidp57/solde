# Lot CHECKLIST-MSG — Messages pour la séance de comptabilité

Status: ✅ done
Branch: feature/checklist-messages → PR → develop

## Problem Statement

Ce que l'équipe sait et que le trésorier doit traiter au mois — une facture reçue à la main, un chèque mis de côté, un remboursement promis — passe aujourd'hui par la mémoire ou par un message hors de l'application.
La séance de comptabilité (lot CHECKLIST) ne voit que ce que l'application peut constater.

## Solution

Un bouton dans le bandeau, à côté de celui de la séance, ouvre une fenêtre où **n'importe quel rôle** laisse un message libre.
Le trésorier lui-même s'en sert pour noter quelque chose à sa prochaine séance.

Les messages s'affichent en **premier bloc** de la séance, chacun avec son auteur et sa date, et se cochent comme une étape.

## Décisions (établies avec l'utilisateur)

- **Qui écrit** : tous les rôles, lecture seule comprise.
- **À quelle période** : aucune à choisir. Un message attend, non coché, et s'affiche dans la séance ouverte ou, à défaut, dans la prochaine qu'on ouvre.
- **Traitement** : une case par message. Cocher le rattache à la séance en cours ; une séance clôturée liste les messages qu'elle a traités. Un message non coché à la clôture reste affiché sur la séance suivante, marqué « En retard ».
- **Retrait** : l'auteur peut supprimer son message tant qu'il n'est pas coché ; pas de modification. Une fois coché, il fait partie de l'historique de la séance.
- Les messages ne comptent pas dans la progression « n / 17 » : ce ne sont pas des étapes.

## Tickets

| Ticket | Titre | Statut |
|---|---|---|
| [BIZ-265](tickets/01-checklist-messages.md) | Messages laissés au trésorier, affichés en tête de séance | ✅ |
