# Lot DOCS — Espace de documents

Status: ✅ done
Branch: feature/documents → PR → develop

## Problem Statement

Une association produit et reçoit des documents qui n'ont **aucun rattachement naturel**
à une facture, un règlement ou un salarié : statuts, procès-verbaux d'assemblée générale,
attestations d'assurance, courriers administratifs, conventions, rapports d'activité,
états financiers signés, justificatifs divers.

Aujourd'hui Solde ne sait stocker un fichier qu'**attaché à un objet métier** : le PDF
d'une facture (`data/pdfs/`), un classeur d'import (`data/uploads/`). Un document isolé
n'a nulle part où aller. Il finit sur le poste de la trésorière ou dans une boîte mail,
c'est-à-dire hors de portée de la personne suivante.

Le déclencheur immédiat : la clôture de l'exercice 2025-2026 produit un bilan et un
compte de résultat en PDF (lot livré en 1.15.0) qu'il faut **conserver avec l'exercice
auquel ils se rapportent**. Rien ne permet de le faire dans l'application.

## Solution

Un **espace de documents** générique : on y dépose un fichier, on lui donne un titre, on
peut l'associer à un exercice comptable et lui poser des étiquettes. Rien de plus.

Le rattachement à un exercice est **facultatif** : les statuts de l'association ne
dépendent d'aucun exercice, le bilan 2025-2026 si.

Modèle d'un document :

| Champ | Nature | Détail |
|---|---|---|
| `title` | obligatoire | Titre lisible, saisi par l'utilisateur — indépendant du nom du fichier |
| `filename` | automatique | Nom d'origine du fichier, conservé pour le téléchargement |
| `uploaded_at` | automatique | Date et heure du dépôt |
| `fiscal_year_id` | facultatif | Exercice de rattachement |
| `tags` | facultatif | Étiquettes libres, avec suggestion de celles déjà utilisées |
| `notes` | facultatif | Quelques lignes de contexte |

## User Stories

1. En tant que trésorière, je veux déposer le bilan et le compte de résultat d'un
   exercice clôturé et les retrouver rattachés à cet exercice, pour que les pièces
   comptables d'une année soient réunies au même endroit.
2. En tant que secrétaire, je veux déposer un document sans avoir à choisir un exercice
   ni une catégorie imposée, pour ne pas être bloquée par une taxonomie qui ne
   correspond pas au document que j'ai en main.
3. En tant qu'utilisateur, je veux filtrer les documents par exercice et par étiquette,
   pour retrouver une pièce sans faire défiler toute la liste.
4. En tant qu'utilisateur, je veux voir les étiquettes déjà employées au moment d'en
   poser une, pour ne pas créer « AG » à côté de « assemblée générale ».
5. En tant que successeur de la trésorière, je veux que les documents survivent au départ
   de la personne qui les a déposés, ce qui est précisément ce qu'un dossier personnel ne
   garantit pas.

## Implementation Decisions

- **Étiquettes stockées en colonne JSON**, pas en table dédiée. Une table
  d'associations coûterait une migration, deux modèles et des jointures pour un usage qui
  restera de l'ordre de la dizaine d'étiquettes. Un endpoint dédié agrège les valeurs
  distinctes pour alimenter la suggestion à la saisie. Le projet emploie déjà ce procédé
  (`Invoice.reminder_dates`). Si le besoin grandit — renommage global, couleurs,
  hiérarchie — la table se justifiera alors ; pas avant.
- **Normalisation des étiquettes à l'écriture** : minuscules, espaces réduits, doublons
  supprimés. Sans quoi « AG » et « ag » cohabitent et aucun filtre ne fonctionne.
- **Titre obligatoire, distinct du nom de fichier.** Un fichier nommé
  `scan_20260804_001.pdf` ne se retrouve pas ; « PV assemblée générale 2026 » si.
- **Rôles** : lecture et téléchargement pour tout utilisateur connecté, `readonly`
  compris — l'application donne déjà la lecture intégrale à ce rôle. Dépôt, modification
  et suppression à partir de `secretaire` : la secrétaire est la première concernée par
  le classement, en faire une opération d'administrateur viderait la fonction de son
  intérêt.
- **Stockage sur disque, pas en base.** Fichiers dans `data/documents/`, sous un nom
  `<uuid>-<nom-assaini>` pour écarter les collisions et toute traversée de chemin. La
  base ne porte que les métadonnées. Cohérent avec `data/pdfs/` et avec le budget de
  384 Mo de RAM : rien de volumineux ne transite par SQLite.
- **Liste blanche de types, vérifiée aux octets d'en-tête** et pas seulement à
  l'extension ni au `Content-Type` déclaré : PDF, JPEG, PNG, WebP, classeurs Office
  (xlsx/docx, qui sont des ZIP), documents Office anciens (xls/doc), CSV et texte brut.
  Les deux derniers n'ayant pas de signature, ils sont acceptés sur extension après
  contrôle qu'ils se décodent en UTF-8 ou Latin-1.
- **Plafond à 20 Mo par fichier**, contre 10 Mo pour l'import Excel : un PV scanné pèse
  plus lourd qu'un classeur, et le fichier est écrit en flux sans être chargé deux fois
  en mémoire.
- **La suppression retire le fichier du disque.** Un enregistrement supprimé qui laisse
  son fichier derrière lui remplit le volume sans que rien ne le signale.

## Out of Scope

- **Prévisualisation dans l'application.** Le téléchargement suffit ; un lecteur PDF
  intégré est un chantier à lui seul.
- **Versions successives d'un même document.** Un nouveau dépôt est un nouveau document.
- **Recherche en plein texte du contenu.** La recherche porte sur le titre, les
  étiquettes et les notes.
- **Rattachement à une facture ou à un contact.** L'espace est volontairement détaché des
  objets métier — c'est ce qui lui donne sa raison d'être. Un tel lien pourra se
  concevoir plus tard, comme un ajout et non comme un préalable.
- **Inclusion dans la sauvegarde applicative.** Celle-ci ne couvre que la base ; les
  fichiers déposés vivent dans le volume `data/`, sauvegardé au niveau du NAS, au même
  titre que `data/pdfs/`. À traiter globalement le jour où l'on étend la sauvegarde aux
  fichiers, pas dans ce lot.

## Tickets

| # | Ticket | Objet |
|---|---|---|
| 01 | BIZ-240 | Modèle, migration et service de documents |
| 02 | BIZ-241 | API REST : dépôt, liste, téléchargement, suppression |
| 03 | BIZ-242 | Écran Documents |

## Écart assumé

Le ticket 03 plaçait l'entrée de menu dans la section **Gestion**. Elle est finalement dans
**Accueil** : la section Gestion est fermée au rôle `readonly`, or le PRD lui ouvre la
lecture. Le PRD prime.
