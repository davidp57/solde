# Lot PAY-NEW — Bouton « Nouveau paiement » dans la vue Paiements

Status: 🔄 in-progress
Branch: feature/pay-new-button → PR → develop

## Problem Statement

Constat de recette : la vue **Factures** a un bouton « Nouvelle facture », la vue **Paiements** n'a aucun bouton de création, ni sur ordinateur ni sur téléphone.
Pour encoder un règlement, il faut repasser par la carte « Encoder un paiement » du tableau de bord ou par la fiche de la facture.
La clé i18n `payments.new` (« Nouveau paiement ») existe déjà mais n'est utilisée nulle part.

## Solution

Ajouter dans l'en-tête de la vue Paiements un bouton principal **« Nouveau paiement »** (icône `pi pi-plus`), visible aussi sur téléphone, qui ouvre l'assistant existant `QuickPaymentWizard` — le même que celui du tableau de bord : choix de la facture impayée, puis saisie du règlement.
Pas de second formulaire.

- L'assistant émet un événement `saved` après chaque paiement enregistré ; la vue recharge alors la liste, pour que le nouveau paiement apparaisse.
  Le tableau de bord ignore cet événement : son usage est inchangé.
- La route des paiements accepte `?create=1` pour ouvrir l'assistant, comme les factures, puis retire le paramètre de l'URL.
- Droits : la route `payments` exige déjà `requiresManagement` (secrétaire, trésorier, admin), exactement les rôles autorisés par `POST /api/payments/` ; la vue n'applique pas d'autre restriction à la modification. Le bouton est donc affiché à tous ceux qui voient la vue.

## Tickets

| Ticket | Titre | Statut |
|---|---|---|
| [BIZ-266](tickets/01-payments-new-button.md) | Bouton « Nouveau paiement » dans la vue Paiements | 🔄 |
