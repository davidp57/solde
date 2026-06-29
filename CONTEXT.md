# Solde — Glossaire métier

Application de comptabilité d'une association loi 1901 (soutien scolaire) :
facturation, paiements, trésorerie, comptabilité en partie double. Ce fichier
est un glossaire des termes métier propres au projet — pas une spec, pas un
bloc-notes d'implémentation.

## Language

### Créances & recouvrement

**Facture en retard** (_overdue_) :
Facture dont l'échéance (`due_date`) est dépassée, au statut ni brouillon, ni
archivée, **ni irrécouvrable**, et dont le montant restant dû est strictement
positif. Une créance abandonnée (irrécouvrable) n'est donc pas « en retard » :
elle est sortie du recouvrement comme des métriques. Calculée, pas stockée
(`isOverdueInvoice()`).
_Avoid_: impayée (au sens large), arriéré.

**Facture irrécouvrable** (_irrecoverable_) :
Créance client qu'on a renoncé à recouvrer. Statut `IRRECOVERABLE` ; le passage
génère une écriture comptable (654 / 411) et est réversible. Notion purement
métier de gestion des créances douteuses.
_Avoid_: **irréconciliable** (terme à proscrire : évoque à tort le rapprochement
bancaire), créance perdue, write-off.

**Relance** (_reminder_) :
Action de rappeler à un client le paiement d'une facture en retard, distincte de
l'envoi initial de la facture. Une facture peut faire l'objet de plusieurs
relances successives, dont on conserve l'historique daté.
_Avoid_: rappel, dunning, relaunch.
