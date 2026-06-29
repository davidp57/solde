# Lot ML — Mailing aux adhérents actifs

Status: ✅ done
Version: v1.8.1 — released 2026-06-23
Branch(es): feat/member-mailing → develop

Envoyer un email à tous les **adhérents (clients) actifs**. **Actif** = a eu une facture
client émise OU un paiement reçu dans les X derniers mois (défaut 6, réglable). Parcours
en 3 étapes : période → sélection (tous cochés par défaut) → rédaction (sujet + corps).
Infra SMTP existante (`email_service`) ; **envoi individuel** (un email par destinataire,
adresses secondaires en `Cc`, pas de BCC global) ; accès Secrétaire+.

| Ticket | Titre | Prio | Statut |
|--------|-------|------|--------|
| TEC-210 | Backend — endpoint « clients actifs » (mois paramétrable) + envoi groupé sur connexion SMTP unique | P2 | ✅ |
| BIZ-217 | Frontend — assistant d'envoi en 3 étapes (période → sélection → rédaction) | P2 | ✅ |

## Notes de clôture

- Endpoints : `GET /api/contacts/active-clients?months=6` (EXISTS factures/paiements,
  pas de N+1) et `POST /api/contacts/mailing` (`To` primaire + `Cc` secondaires, session
  SMTP réutilisée, récap `{sent, failed[]}`).
