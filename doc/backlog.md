# Backlog — Solde ⚖️

## But

Ce document est la source de vérité des changements à discuter puis à planifier hors roadmap de jalons :

- corrections découvertes en test ou en usage réel ;
- améliorations UX ;
- évolutions fonctionnelles ;
- dette technique ciblée ;
- suites à donner aux points remontés pendant les échanges avec l'utilisateur.

Il reste volontairement léger, versionné dans Git, et relu en même temps que le code.

Tout sujet concret qui doit survivre au-delà de la séance en cours doit être capturé ici avec un statut explicite et mis à jour au fil du travail.

## Règles de fonctionnement

1. Ajouter chaque nouveau sujet dans le **Récapitulatif des sujets ouverts** avec une formulation courte et concrète.
2. Proposer une **priorité** (`P1`, `P2`, `P3`) avant arbitrage.
3. Passer un sujet en **Prêt** une fois le besoin clarifié.
4. Déplacer en **En cours** quand le travail démarre sur une branche active.
5. Déplacer en **Fait** quand l'implémentation est livrée et considérée comme terminée côté backlog.
6. Suivre les dates avec le format ISO (`YYYY-MM-DD`) : `created`, `started`, `completed`.
7. Ne pas laisser de suite actionnable uniquement dans la conversation si elle doit être retrouvée plus tard.
8. Dans chaque section qui liste des tickets, y compris le récapitulatif des sujets ouverts, conserver l'ordre numérique croissant des identifiants `BL-xxx`.

### Signification des priorités

- `P1` — important à discuter rapidement ; fort impact métier, besoin opérationnel ou risque notable.
- `P2` — utile mais non bloquant ; amélioration à programmer.
- `P3` — confort, finition ou dette technique optionnelle.

### Signification des statuts

- `Bac d'entrée` — besoin capturé, pas encore arbitré.
- `Prêt` — besoin clarifié, prêt à être pris.
- `En cours` — sujet en cours d'implémentation sur une branche active.
- `Fait` — sujet livré et prêt à être fusionné ou déjà intégré.
- Dans ce document, un sujet encore au statut `Bac d'entrée` apparaît uniquement dans le récapitulatif des sujets ouverts, sans entrée dédiée dans `Prêt`, `En cours` ou `Fait`.

### Champs de dates

- `created` — date d'entrée initiale dans le backlog.
- `started` — date de démarrage effectif sur une branche.
- `completed` — date à laquelle le sujet est considéré comme livré côté backlog.
- Toujours utiliser le format ISO `YYYY-MM-DD`.
- Dans `Détail des sujets`, ajouter systématiquement une ligne `Dates` avec uniquement les champs connus pour le statut courant.
- Pour un sujet historique déjà traité avant structuration complète du backlog, approximer `created` à partir de la première trace utile disponible dans l'historique récent du dépôt.

## Priorités proposées pour la prochaine discussion

1. **BL-045 à BL-049** — corriger les failles de sécurité critiques (rate limiting, stockage des tokens, en-têtes HTTP) et remettre les tests au vert.
2. **BL-021** — finaliser le manuel utilisateur illustré avec stabilisation éditoriale et enrichissement visuel.
3. **BL-050 à BL-053** — fiabiliser le moteur comptable (numérotation thread-safe), protéger `reset-db`, forcer le changement du mot de passe admin, et planifier le refactoring du god module `excel_import.py`.

## Récapitulatif des sujets ouverts

| ID | Créé le | Type | Zone | Priorité proposée | Sujet |
|---|---|---|---|---|---|
| BL-019 | 2026-04-13 | Documentation | Projet / Exploitation | P1 | Refaire le README et la documentation technique d'installation, mise à jour, pile techno, configuration et exploitation Docker |
| BL-020 | 2026-04-13 | Documentation | Développement | P3 | Documenter clairement comment participer au projet : prérequis, environnement local, commandes utiles, qualité attendue et workflow PR |
| BL-021 | 2026-04-13 | Documentation | Utilisateur / Parcours | P1 | Rédiger un manuel utilisateur illustré et pas à pas aligné sur les écrans réellement disponibles |
| BL-033 | 2026-04-21 | Import / Fonctionnel | Gestion / Paiements | P1 | Clarifier la comparaison des chèques inter-exercices entre date de paiement et date de remise |
| BL-034 | 2026-04-21 | Fonctionnel / Architecture | Banque / Multi-compte | P2 | Introduire un support multi-compte explicite pour la banque afin de distinguer proprement compte courant et compte épargne dans les données, les imports et les écrans |
| BL-035 | 2026-04-21 | UX / Fonctionnel | Contacts | P2 | Séparer les contacts clients et fournisseurs dans deux onglets dédiés sur l'écran des contacts |
| BL-036 | 2026-04-21 | UX / Fonctionnel | Factures client / Synthèse | P2 | Rendre la carte `restant en retard` cliquable pour ouvrir la liste des factures clientes concernées |
| BL-037 | 2026-04-21 | UX / Navigation | Shell utilisateur | P3 | Remplacer l'entrée de menu `Mon profil` par un accès au profil via un clic sur le nom de l'utilisateur |
| BL-038 | 2026-04-21 | UX / Produit | Application / Shell | P3 | Afficher un numéro de version discret mais visible dans l'interface de l'application |
| BL-039 | 2026-04-21 | Qualité / Recette | Factures client / Email | P1 | Rejouer et fiabiliser les scénarios d'édition de facture client et d'envoi par e-mail avec validation explicite du comportement attendu |
| BL-040 | 2026-04-21 | Import / Fonctionnel | Contacts client | P2 | Ajouter un import one-shot d'une liste d'adresses e-mail pour enrichir les contacts clients existants |
| BL-041 | 2026-04-21 | UX / Fonctionnel | Paiements / Synthèse | P2 | Rendre la carte `non remis` cliquable pour ouvrir la liste des paiements concernés |
| BL-042 | 2026-04-21 | UX / Cohérence | Tables / Filtres | P2 | Ajouter un bouton `reset` sur tous les filtres de toutes les tables pour revenir rapidement à l'état initial |
| BL-043 | 2026-04-21 | UX / Fonctionnel | Comptabilité / Filtres | P2 | Remplacer les filtres de comptes comptables par des combos affichant numéro, nom et couleur des comptes suivis |
| BL-045 | 2026-04-22 | Sécurité | Authentification | P1 | Ajouter un rate limiting sur `/auth/login` pour bloquer le brute force |
| BL-046 | 2026-04-22 | Sécurité | Authentification / Tokens | P1 | Migrer le refresh token vers un cookie HttpOnly au lieu de localStorage |
| BL-047 | 2026-04-22 | Sécurité | HTTP / Infrastructure | P1 | Ajouter les en-têtes de sécurité HTTP (CSP, HSTS, X-Content-Type-Options, X-Frame-Options) |
| BL-048 | 2026-04-22 | Qualité / Tests | Backend / Tests unitaires | P1 | Corriger les 11 tests en échec et la 1 erreur dans la suite backend |
| BL-049 | 2026-04-22 | Qualité / Tests | Backend + Frontend | P1 | Remonter la couverture de test de 29 % vers les objectifs (services ≥ 90 %, API ≥ 80 %, composables ≥ 70 %) |
| BL-050 | 2026-04-22 | Dette technique | Services / Import Excel | P1 | Refactorer `excel_import.py` (5 038 lignes) en package avec modules < 500 lignes |
| BL-051 | 2026-04-22 | Fiabilité / Comptabilité | Écritures comptables | P1 | Corriger la numérotation des écritures comptables (COUNT non thread-safe → MAX + lock) |
| BL-052 | 2026-04-22 | Sécurité | Administration / Données | P1 | Désactiver ou protéger l'endpoint `POST /settings/reset-db` en production |
| BL-053 | 2026-04-22 | Sécurité | Authentification / Bootstrap | P1 | Forcer le changement du mot de passe admin au premier login |
| BL-054 | 2026-04-22 | DevOps / Docker | Déploiement | P2 | Séparer les migrations Alembic du démarrage Uvicorn dans le Dockerfile |
| BL-055 | 2026-04-22 | Sécurité / Config | CORS | P2 | Configurer les origines CORS pour la production au lieu de `allow_origins=[]` |
| BL-056 | 2026-04-22 | Sécurité / Traçabilité | Audit | P2 | Ajouter un journal d'audit structuré pour les actions sensibles (connexions, rôles, suppressions) |
| BL-057 | 2026-04-22 | Dette technique | Backend / ORM | P2 | Créer un TypeDecorator SQLAlchemy pour Decimal afin d'éliminer les ~30 occurrences de `Decimal(str(...))` |
| BL-058 | 2026-04-22 | Dette technique | Services / Import Excel | P2 | Typer les exceptions dans l'import Excel (remplacer les `except Exception` généralisés) |
| BL-059 | 2026-04-22 | Sécurité / API | Endpoints de liste | P2 | Ajouter des limites de pagination par défaut (100) et maximum (1 000) sur tous les endpoints de liste |
| BL-060 | 2026-04-22 | Fiabilité / DB | Schéma | P2 | Retirer `Base.metadata.create_all` de `init_db()` et se reposer uniquement sur Alembic pour le schéma |
| BL-061 | 2026-04-22 | DevOps / Docker | Monitoring | P2 | Ajouter un HEALTHCHECK Docker pour la supervision Synology |
| BL-062 | 2026-04-22 | Qualité / Projet | Versions | P2 | Synchroniser les versions frontend (`0.0.0`) et backend (`0.1.0`) |
| BL-063 | 2026-04-22 | RGPD / Données | Plan comptable | P3 | Retirer les noms de personnes réelles du plan comptable par défaut dans le code source |
| BL-064 | 2026-04-22 | Qualité / Frontend | Code mort | P3 | Supprimer `stores/counter.ts` (scaffolding Vue non utilisé) |
| BL-065 | 2026-04-22 | Qualité / Backend | Modèles | P3 | Éliminer `__allow_unmapped__` du modèle Payment et utiliser un DTO séparé |
| BL-066 | 2026-04-22 | Qualité / Backend | Config | P3 | Utiliser `@lru_cache` pour le singleton Settings au lieu du pattern global mutable |

## Détail des sujets ouverts

### BL-019 — README et documentation technique d'exploitation

- **Dates** : `created=2026-04-13`, `started=2026-04-21`
- **Pourquoi** : la documentation projet existe mais reste encore trop dispersée ou trop implicite pour quelqu'un qui doit installer, mettre à jour ou exploiter Solde sans relire tout le dépôt.
- **Résultat attendu** : un README plus clair et une documentation technique structurée couvrant au minimum l'installation, la mise à jour, la pile technologique, la configuration, Docker, les volumes de données, les sauvegardes et les points d'exploitation courants.
- **Avancement actuel** : le `README.md` est recentré comme page d'entrée synthétique `FR + EN`, une documentation technique dédiée `doc/dev/exploitation.md` couvre désormais en anglais la configuration, Docker, les volumes, les sauvegardes et les opérations courantes, un guide d'installation `FR + EN` est ajouté dans `doc/user/installation.md`, et `.env.example` documente explicitement les variables de bootstrap administrateur et les informations association.
- **Reste à confirmer** : le ticket reste ouvert tant que ce socle documentaire n'a pas été entièrement revalidé en tests réels d'installation, de mise à jour et d'exploitation, avec corrections éventuelles à intégrer.
- **Point d'attention** : distinguer ce qui relève du guide d'exploitation réel de ce qui relève des détails purement développeur, pour éviter un README surchargé.

### BL-020 — Documentation de développement et contribution

- **Dates** : `created=2026-04-13`, `started=2026-04-21`
- **Pourquoi** : contribuer efficacement au projet suppose aujourd'hui de reconstituer les prérequis et les conventions depuis plusieurs fichiers, ce qui freine la reprise de contexte et la qualité des contributions.
- **Résultat attendu** : une documentation développeur claire expliquant les prérequis, la mise en route locale, les commandes de build/test/lint, la qualité attendue, l'organisation du dépôt, le workflow de contribution et les attentes avant PR.
- **Avancement actuel** : la nouvelle documentation `doc/dev/contribuer.md`, rédigée en anglais, centralise la mise en route locale, l'usage de `dev.ps1`, la matrice de checks backend/frontend, les conventions de code et de langue, le rôle du backlog et le workflow Git attendu avant PR ; les consignes du dépôt ont été alignées sur une politique de langue plus explicite pour distinguer docs techniques `EN` et docs utilisateur / installation `FR + EN`.
- **Reste à confirmer** : le ticket reste ouvert tant que la documentation de contribution n'a pas été relue et validée sur le vrai cycle `setup -> checks -> PR`, avec ajustements éventuels après tests.
- **Point d'attention** : cette documentation doit rester fidèle aux commandes réellement utilisées dans le dépôt, pas à un idéal théorique.

### BL-021 — Manuel utilisateur illustré et pas à pas

- **Dates** : `created=2026-04-13`, `started=2026-04-13`
- **Pourquoi** : la documentation utilisateur est la plus critique pour l'adoption réelle de Solde, car les utilisateurs visés ne sont pas nécessairement informaticiens et ont besoin d'un guidage concret, rassurant et progressif.
- **Résultat attendu** : un manuel utilisateur en français, très clair, illustré par des captures d'écran, couvrant pas à pas les actions principales comme saisir une facture client, enregistrer un paiement client, saisir un achat avec facture, gérer la caisse, consulter la banque, utiliser les imports et comprendre les principaux écrans comptables.
- **Critère d'acceptation** : un utilisateur non technique doit pouvoir suivre le guide pour exécuter les scénarios métier essentiels sans aide orale complémentaire.
- **Avancement actuel** : le manuel utilisateur FR/EN dispose maintenant d'une structure pas à pas consolidée avec orientation rapide par besoin, liens explicites vers les guides complémentaires et formulation homogénéisée sur les parcours principaux ; le lot restant porte surtout sur l'enrichissement visuel réel (captures annotées homogènes, puis éventuellement version imprimable).
- **Priorisation proposée** : chantier éditorial majeur et prioritaire côté valeur utilisateur ; il faut l'attaquer tôt, mais avec une stratégie incrémentale plutôt qu'un objectif “manuel complet” monolithique.
- **Séquence recommandée** : commencer par un socle de parcours essentiels (`facture client`, `paiement client`, `achat fournisseur`, `caisse`, `banque`, `import Excel`), puis enrichir ensuite avec les écrans comptables avancés et les cas plus rares.
- **Table des matières cible** :
	- introduction : à quoi sert Solde et à qui s'adresse l'application ;
	- premiers pas : connexion, repères de navigation, vocabulaire simple, exercice courant ;
	- gérer les contacts ;
	- créer une facture client ;
	- enregistrer un paiement client ;
	- saisir un achat fournisseur avec sa facture ;
	- gérer la caisse ;
	- gérer la banque et les remises ;
	- utiliser les imports Excel ;
	- consulter les écrans comptables ;
	- corriger une erreur fréquente ou revenir en arrière ;
	- questions fréquentes et glossaire métier.
- **Ordre de rédaction recommandé** :
	- lot 1 : `connexion et repères`, `contacts`, `facture client`, `paiement client` ;
	- lot 2 : `achat fournisseur`, `caisse`, `banque et remises` ;
	- lot 3 : `import Excel`, `lecture des écrans comptables`, `FAQ`, `glossaire` ;
	- lot 4 : stabilisation éditoriale et enrichissement visuel avec captures homogènes, encadrés d'alerte et version imprimable si utile.
- **Format attendu par chapitre** :
	- objectif simple ;
	- prérequis éventuels ;
	- étapes numérotées ;
	- capture(s) annotée(s), ajoutées seulement en fin de chantier quand les écrans sont suffisamment stabilisés ;
	- résultat attendu ;
	- erreurs fréquentes ou points d'attention.
- **Point d'attention** : ce manuel doit privilégier les parcours métier concrets, le vocabulaire simple et les écrans réels de l'application, plutôt qu'une description abstraite des fonctionnalités ; les captures doivent arriver en dernière étape pour éviter une maintenance inutile tant que l'UI continue d'évoluer.

### BL-033 — Comparaison des chèques inter-exercices dans les imports et validations

- **Dates** : `created=2026-04-21`
- **Pourquoi** : pour un chèque, la date de règlement réellement prise en compte peut appartenir à l'exercice précédent alors que la remise en banque intervient dans l'exercice courant ; la comparaison actuelle des paiements importés reste trop centrée sur `payment.date`, ce qui crée des écarts trompeurs entre Excel et Solde lors des validations `Gestion` / `Comptabilité` par exercice.
- **Résultat attendu** : expliciter noir sur blanc la convention métier et technique retenue pour les chèques inter-exercices, puis aligner la comparaison d'import et la documentation sur cette convention afin qu'un chèque reçu en `N-1` mais remis en banque en `N` ne soit plus interprété comme un écart de paiement si le comportement est attendu.
- **Avancement actuel** : les constats et écarts déjà expliqués sur la validation `Gestion/Comptabilité 2025` sont désormais suivis dans `doc/dev/bl-026-validation-2025-working-notes.md`, afin de maintenir une liste courte et vivante des deltas confirmés au fur et à mesure des tests.
- **Point d'attention** : il faut conserver la séparation métier entre `date du paiement` et `date de remise`, sans réécrire artificiellement les dates pour faire coller les comparaisons ; si nécessaire, la validation doit raisonner différemment selon le domaine (`paiement`, `remise`, `banque`, `511200`) ou afficher explicitement les cas de report inter-exercices.

### BL-045 — Rate limiting sur `/auth/login`

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point S1).
- **Pourquoi** : l'endpoint de connexion n'a aucun mécanisme de limitation de débit. Un attaquant peut effectuer un nombre illimité de tentatives de mot de passe.
- **Résultat attendu** : ajouter un rate limiting (ex. `slowapi` ou middleware custom) limitant à 5 tentatives par minute par IP sur `/auth/login`, avec un code `429 Too Many Requests` en retour.
- **Point d'attention** : ne pas bloquer les tests automatisés ; prévoir un bypass configurable pour l'environnement de test.

### BL-046 — Migrer le refresh token vers un cookie HttpOnly

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point S2).
- **Pourquoi** : le refresh token est actuellement stocké en `localStorage`, accessible par n'importe quel JavaScript de la page. Si une dépendance tierce est compromise (XSS supply-chain), l'attaquant récupère le token directement.
- **Résultat attendu** : stocker le refresh token dans un cookie `HttpOnly`, `Secure`, `SameSite=Strict`. L'access token peut rester en mémoire JavaScript (variable réactive) avec rafraîchissement automatique. Adapter l'intercepteur Axios et le backend pour lire le refresh token depuis le cookie.
- **Point d'attention** : ce changement impacte le flow d'auth frontend (`stores/auth.ts`), l'intercepteur 401 (`api/client.ts`), et l'endpoint `/auth/refresh` côté backend.

### BL-047 — En-têtes de sécurité HTTP

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point S3).
- **Pourquoi** : aucun en-tête de sécurité HTTP n'est configuré (CSP, HSTS, X-Content-Type-Options, X-Frame-Options). En mode mono-conteneur sans reverse proxy, c'est la responsabilité de l'application.
- **Résultat attendu** : ajouter un middleware FastAPI injectant au minimum `Content-Security-Policy: default-src 'self'; script-src 'self'`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`.
- **Point d'attention** : tester que la CSP ne casse pas le chargement des assets PrimeVue (fonts, CSS inline éventuels).

### BL-048 — Corriger les tests en échec

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point T1).
- **Pourquoi** : la suite backend comporte 11 tests en échec et 1 erreur. Cela indique des régressions non corrigées ou du code qui a évolué sans mise à jour des tests. Situation incompatible avec la discipline TDD prescrite.
- **Résultat attendu** : tous les tests passent au vert. Les tests cassés concernent principalement le parsing Excel (`test_excel_import_parsers.py`, `test_excel_import_parsing.py`) et l'API d'import de test.
- **Tests en échec identifiés** :
	- `test_parse_invoice_sheet_extracts_optional_cs_a_components`
	- `test_parse_invoice_sheet_accepts_zero_value_cs_a_component`
	- `test_parse_invoice_sheet_blocks_inconsistent_explicit_cs_a_components`
	- `test_parse_payment_sheet_normalizes_payment_fields`
	- `test_parse_cash_sheet_ignores_safe_rows_and_parses_signed_amount`
	- `test_parse_bank_sheet_ignores_balance_description_and_parses_credit_debit`
	- `test_parse_entries_sheet_ignores_zero_rows_and_reports_invalid_amounts`
	- `test_parse_entries_sheet_keeps_change_num_marker`
	- `test_parse_date_handles_datetime_and_string_formats`
	- 2 autres échecs dans la même famille
	- 1 erreur sur `test_test_import_shortcuts_list_and_run_configured_file`

### BL-049 — Remonter la couverture de test

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point T2).
- **Pourquoi** : la couverture de test backend est à 29 %, loin des objectifs fixés par le projet (services métier ≥ 90 %, API ≥ 80 %, composables frontend ≥ 70 %). Certains services critiques sont à peine couverts (`settings.py` 21 %, `salary_service.py` 25 %).
- **Résultat attendu** : monter la couverture de manière incrémentale ; viser un palier intermédiaire réaliste de 60 % global avant d'attaquer les cibles finales. Prioriser les services métier critiques (accounting engine, fiscal year, payment, invoice).
- **Point d'attention** : ce ticket est un chantier continu ; chaque nouvelle fonctionnalité doit respecter les cibles de couverture dès la livraison.

### BL-050 — Refactorer `excel_import.py` en package

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point P1).
- **Pourquoi** : `services/excel_import.py` fait 5 038 lignes. C'est un god module ingérable qui concentre plus de 15 blocs `except Exception` et rend la revue de code, le test ciblé et la maintenance pratiquement impossibles.
- **Résultat attendu** : transformer `services/excel_import.py` en un package `services/excel_import/` avec des sous-modules dédiés (orchestrateur, contacts, factures, paiements, comptabilité, salaires), chacun sous les 500 lignes. Conserver les mêmes interfaces publiques pour ne pas casser les routeurs ni les tests existants.
- **Point d'attention** : ce refactoring doit être purement structurel, sans changement de comportement. Les tests existants doivent rester au vert tout au long du processus. `import_reversible.py` (3 030 lignes) est un candidat similaire pour un second lot.

### BL-051 — Numérotation des écritures comptables thread-safe

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point C1).
- **Pourquoi** : `_next_entry_number()` utilise `SELECT COUNT(*)` pour générer le numéro séquentiel suivant. Deux requêtes concurrentes peuvent produire le même numéro. Avec 1 worker Uvicorn et SQLite, le risque est faible mais viole le principe de fiabilité comptable.
- **Résultat attendu** : remplacer `COUNT(*)` par `SELECT MAX(entry_number)` avec un verrou approprié, ou utiliser une séquence SQLite (`INSERT` + `last_insert_rowid`). La solution doit garantir l'unicité même en cas de requêtes async concurrentes.
- **Point d'attention** : vérifier que le changement n'impacte pas les tests existants qui supposent une numérotation consécutive.

### BL-052 — Désactiver ou protéger `reset-db` en production

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point S5).
- **Pourquoi** : `POST /api/settings/reset-db` efface toutes les données applicatives et n'est protégé que par le rôle ADMIN. Pas de confirmation supplémentaire, pas de log d'audit, et l'endpoint est actif en production.
- **Résultat attendu** : au minimum, désactiver cet endpoint quand `debug=False`. Idéalement, ajouter une double confirmation (re-saisie du mot de passe admin) même en mode debug.
- **Point d'attention** : le reset sélectif de `BL-015` offre déjà une alternative plus ciblée ; `reset-db` ne devrait servir qu'en environnement de test.

### BL-053 — Forcer le changement du mot de passe admin au premier login

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point S6).
- **Pourquoi** : le bootstrap crée un admin avec le mot de passe `changeme`. Si l'administrateur ne le change pas, l'application reste accessible avec des credentials triviaux indéfiniment.
- **Résultat attendu** : ajouter un flag `must_change_password` au modèle `User`. L'activer au bootstrap et après chaque reset administrateur. L'application doit rediriger vers un écran de changement de mot de passe tant que ce flag est actif, et bloquer l'accès aux autres fonctionnalités.
- **Point d'attention** : ne pas casser le flow de test automatisé ; le flag doit pouvoir être désactivé en fixture de test.

### BL-054 — Séparer les migrations Alembic du démarrage Uvicorn

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point K1).
- **Pourquoi** : le `CMD` Docker fait `alembic upgrade head && uvicorn ...`. Si la migration échoue, le `&&` shell masque la cause. De plus, les migrations s'exécutent à chaque redémarrage du conteneur.
- **Résultat attendu** : utiliser un script `entrypoint.sh` dédié avec gestion d'erreurs explicite, ou séparer la migration dans un step `docker-compose` distinct.

### BL-055 — Configurer les origines CORS pour la production

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point S4).
- **Pourquoi** : en mode production (`debug=False`), `allow_origins=[]` bloque toute origine. Le frontend servi depuis le même conteneur fonctionne (même origine), mais un accès via reverse proxy ou sous-domaine serait bloqué silencieusement.
- **Résultat attendu** : ajouter un paramètre `cors_allowed_origins` dans les settings pour la production, ou ne pas configurer CORS du tout si le frontend est toujours servi du même domaine (ce qui est le cas dans l'architecture mono-conteneur actuelle).

### BL-056 — Journal d'audit structuré

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point S8).
- **Pourquoi** : les échecs de connexion, les changements de rôle, les suppressions de données et les accès aux endpoints dangereux ne sont pas tracés dans un journal d'audit structuré. Le log applicatif standard ne suffit pas pour un contexte associatif gérant des données financières.
- **Résultat attendu** : implémenter un journal d'audit minimal (table dédiée ou log structuré JSON) traçant au minimum les connexions réussies/échouées, les changements de rôle et d'activation, les réinitialisations de mot de passe, et les opérations de suppression massive.

### BL-057 — TypeDecorator Decimal pour l'ORM

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point C2).
- **Pourquoi** : environ 30 occurrences de `Decimal(str(e.debit))` et similaires sont éparpillées dans les services. Les colonnes `Numeric` de SQLAlchemy avec `aiosqlite` retournent parfois des `float` au lieu de `Decimal`. Le contournement fonctionne mais est fragile et verbeux.
- **Résultat attendu** : créer un `TypeDecorator` SQLAlchemy personnalisé qui garantit le retour en `Decimal` nativement, puis éliminer les conversions manuelles.
- **Point d'attention** : vérifier la compatibilité avec les migrations Alembic existantes ; le type stocké ne doit pas changer.

### BL-058 — Typer les exceptions dans l'import Excel

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point C3).
- **Pourquoi** : plus de 15 blocs `except Exception` dans `excel_import.py` et les routeurs associés. Ce pattern attrape tout, y compris des erreurs de programmation, et masque les problèmes.
- **Résultat attendu** : remplacer les `except Exception` par des exceptions métier typées (`ImportParseError`, `ImportValidationError`, etc.) et ne garder les catches génériques qu'au point d'entrée du routeur, avec un log explicite.
- **Point d'attention** : ce ticket dépend logiquement de `BL-050` (refactoring du module) ; il peut être traité en même temps ou juste après.

### BL-059 — Pagination bornée par défaut

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point C4).
- **Pourquoi** : tous les endpoints de liste (`/invoices/`, `/contacts/`, `/payments/`, etc.) ont `limit=None` par défaut. Un client peut récupérer la totalité de la base en une seule requête, ce qui est un risque de déni de service.
- **Résultat attendu** : ajouter un `limit` par défaut de 100 et un `max_limit` de 1 000 sur tous les endpoints de liste. Adapter le frontend si nécessaire pour paginer.

### BL-060 — Retirer `create_all` de `init_db()`

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point D1).
- **Pourquoi** : `init_db()` appelle `Base.metadata.create_all` en plus des migrations Alembic. Si une migration est oubliée, `create_all` masque le problème en dev mais pas en production. C'est une source classique de divergence de schéma.
- **Résultat attendu** : retirer `create_all` de `init_db()` et se reposer uniquement sur Alembic. Conserver `create_all` uniquement dans la fixture de test (`conftest.py`).

### BL-061 — Docker HEALTHCHECK

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point K2).
- **Pourquoi** : ni le Dockerfile ni le docker-compose ne déclarent de health check. Le NAS Synology ne peut pas savoir si l'application est fonctionnelle après un redémarrage.
- **Résultat attendu** : ajouter un `HEALTHCHECK` dans le Dockerfile ciblant un endpoint léger (ex. `/api/docs` ou un `/api/health` dédié) et un `healthcheck:` correspondant dans `docker-compose.yml`.

### BL-062 — Synchroniser les versions frontend / backend

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point F3).
- **Pourquoi** : `pyproject.toml` indique version `0.1.0` alors que `package.json` affiche `0.0.0`. Les versions doivent être synchronisées pour la traçabilité des releases.
- **Résultat attendu** : aligner `package.json` sur `0.1.0` et s'assurer que le processus de release (documenté dans les instructions Copilot) met à jour les deux fichiers systématiquement.

### BL-063 — Retirer les noms personnels du plan comptable par défaut (RGPD)

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point D3).
- **Pourquoi** : le plan comptable par défaut dans `models/accounting_account.py` contient des noms de personnes réelles en dur (« Riad ALIOUCHE », « Fatou NDOYE/AST »). Ces données personnelles ne doivent pas figurer dans le code source d'un dépôt potentiellement public.
- **Résultat attendu** : remplacer ces noms par des libellés génériques (« Client litigieux 1 », « Client litigieux 2 ») ou supprimer ces sous-comptes du plan par défaut.
- **Point d'attention** : ces comptes sont marqués `is_active=False` et `is_default=True` ; ils existent probablement déjà en base pour les imports historiques. La migration doit préserver les données existantes.

### BL-064 — Supprimer `stores/counter.ts` (code mort)

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point O3).
- **Pourquoi** : fichier `stores/counter.ts` généré automatiquement par le scaffolding Vue.js `create-vue`, non utilisé dans l'application.
- **Résultat attendu** : supprimer le fichier.

### BL-065 — Éliminer `__allow_unmapped__` du modèle Payment

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point P3).
- **Pourquoi** : le modèle `Payment` utilise `__allow_unmapped__ = True` pour porter des attributs transients (`invoice_number`, `invoice_type`) qui ne sont pas des colonnes. Ce pattern mélange données persistées et données calculées sur le même objet ORM, rendant le modèle ambigu.
- **Résultat attendu** : déplacer ces attributs vers le schéma Pydantic `PaymentRead` ou un DTO dédié, et retirer `__allow_unmapped__`.

### BL-066 — Settings singleton avec `@lru_cache`

- **Dates** : `created=2026-04-22`
- **Origine** : audit technique du `2026-04-22` (`doc/dev/audit-report-2026-04.md`, point C6).
- **Pourquoi** : le singleton `get_settings()` utilise un pattern `global _settings` mutable. Avec 1 worker Uvicorn le risque est nul, mais un simple `@lru_cache` serait plus idiomatique et thread-safe.
- **Résultat attendu** : remplacer le pattern actuel par `@lru_cache` sur `get_settings()`, comme recommandé par la documentation FastAPI.


## Détail des sujets fermés

### BL-001 — Stabiliser la méthode de triage du backlog

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : éviter que les retours de tests, idées d'amélioration et changements de cap restent seulement dans l'historique de conversation.
- **Résultat attendu** : une règle simple d'entrée dans le backlog, de priorisation et de mise à jour au fil du travail.
- **Livré parce que** : le backlog est maintenant utilisé comme support de suivi versionné, avec statuts, priorités et mises à jour récurrentes.

### BL-002 — Documentation utilisateur import/reset

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : l'écran d'import a été clarifié, mais il fallait une documentation utilisateur durable et centralisée.
- **Résultat attendu** : une documentation en français expliquant la différence entre import `Gestion` et `Comptabilité`, le lien avec les exercices, le rôle du plan comptable et des règles, la coexistence comptable et la portée exacte de la réinitialisation.
- **Livré parce que** : la documentation utilisateur a été rédigée dans `doc/user/import-excel-et-reinitialisation.md` avec un mode d'emploi orienté reprise et tests manuels.

### BL-003 — Campagne de retest métier sur imports réels

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : plusieurs corrections récentes ont modifié l'import fournisseurs, la coexistence comptable, les dates et la lisibilité UI.
- **Résultat attendu** : une nouvelle passe de tests manuels structurés sur les fichiers historiques réels, avec une liste courte d'écarts résiduels.
- **Livré parce que** : le rejeu réel sur base isolée a confirmé l'absence d'écart bloquant ; la procédure a seulement été ajustée pour refléter les nouveaux compteurs et le besoin de précharger les exercices couvrant toutes les dates utiles.

### BL-004 — Historique d'import réversible dans l'interface

- **Dates** : `created=2026-04-12`, `started=2026-04-20`, `completed=2026-04-20`
- **Pourquoi** : l'application conserve déjà des traces techniques d'import, mais elles restent peu visibles pour l'utilisateur.
- **Résultat attendu** : un écran ou panneau affichant les imports passés, leur type, leur date, leur résultat, les principales anomalies, et un niveau de traçabilité suffisant pour comprendre quelles opérations ont été préparées puis exécutées, quels objets elles ont créés ou modifiés, et permettre un `undo/redo` au niveau opération ou import complet.
- **Cadrage produit acté** : un import doit d'abord analyser le fichier Excel et construire une liste ordonnée d'opérations métier persistées ; l'import réel consiste ensuite à exécuter ces opérations. Chaque opération doit porter son état initial, son état appliqué, sa logique `do`, sa logique `undo`, et pouvoir être rejouée tant que les préconditions strictes de cohérence sont respectées.
- **Règles actées à ce stade** :
	- l'annulation est `stricte` : on bloque `undo` ou `redo` si l'état courant d'un objet touché ne correspond plus à l'état attendu ;
	- le `redo` porte sur les opérations persistées par Solde, pas sur le fichier source ;
	- l'UI d'import doit pouvoir présenter la liste ordonnée des opérations préparées avant leur exécution, afin que l'utilisateur puisse relire ce qui va être joué ;
	- la granularité visible d'une opération doit rester métier et source-centrée (ligne ou groupe de lignes Excel cohérent), et non se limiter à chaque objet SQL créé individuellement ;
	- une opération visible peut produire plusieurs effets internes sur plusieurs objets (création, modification, régénération, lien, suppression logique), qui servent de base à l'exécution et à l'annulation ;
	- l'UI doit permettre `undo` / `redo` d'une opération individuelle, `undo` de tout l'import, et idéalement `redo` complet d'un import entièrement annulé ;
	- un import partiellement annulé doit apparaître avec un statut `partiellement annulé`, et un import totalement annulé avec un statut `annulé` ;
	- le réimport du fichier Excel reste une action distincte, possible une fois l'import annulé, mais ce n'est pas le mécanisme de `redo`.
- **Point d'attention** : le résumé sérialisé actuel dans `import_logs` ne suffira probablement pas ; la cible implique un vrai journal d'opérations réversibles avec ordre d'exécution, décision de preview (`apply`, `ignore`, `block`), effets détaillés par objet touché, état avant, état après et statut courant.
- **Résultat livré** : le backend persiste désormais des `runs`, `operations` et `effects` réversibles, l'API expose le cycle `prepare -> execute -> undo/redo` ainsi qu'un historique unifié `runs + import_logs`, l'écran d'import permet de prévisualiser les opérations préparées, et l'historique dispose d'une page dédiée pour consulter, annuler ou rejouer les imports passés.
- **Livré parce que** : les migrations, le moteur réversible, l'API, l'UI et les tests backend/frontend ciblés sont implémentés et validés localement le `2026-04-20`, y compris la stabilisation du cas où un paiement du même classeur doit se rapprocher d'une facture seulement préparée plus haut dans le run.

### BL-005 — Politique de coexistence import / écritures existantes

- **Dates** : `created=2026-04-12`, `started=2026-04-19`, `completed=2026-04-19`
- **Pourquoi** : l'import historique a désormais des garde-fous solides, mais la politique cible n'est pas encore entièrement tranchée quand des écritures manuelles, des écritures auto-générées ou des doublons métier proches coexistent déjà en base.
- **Résultat attendu** : une politique explicite, documentée et testée qui dit pour chaque cas de coexistence ce qui doit être bloqué, toléré, ignoré comme doublon ou remonté pour revue manuelle avant d'ouvrir davantage l'import `Comptabilite` en réel.
- **Résultat livré** : la politique de coexistence actuellement implémentée est maintenant explicitée dans `doc/dev/bl-005-politique-coexistence-imports.md` et traduite dans le code et les tests avec trois diagnostics distincts pour les imports `Comptabilite` : `entry-existing` pour le doublon exact, `entry-covered-by-solde` pour une ligne déjà couverte par Solde, et `entry-near-manual` pour une proximité non bloquante avec une écriture `MANUAL` existante.
- **Critère d'acceptation** : à lecture de la preview, un utilisateur doit comprendre sans ambiguïté pourquoi un cas coexistence est bloqué, toléré ou seulement signalé, et la même décision doit être respectée à l'import réel.
- **Livré parce que** : la PR `#20` a été mergée dans `develop` le `2026-04-19` après validation backend/frontend complète, avec documentation dédiée, diagnostics structurés et couverture de tests associée.

### BL-006 — Warnings de dépréciation FastAPI

- **Dates** : `created=2026-04-12`, `started=2026-04-21`, `completed=2026-04-21`
- **Pourquoi** : la suite complète remonte encore des warnings autour de `HTTP_422_UNPROCESSABLE_ENTITY`.
- **Résultat attendu** : éliminer ces warnings pour garder une base de tests propre et limiter le risque de casse lors des montées de version.
- **Résultat livré** : les routes concernées utilisent désormais `HTTP_422_UNPROCESSABLE_CONTENT`, et la suite backend validée sur le dépôt courant ne remonte plus de warning de dépréciation lié à l'ancienne constante.
- **Livré parce que** : la vérification du `2026-04-21` confirme l'absence d'occurrence restante de `HTTP_422_UNPROCESSABLE_ENTITY` dans le code Python du dépôt, et `pytest tests/ -W default::DeprecationWarning -q` passe sans warning de dépréciation FastAPI associé.

### BL-007 — Source de vérité backlog vs issues GitHub

- **Dates** : `created=2026-04-12`, `completed=2026-04-13`
- **Pourquoi** : il faut éviter une divergence future entre backlog Git et éventuelles issues GitHub.
- **Résultat attendu** : une convention claire sur l'outil qui fait foi et les cas où un doublon assumé serait acceptable.
- **Livré parce que** : la convention de travail actuelle est suffisamment claire pour l'instant : `doc/backlog.md` reste la source de vérité, et un éventuel relais vers des issues GitHub ne sera rouvert que si le mode de collaboration change.

### BL-008 — Import Excel comme validation itérative de convergence

- **Dates** : `created=2026-04-12`, `started=2026-04-18`, `completed=2026-04-18`
- **Pourquoi** : l'import Excel ne doit pas seulement servir à la reprise initiale 2024/2025 ; il doit aussi devenir un garde-fou qualité pendant la période de double tenue Excel + Solde.
- **Phase 1** : initialiser proprement Solde à partir des fichiers historiques existants.
- **Phase 2** : réimporter régulièrement Excel pour vérifier que les écritures et mouvements saisis dans Solde correspondent exactement à la réalité comptable de référence.
- **Résultat attendu** : détecter toute écriture manquante, en trop ou divergente, avec un haut niveau d'exigence sur montants, dates, libellés et équilibres, et une politique claire sur ce qui reste bloquant versus seulement signalé.
- **Objectif métier clarifié au 2026-04-18** : après un import initial, vérifier que ce qui est ensuite généré dans Solde et ce qui continue à être saisi dans Excel restent cohérents sur les invariants métier essentiels, plutôt que d'exiger une identité aveugle ligne à ligne sur tout l'historique ou d'attendre qu'un seul fichier Excel recouvre à lui seul tout ce qui existe dans Solde.
- **Invariants métier à contrôler** :
	- les factures clientes sont cohérentes dans les deux sens, mais sur des périmètres différents : côté `Solde -> Excel`, seules les factures appartenant à la vraie période/exercice du fichier doivent être attendues dans Excel ; côté `Excel -> Solde`, toutes les factures encore présentes dans Excel, même anciennes car non soldées, doivent exister aussi dans Solde ;
	- les soldes des comptes de trésorerie sont cohérents entre Solde et Excel (`Banque`, `Caisse`, remises/chèques à déposer) ;
	- les soldes comptables des comptes structurants sont identiques entre Solde et Excel (`clients`, `fournisseurs`, `banque`, `caisse`, `chèques à déposer`, autres comptes pivots de rapprochement), sans exiger que le détail des écritures soit identique ligne à ligne si les deux systèmes modélisent différemment une même opération ;
	- les paiements/règlements sont cohérents avec les factures ouvertes et soldées : pas de facture marquée payée d'un côté et impayée de l'autre, pas de règlement orphelin ou dupliqué ;
	- les comparaisons métier qui dépendent d'écritures dérivées doivent être raisonnées sur l'ensemble `Gestion + Comptabilite`, et non sur un seul fichier pris isolément, en particulier quand `Comptabilite` porte des ventilations ou des splits absents de `Gestion` ;
	- les écarts acceptables doivent être explicitement normalisés par politique métier (différences de granularité, projections fournisseur, écritures d'ouverture, reports historiques encore ouverts), et tout le reste doit ressortir comme divergence réelle ;
	- la cible finale n'est pas l'absence totale d'écart brut, mais le fait que tous les écarts restants soient prévisibles, explicables et progressivement réduits à mesure que les règles métier de comparaison sont enrichies.
- **Décisions de cadrage issues de `BL-026`** :
	- prévoir deux modes de comparaison distincts : `convergence globale` pour comparer l'état final Excel et l'état final Solde, y compris les écritures d'ouverture et les écritures importées depuis `Comptabilite`, et `validation du moteur Gestion` pour comparer seulement les écritures générées par `Gestion` avec les écritures Excel correspondant aux mêmes événements métier ;
	- ne pas imposer une identité ligne à ligne comme unique cible : certaines différences de structure doivent être rapprochées par des règles métier explicites ;
	- pour les fournisseurs, considérer comme cas normalisable le fait qu'Excel porte souvent un paiement direct (`charge -> banque/caisse`) alors que Solde modélise `facture fournisseur -> règlement` ;
	- pour les factures clients mixtes de type `cs+a`, considérer au contraire que la ventilation multi-comptes observée dans Excel exprime une réalité comptable cible et non un simple artefact de rapprochement ;
	- sur les salaires, ne pas ouvrir de sujet correctif tant qu'aucun écart métier de montant n'est démontré ; au besoin, formaliser seulement une convention de date et de regroupement pour la comparaison.
	- pour les factures clients, la comparaison `Solde -> Excel` ne doit pas prendre comme borne la première ou la dernière facture visible dans le classeur, car `Gestion 2025` peut conserver quelques factures beaucoup plus anciennes encore impayées ; le périmètre des `extra_in_solde` doit être borné par la vraie plage de l'exercice du fichier, tandis que la comparaison inverse `Excel -> Solde` doit continuer à vérifier toutes les factures effectivement présentes dans le classeur, y compris les anciennes restées ouvertes ; la même asymétrie de périmètre devra être confirmée ou non pour les autres domaines (`Paiements`, `Caisse`, `Banque`).
	- pour rendre cette règle opérationnelle sur `Factures`, un fichier nommé `Gestion YYYY` doit être interprété comme l'exercice démarrant au mois `fiscal_year_start_month` de l'année `YYYY` et se terminant la veille du même mois l'année suivante ; si le nom du fichier ne permet pas de déduire l'exercice, la comparaison peut retomber provisoirement sur les dates visibles dans le classeur.
	- pour `Paiements / règlements`, la comparaison bidirectionnelle doit suivre la même fenêtre d'exercice `Gestion YYYY` pour le périmètre temporel principal, y compris quand cet exercice déborde sur l'année civile suivante ; le contrôle complémentaire des paiements rattachés à des factures anciennes encore ouvertes reste un sujet distinct.
	- pour `Banque`, le sens `Solde -> Excel` doit suivre la plage réelle couverte par le relevé visible dans le classeur, et cette plage peut recouvrir plusieurs années civiles même si aucune ligne n'existe dans l'une d'elles ; les `extra_in_solde` doivent donc être cherchés sur toute la fenêtre de dates, pas seulement sur les années explicitement présentes dans les lignes du fichier.
	- pour `Caisse`, le sens `Solde -> Excel` doit suivre la plage réelle couverte par le registre visible dans le classeur, avec la même vigilance que pour `Banque` sur les années intermédiaires absentes des lignes affichées ; les `extra_in_solde` doivent être cherchés sur toute la fenêtre de dates, en excluant toujours le solde d'ouverture système.
- **Grille de contrôle cible par domaine** :
	- `Factures` :
	  - **Source de vérité** : `Gestion` pour la présence des pièces ouvertes/soldées ; `Comptabilite` pour les ventilations dérivées quand une facture `cs+a` ou une règle de projection produit plusieurs lignes comptables.
	  - **Sens de comparaison** : `Excel -> Solde` sur toutes les factures encore visibles dans le fichier ; `Solde -> Excel` seulement sur la vraie période/exercice du fichier.
	  - **Invariants à vérifier** : existence des factures, montant total, statut métier (`ouverte`, `partielle`, `soldée`), reste dû, rattachement au bon contact.
	  - **Écarts acceptables** : factures historiques encore ouvertes hors période d'exercice ; différences de ventilation comptable si le total et le reste dû restent cohérents.
	- `Paiements / règlements` :
	  - **Source de vérité** : `Gestion` pour les paiements clients et les règlements simples ; `Gestion + Compta` quand la contrepartie comptable doit être reconstituée.
	  - **Sens de comparaison** : bidirectionnel sur la période du fichier, avec contrôle complémentaire des paiements rattachés à des factures encore ouvertes dans Excel.
	  - **Invariants à vérifier** : pas de règlement orphelin, pas de doublon significatif, même facture soldée/non soldée des deux côtés, mêmes montants encaissés/décaisés par pièce.
	  - **Écarts acceptables** : différences de granularité technique tant que le total réglé par facture et le statut de solde restent identiques.
	- `Banque` :
	  - **Source de vérité** : `Gestion` pour les mouvements bancaires importés ; `Comptabilite` pour vérifier les soldes de comptes et les projections induites.
	  - **Sens de comparaison** : `Excel -> Solde` sur tous les mouvements du fichier ; `Solde -> Excel` borné à la période du relevé/exercice contrôlé.
	  - **Invariants à vérifier** : même solde bancaire final, mêmes mouvements significatifs non rapprochés, mêmes remises/chèques en transit.
	  - **Écarts acceptables** : lignes descriptives de solde, écritures d'ouverture, regroupements techniques explicitement normalisés.
	- `Caisse` :
	  - **Source de vérité** : `Gestion` pour les mouvements de caisse ; `Comptabilite` pour la cohérence du compte de caisse et des projections associées.
	  - **Sens de comparaison** : bidirectionnel sur la période du fichier, avec borne métier d'exercice et exclusion explicite du solde d'ouverture système.
	  - **Invariants à vérifier** : même solde de caisse, mêmes entrées/sorties significatives, pas d'écart inexpliqué sur les remises d'espèces ou les décaissements fournisseurs.
	  - **Écarts acceptables** : solde initial, prévisions de remise d'espèces ou regroupements normalisés par politique métier.
	- `Comptabilité / comptes pivots` :
	  - **Source de vérité** : `Comptabilite` pour les écritures de référence ; `Gestion` sert d'entrée métier mais ne suffit pas à lui seul pour comparer les écritures dérivées.
	  - **Sens de comparaison** : comparaison des soldes et des groupes d'écritures sur la période, pas identité brute ligne à ligne si les deux systèmes modélisent différemment la même opération.
	  - **Invariants à vérifier** : mêmes soldes sur les comptes structurants (`clients`, `fournisseurs`, `banque`, `caisse`, `chèques à déposer`, autres comptes de rapprochement), mêmes équilibres par groupe métier important.
	  - **Écarts acceptables** : une opération détaillée en `2` écritures dans Excel et `4` dans Solde si le résultat comptable final, les soldes et le sens des comptes restent identiques.
	- `Écarts résiduels` :
	  - **Objectif** : tout écart restant doit être classé comme `attendu et expliqué par une règle métier`, `toléré mais à surveiller`, ou `anomalie réelle`.
	  - **Critère de maturité BL-008** : les écarts non expliqués doivent tendre vers zéro, et chaque nouvelle passe de recette doit enrichir les règles de comparaison pour rendre les écarts restants prévisibles et compréhensibles.
- **Premier lot visé** :
	- formaliser ces deux modes de validation (`convergence globale` et `validation du moteur Gestion`) et leurs périmètres respectifs ;
	- formaliser un contrat de comparaison par domaine (`Factures`, `Paiements`, `Caisse`, `Banque`, `Journal`) ;
	- ajouter un mode de comparaison sans écriture, probablement adossé à la preview existante ;
	- catégoriser les écarts avec des codes stables (`missing-in-solde`, `extra-in-solde`, `amount-mismatch`, `date-mismatch`, `ambiguous-match`, `ignored-by-policy`, `blocked-by-coexistence`) ;
	- porter explicitement des règles de projection ou de normalisation pour les cas attendus (`facture fournisseur + règlement` côté Solde vs paiement direct côté Excel, ouvertures d'exercice, autres écarts de granularité assumés) ;
	- produire un rapport exploitable avec résumé global, détail par feuille et exemples d'écarts ;
	- cibler d'abord la chaîne réelle `Gestion 2024` / `Gestion 2025` avant toute généralisation plus large.
- **Critère d'acceptation** : on doit pouvoir répondre, sans rien persister, à quatre questions simples pour chacun des deux modes : qu'est-ce qui manque dans Solde, qu'est-ce qui est en trop, qu'est-ce qui diverge, et qu'est-ce qui est ignoré volontairement selon la politique métier.
- **Hors périmètre initial** : pas de correction automatique des écarts, pas d'ouverture large de l'import `Comptabilite` en réel tant que `BL-005` n'est pas tranché, et pas d'outil générique de réconciliation déconnecté du cas de reprise réel.
- **Enjeu** : sujet critique pour la confiance métier pendant toute la transition hors Excel.
- **Résultat livré au 2026-04-18** : les deux premiers lots prévus sont désormais intégrés dans `develop` dans la preview sans écriture : `Gestion` expose le delta `Excel -> Solde` avec le sens inverse `extra_in_solde`, `Comptabilite` expose un mode `convergence globale` bidirectionnel, et une recette locale rejouable est désormais documentée dans `doc/dev/bl-008-recette-convergence.md` via `scripts/run_excel_convergence_preview.py`.

### BL-009 — Enrichir le plan comptable par défaut à partir des imports réels

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : le rejeu réel des fichiers `Gestion` et `Comptabilité` faisait apparaître davantage de comptes que ceux seedés par défaut.
- **Résultat attendu** : un plan comptable par défaut plus proche des comptes réellement utilisés, pour améliorer journal, balance, grand livre et compte de résultat.
- **Livré parce que** : le seed par défaut a été enrichi avec les comptes récurrents observés ; les sous-comptes historiques `401103`, `401104`, `416001` et `416002` sont conservés comme inactifs pour préserver les libellés et les états sur l'historique importé.

### BL-010 — Stratégie de clôture des exercices historiques importés

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : lors d'une reprise historique, il faut éviter de recréer dans Solde des écritures de clôture et de report à nouveau déjà présentes dans Excel.
- **Résultat attendu** : une stratégie explicite et sûre pour garder un seul exercice courant ouvert sans fausser le journal historique.
- **Livré parce que** : la stratégie retenue consiste à laisser les exercices historiques ouverts pendant la reprise, puis à les clôturer administrativement sans générer de nouvelles écritures de clôture ni de report à nouveau.

### BL-011 — Exercice courant global et suppression des plafonds arbitraires par écran

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : plusieurs écrans chargeaient un sous-ensemble borné puis filtraient localement, ce qui devenait incohérent dès que le volume augmentait.
- **Résultat attendu** : un exercice courant global, visible et partagé, servant de filtre métier par défaut sur les écrans principaux.
- **Livré parce que** : un store global d'exercice, un sélecteur partagé et le branchement des écrans comptables sur l'exercice courant ont été mis en place, avec correction du choix automatique de l'exercice ouvert couvrant la date du jour.

### BL-012 — Liste des paiements : référence visible et édition directe

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : la liste des paiements ne montrait plus la référence métier et ne permettait plus de correction rapide depuis l'écran principal.
- **Résultat attendu** : afficher la colonne `Référence` et permettre l'édition directe d'un paiement existant.
- **Livré parce que** : la vue expose maintenant la référence, un bouton d'édition par ligne et un dialogue de modification branché sur `PUT /payments/{id}`.

### BL-013 — Journal de caisse : référence, détail et édition directe

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : le journal de caisse n'affichait pas la référence métier et ne permettait ni consultation détaillée ni correction rapide.
- **Résultat attendu** : afficher la référence, proposer un détail consultable et permettre l'édition directe d'une écriture.
- **Livré parce que** : la vue dispose maintenant d'une référence visible, d'un panneau de détail, d'une édition directe et d'un recalcul cohérent des soldes après modification.

### BL-014 — Journal comptable : lisibilité métier et navigation vers les factures

- **Dates** : `created=2026-04-12`, `completed=2026-04-12`
- **Pourquoi** : le journal exposait surtout des lignes comptables brutes, peu utiles sans libellé, référence métier, tiers lié ou action de consultation.
- **Résultat attendu** : enrichir le journal avec les libellés de comptes, les références métier, le nom du tiers, le détail d'écriture, l'édition des écritures manuelles et, quand c'est possible, un accès direct à la facture concernée.
- **Livré parce que** : le backend et le frontend ont été enrichis pour fournir ces informations, consulter le détail, éditer les paires manuelles et naviguer directement vers les factures correspondantes.

### BL-015 — Reset sélectif orienté reprise d'import

- **Dates** : `created=2026-04-13`, `started=2026-04-20`, `completed=2026-04-20`
- **Pourquoi** : le reset global actuel est utile pour les essais complets, mais il reste trop brutal quand on veut simplement rejouer une filière d'import, un exercice ou une séquence de reprise précise.
- **Recadrage après BL-004** : le cycle `prepare -> execute -> undo/redo` couvre désormais le cas standard de rejeu sûr pour les nouveaux imports réversibles, au niveau d'une opération ou d'un run complet. `BL-015` ne vise donc plus à rejouer ces imports normaux, mais les cas où le journal réversible ne suffit pas ou n'existe pas.
- **Résultat attendu** : proposer un reset plus fin, compréhensible et sûr, capable de supprimer uniquement le périmètre utile à rejouer tout en explicitant le traitement des journaux d'import et des dépendances métier, en particulier pour les imports legacy, les données modifiées après coup qui bloquent un `undo` strict, ou les nettoyages administratifs ciblés par filière, période ou exercice.
- **Livré parce que** : l'administration expose maintenant un reset sélectif avec prévisualisation puis exécution pour un couple `type d'import + exercice`, le backend s'appuie sur les traces `import_logs` et `import_runs` pour retrouver les objets racines puis supprimer aussi, côté `Gestion`, les dépendances métier dérivées explicitement cadrées, l'interface `Paramètres` est branchée de bout en bout, la documentation utilisateur a été consolidée, et toute la matrice de validation locale est passée, y compris `pytest tests/` (`710 passed`), `ruff`, `mypy`, `vue-tsc`, `eslint` et `vitest`.
- **Point d'attention** : ce sujet ne doit pas fragiliser l'intégrité des données ; il faut privilégier des scénarios de reset explicitement cadrés plutôt qu'un outil générique trop puissant, et éviter tout chevauchement fonctionnel inutile avec le journal réversible de `BL-004`.

### BL-016 — Harmonisation i18n et microcopie UI

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Pourquoi** : malgré la forte couverture i18n actuelle, il reste encore des libellés incohérents, des formulations hétérogènes et potentiellement quelques textes en dur qui dégradent la perception de qualité.
- **Résultat attendu** : auditer puis corriger les libellés visibles pour que les écrans utilisent des clés i18n cohérentes, un vocabulaire homogène et une microcopie claire du login jusqu'aux vues métier.
- **Livré parce que** : les écrans `Banque`, `Caisse` et `Salaires` utilisent maintenant des clés i18n cohérentes pour les compteurs, états vides et libellés visibles auparavant hétérogènes ou codés en dur.
- **Point d'attention** : viser d'abord les incohérences utilisateur visibles ; éviter de renommer massivement des clés stables si le gain produit est faible.

### BL-017 — Formats de dates et périodes en français

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Pourquoi** : certaines dates ou périodes restent affichées dans un format trop technique ou ambigu, parfois plus proche d'une lecture ISO ou américaine que d'un usage métier français.
- **Résultat attendu** : uniformiser l'affichage des dates, mois et périodes au format français dans les tableaux, détails, dialogues et exports lisibles, tout en conservant les formats ISO pour les API et les échanges techniques.
- **Livré parce que** : un helper partagé formate désormais les mois en français et il est appliqué sur `Salaires` et le tableau mensuel du `Dashboard`, tout en conservant les formats ISO pour les filtres techniques et les appels API.
- **Point d'attention** : distinguer clairement stockage/échange et présentation UI pour éviter les régressions côté backend ou formulaires.

### BL-018 — Lisibilité des écrans de liste : tri, filtre et états de vue

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Pourquoi** : plusieurs écrans disposent déjà d'un filtre générique ou d'améliorations visuelles, mais l'expérience reste inégale selon les vues pour le tri, la lisibilité des colonnes, les états vides, le chargement et la compréhension du périmètre affiché.
- **Résultat attendu** : définir puis appliquer un socle UX commun pour les écrans de liste afin que recherche, tri, colonnes utiles, états vides, compteurs et chargement soient plus clairs et cohérents d'un écran à l'autre.
- **Livré parce que** : un socle DataTable partagé a été introduit pour les filtres texte, dates, intervalles numériques et multi-sélection, avec compteurs d'état harmonisés, tri/filtrage cohérents sur les principales vues de liste, prise en charge des saisies de date FR/ISO dans les filtres et retrait explicite du tri/filtrage sur les tableaux fixes `bilan` et `résultat`.
- **Point d'attention** : éviter l'uniformisation aveugle ; certaines vues métier auront toujours besoin d'adaptations spécifiques.

### BL-022 — Gestion des utilisateurs, rôles et sécurité de compte

- **Dates** : `created=2026-04-13`, `started=2026-04-13`, `completed=2026-04-19`
- **Pourquoi** : l'authentification existe déjà, mais la gestion des utilisateurs reste encore trop limitée pour un usage réel durable avec plusieurs profils, une administration claire des comptes et des attentes minimales de sécurité.
- **Résultat attendu** : faire évoluer la gestion des comptes pour couvrir un vrai cycle de vie utilisateur : rôles métier lisibles, création et administration des comptes, autonomie minimale des utilisateurs sur leur propre profil et mécanismes de sécurité cohérents pour l'accès au compte.
- **Critère d'acceptation** : un administrateur doit pouvoir gérer les comptes et leurs rôles sans intervention technique, et un utilisateur doit pouvoir accéder à son compte, gérer son profil essentiel et récupérer ou faire réinitialiser son accès selon un processus clair et sûr.
- **État de départ actuel** : l'application dispose déjà d'une authentification JWT, d'un utilisateur courant, d'une création de compte réservée à l'admin et de rôles techniques (`readonly`, `secretaire`, `tresorier`, `admin`), mais pas encore d'interface complète ni de cycle de vie cohérent du compte.
- **Résultat livré** : BL-022 couvre désormais l'ensemble du cycle de vie visé pour les comptes applicatifs : rôles métier clarifiés, administration des comptes côté `admin`, espace `Mon profil` pour consultation et mise à jour de l'e-mail, changement du mot de passe par l'utilisateur lui-même, procédure de réinitialisation administrateur adaptée au contexte auto-hébergé, invalidation des anciens jetons après changement ou reset, et documentation utilisateur/admin alignée sur ces parcours.
- **Livré parce que** : les lots 3 à 5 ont été implémentés sur `feature/bl-022-profile-account-security` avec migration de sécurité, endpoints backend dédiés, vue frontend `Mon profil`, dialogue de réinitialisation administrateur, mises à jour de navigation et de documentation, puis validation backend/frontend complète avant PR.

### BL-023 — Revalider les droits réels par rôle et la visibilité des écrans comptables

- **Dates** : `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14`
- **Pourquoi** : le retest métier après fusion de `BL-022` montre d'abord un problème de définition cible des rôles, puis des incohérences concrètes entre le comportement attendu et le comportement observé. Avant d'implémenter un changement de permissions, il faut clarifier le périmètre produit réel de chaque rôle. Côté symptômes observés, le rôle `secrétaire` semble voir une partie de la comptabilité, la visibilité de certains écrans comptables reste ambiguë selon le profil, et la zone utilisateur du shell (nom d'utilisateur et bouton de déconnexion en bas à gauche) disparaît parfois.
- **Résultat attendu** : disposer d'une matrice d'autorisations explicitement validée côté produit, puis d'un comportement vérifié en conditions réelles pour chaque rôle, avec une visibilité cohérente des écrans comptables, du sélecteur d'exercice et de la zone utilisateur du shell.
- **Précondition** : ne pas corriger les permissions au fil de l'eau sans arbitrage préalable sur la cible produit des rôles ; la discussion de cadrage fait partie du ticket.
- **Avancement actuel** : le cadrage initial a été formalisé dans `doc/dev/bl-023-cadrage-roles-et-matrice-acces.md`, puis la cible produit a été validée et implémentée : séparation visible `Gestion` / `Comptabilité` dans la navigation, nouveaux guards frontend par domaine, renommage métier `Gestionnaire` / `Comptable`, masquage du rôle `readonly` dans les options usuelles d'administration, alignement des permissions backend sur la matrice cible et ajout de tests ciblés sur les rôles.
- **Résultat livré** : la matrice produit validée est maintenant appliquée dans le code. La partie `Gestion` est accessible à `Gestionnaire`, `Comptable` et `Administrateur`, la partie `Comptabilité` est réservée à `Comptable` et `Administrateur`, la navigation est séparée visuellement par section, le sélecteur d'exercice reste disponible pour les profils métier qui consultent des écrans filtrés par exercice, et la zone utilisateur du shell reste visible avec un libellé stable sans être repoussée en bas par la hauteur des vues.
- **Point d'attention** : le rôle technique `readonly` reste présent pour compatibilité, mais n'est plus proposé comme rôle produit normal dans l'interface d'administration. Une éventuelle suppression complète ou migration explicite reste un sujet distinct.

### BL-024 — Clarifier la saisie des paiements et corriger les remises en banque automatiques

- **Dates** : `created=2026-04-13`, `started=2026-04-19`, `completed=2026-04-19`
- **Pourquoi** : en usage réel, il n'est pas clair comment un paiement doit être saisi dans l'application, et les paiements de type `espèces` ou `virement` semblent être remis en banque automatiquement dès leur encodage, ce qui pose une question de justesse métier et comptable.
- **Résultat attendu** : définir un workflow cible simple pour la création, la consultation et l'éventuelle remise en banque des paiements, puis corriger l'application pour que chaque mode de paiement suive le bon traitement.
- **Résultat livré** : la saisie manuelle standard des règlements clients est désormais recentrée sur la facture client pour `chèque` et `espèces`, avec création immédiate d'une écriture de caisse pour les espèces, dépôt manuel explicite selon le type de remise, verrouillage des modifications qui désynchroniseraient la trésorerie, et rejet explicite des `virements` côté saisie manuelle au profit du futur workflow `banque -> paiement` porté par `BL-031`.
- **Décision produit désormais retenue pour les virements** :
	- un `virement` ne doit pas être saisi d'abord comme paiement ; la source de vérité est l'entrée visible sur le relevé bancaire ;
	- le workflow cible est donc `banque -> paiement` pour les virements : import ou saisie du relevé, détection du mouvement créditeur, puis création ou rattachement du paiement correspondant ;
	- un `chèque` reste un flux `paiement -> remise en banque` ;
	- des `espèces` restent un flux `paiement -> caisse`, avec dépôt bancaire éventuel traité séparément.
- **Recadrage acté pendant la discussion** :
	- l'exploration en cours sur `fix/bl-024-payment-workflow` a permis de confirmer que l'application n'implémente aujourd'hui qu'un rapprochement bancaire superficiel (`reconciled` / `reconciled_with`) sans vrai lien métier entre ligne de banque et paiement ;
	- la piste `paiement -> banque` pour les virements a été explicitement rejetée comme cible produit ;
	- le ticket doit maintenant se concentrer sur le bon point d'entrée des paiements selon le moyen de règlement, sans considérer les virements comme des paiements saisis depuis la facture client.
- **Critère d'acceptation** : un utilisateur comprend où saisir un paiement, le fait sans détour, et les écritures ou remises générées correspondent au comportement métier attendu pour chaque mode de règlement.
- **Point d'attention** : ce sujet touche à la fois l'UX des écrans `paiements`, la logique de banque/caisse et la génération des écritures comptables associées.

### BL-031 — Construire une vraie réconciliation bancaire bout en bout

- **Dates** : `created=2026-04-19`, `started=2026-04-19`, `completed=2026-04-20`
- **Pourquoi** : le produit sait aujourd'hui importer ou saisir des opérations bancaires et les marquer comme `rapprochées`, mais ce rapprochement reste superficiel : il n'existe ni vrai lien métier entre une transaction bancaire et un paiement, ni workflow robuste pour partir d'un relevé et en déduire ou rattacher les paiements clients attendus, en particulier pour les virements.
- **Résultat attendu** : disposer d'une chaîne cohérente de réconciliation bancaire couvrant l'import des relevés, la détection des transactions utiles, leur catégorisation, la proposition de rapprochements, et la création ou le rattachement des paiements et autres mouvements métier appropriés.
- **Résultat livré** : l'écran `Banque` supporte désormais l'import `CSV` / `OFX` / `QIF`, une catégorisation initiale des transactions, la création ou la confirmation de virements clients et fournisseurs depuis le relevé, la gestion d'un virement client unique ou ventilé sur plusieurs factures, la confirmation de plusieurs règlements clients existants quand leur total correspond exactement à la ligne bancaire, et une traçabilité explicite via les liens `transaction <-> payment(s)`.
- **Premier lot visé au démarrage** : rendre les relevés `OFX` et `QIF` réellement exploitables dans l'interface `Banque`, puis enrichir chaque transaction importée d'une première catégorisation détectée automatiquement pour préparer le vrai workflow de rapprochement.
- **Avancement actuel sur la branche** : en plus de ce premier lot, l'écran `Banque` permet maintenant de traiter les virements clients et fournisseurs directement depuis les lignes du relevé : création d'un règlement à partir d'une facture ouverte ou confirmation d'un règlement déjà saisi en liant la transaction bancaire au paiement existant, avec une meilleure suggestion automatique du candidat le plus plausible selon le montant, la date, la référence, le numéro de pièce et le tiers. Pour les virements clients, une même ligne bancaire positive peut désormais soit créer plusieurs règlements ventilés sur plusieurs factures, soit confirmer plusieurs règlements clients déjà saisis quand leur total correspond exactement au montant du virement.
- **Signalement utilisateur au 2026-04-20** : quelques écarts ont été observés en recette, notamment sur le solde banque, sans diagnostic encore tranché entre import, génération d'écritures ou autre logique transverse.
- **Décision de pilotage actée** : ne pas ouvrir maintenant une chasse aux écarts isolés tant que les fonctionnalités MVP restantes ne sont pas terminées ; faire ensuite une recette bout en bout de qualification MVP et utiliser cette passe finale pour attribuer proprement chaque anomalie résiduelle à l'import, aux écritures générées ou à un autre composant.
- **Cas métier existants explicités pendant la discussion** :
	- un même virement ou chèque peut correspondre à plusieurs factures clientes ;
	- une même facture peut être réglée en plusieurs fois, par exemple avec plusieurs chèques ;
	- une même facture peut aussi être réglée par plusieurs moyens de paiement, par exemple `20 EUR` en espèces et `50 EUR` par chèque, ou `30 EUR` par chèque et `40 EUR` par virement.
- **Périmètre visé** :
	- import des relevés via les formats utiles (`QIF`, `OFX`, et si pertinent les extractions Excel ou CSV réellement utilisées) ;
	- détection des mouvements créditeurs et débiteurs significatifs ;
	- catégorisation initiale des lignes (`virement client`, `frais bancaires`, `virement interne`, `subvention`, `prélèvement`, etc.) ;
	- proposition de rapprochement avec les factures, paiements, remises et autres objets métier ;
	- création d'un paiement à partir d'une ligne bancaire quand le flux métier le justifie, notamment pour les virements clients ;
	- conservation d'un lien traçable entre la ligne de relevé, la transaction bancaire persistée, le paiement éventuel et l'objet métier final.
- **Questions à trancher** :
	- quelles sources d'import doivent être supportées en priorité dans le vrai workflow de rapprochement (`QIF`, `OFX`, CSV bancaire, export Excel) ;
	- jusqu'où pousser l'automatisation de la catégorisation avant validation humaine ;
	- quels critères de matching utiliser pour proposer un rattachement (montant exact, date, contact, libellé, référence, tolérance temporelle, fractionnement ou agrégation) ;
	- faut-il distinguer un statut `détecté`, `catégorisé`, `proposé`, `rapproché`, `confirmé` plutôt qu'un simple booléen `reconciled` ;
	- comment gérer les cas ambigus ou composites (virement groupé, paiement partiel, un virement pour plusieurs factures, référence absente ou bruitée).
- **Critère d'acceptation** : depuis un relevé importé, un utilisateur peut identifier les lignes bancaires à traiter, voir des suggestions de catégorisation et de rapprochement, confirmer le bon rattachement, puis obtenir une trace explicite entre l'opération bancaire et le paiement ou mouvement métier créé.
- **Point d'attention** : ce ticket touche au coeur du modèle de trésorerie ; il faudra éviter d'empiler un second workflow implicite par-dessus le booléen `reconciled` actuel sans refonte explicite du concept de rapprochement.

### BL-032 — Migrer en anglais la documentation technique historique restante

- **Dates** : `created=2026-04-21`, `started=2026-04-21`, `completed=2026-04-21`
- **Pourquoi** : la convention documentaire a été clarifiée, mais plusieurs documents techniques historiques restaient encore en français alors que les nouvelles docs techniques sont désormais rédigées en anglais.
- **Résultat attendu** : disposer d'une base documentaire technique cohérente en anglais pour les docs projet et techniques historiques réellement utiles au développement, à l'exploitation et au cadrage fonctionnel.
- **Résultat livré** : les documents techniques historiques restants ont été migrés en anglais sur la branche en cours, y compris `doc/architecture.md`, `doc/plan.md`, `doc/roadmap.md`, `doc/import-excel-plan.md`, `doc/plan-reprise-post-imp.md`, `doc/dev/gestion-utilisateurs-et-permissions.md`, `doc/dev/bl-005-politique-coexistence-imports.md`, `doc/dev/bl-008-recette-convergence.md`, `doc/dev/bl-023-cadrage-roles-et-matrice-acces.md`, `doc/dev/bl-026-cadrage-validation-imports-excel.md`, `doc/dev/bl-026-constat-validation-imports.md`, `doc/dev/bl-030-politique-modification-objets-valides.md`, `doc/dev/import-excel-contract.md` et `doc/dev/import-excel-procedure.md`.
- **Livré parce que** : un rescan ciblé de `doc/**/*.md` après traduction ne remonte plus de document technique historique restant en français, hors artefacts volontairement exclus par la convention comme le backlog, les notes de release et la documentation utilisateur bilingue.
- **Point d'attention** : le backlog et les notes de release restent volontairement en français ; la migration ne devait donc viser que la documentation technique, pas les artefacts de pilotage projet explicitement exclus par la convention.

### BL-044 — Convention métier des créances adhérents dans les synthèses

- **Dates** : `created=2026-04-21`, `started=2026-04-21`, `completed=2026-04-21`
- **Pourquoi** : la balance comptable des comptes tiers et le KPI `restant à payer` des factures ne racontaient pas exactement la même histoire dès qu'il existait des impayés plus anciens encore ouverts, ce qui pouvait faire croire à un écart faux alors qu'il s'agissait d'une différence de périmètre.
- **Résultat attendu** : expliciter puis implémenter une convention produit stable distinguant au minimum `reste à payer des factures de l'exercice sélectionné` et `encours adhérents total incluant les impayés historiques encore ouverts`, avec des libellés suffisamment clairs pour éviter toute confusion métier.
- **Résultat livré** : les synthèses factures client distinguent désormais clairement le `restant à payer de l'exercice` et l'`encours adhérents total`, avec un sous-texte explicite pour la part historique encore ouverte et des libellés i18n dédiés côté frontend.
- **Livré parce que** : la PR mergée a intégré les calculs séparés et l'affichage associé dans l'écran `Factures client`, ainsi que la couverture de tests correspondante.
- **Point d'attention** : si la lecture métier évolue encore, la convention devra rester alignée entre les cartes de synthèse, l'aide utilisateur et les contrôles de recette.

### BL-025 — Corriger le report à nouveau et les soldes du grand livre multi-exercices

- **Dates** : `created=2026-04-13`, `started=2026-04-13`, `completed=2026-04-13`
- **Pourquoi** : le grand livre du compte `512102` cumule au moins deux écritures d'ouverture d'exercice (`2024` et `2025`), ce qui fausse le solde affiché ; le problème est probablement plus large et remet en cause la justesse comptable des vues par compte.
- **Résultat attendu** : rétablir un calcul juste des soldes et des écritures d'ouverture dans le grand livre, en respectant une lecture strictement bornée à l'exercice choisi, sans option `tous les exercices` sur cette vue.
- **Décision produit actée** : le grand livre doit toujours afficher uniquement les transactions de l'exercice choisi ; il ne doit pas proposer `tous les exercices`, car cette agrégation rend ambigu le solde dès qu'un report à nouveau existe.
- **Questions à trancher** :
	- comment calculer le `solde d'ouverture` quand l'utilisateur borne en plus la vue avec une date de début à l'intérieur de l'exercice ;
	- le problème touche-t-il aussi le journal, la balance et d'autres comptes au-delà de `512102` ;
	- faut-il exposer séparément, plus tard, une vue d'historique brute multi-exercices distincte du grand livre.
- **Critère d'acceptation** : pour un exercice donné, le grand livre n'affiche que les écritures rattachées à cet exercice, y compris son report à nouveau éventuel, et présente un solde cohérent sans cumul indu entre ouvertures d'exercices successifs.
- **Point d'attention** : c'est un sujet comptable critique à traiter avant de faire confiance aux états ; il faudra le recouper avec `BL-010` et les choix de clôture des exercices historiques.

### BL-026 — Valider les imports Excel par rapprochement chiffré sur 2024 et 2025

- **Dates** : `created=2026-04-15`, `started=2026-04-15`, `completed=2026-04-16`
- **Pourquoi** : après la fiabilisation de la mécanique d'import, il faut maintenant confirmer sur le cas réel que les données visibles dans Solde correspondent bien aux fichiers Excel sources, aussi bien côté `Gestion` que côté `Comptabilité`, et cela sur les deux exercices historiques.
- **Résultat attendu** : disposer d'une validation explicite, exercice par exercice, des chiffres importés dans Solde par rapport aux fichiers Excel `2024` et `2025`, avec une liste claire des écarts constatés ou la confirmation qu'il n'y en a pas.
- **Résultat livré** : le cadrage de recette a été formalisé dans `doc/dev/bl-026-cadrage-validation-imports-excel.md` et un constat exploitable a été produit dans `doc/dev/bl-026-constat-validation-imports.md` pour l'exercice `2024`, avec distinction entre chiffres conformes, écarts justifiés de modélisation et sujets à corriger. Le ticket est clos comme ticket de constat et d'orientation ; la poursuite de la validation comptable stricte est désormais renvoyée vers `BL-008`, et l'alignement du comportement comptable attendu sur les factures clients mixtes vers `BL-029`.
- **Périmètre minimal** :
	- comparer les chiffres de `Gestion` visibles dans l'application avec ceux des fichiers Excel correspondants pour `2024` et `2025` ;
	- comparer les chiffres de `Comptabilité` visibles dans l'application avec ceux des fichiers Excel correspondants pour `2024` et `2025` ;
	- expliciter la méthode de rapprochement retenue par écran ou par état (totaux, comptes, journaux, soldes, volumes) ;
	- consigner tout écart résiduel avec un diagnostic exploitable pour décider s'il s'agit d'un bug, d'un problème de données source ou d'un écart de lecture métier.
- **Critère d'acceptation** : pour chacun des deux exercices, on peut produire un constat de validation lisible indiquant ce qui a été comparé, quels chiffres concordent entre Excel et Solde, et quels écarts restent ouverts le cas échéant.
- **Point d'attention** : ce ticket est complémentaire de `BL-008` ; la clôture de `BL-026` ne signifie pas que la convergence comptable Excel/Solde est entièrement démontrée, mais que les écarts restants ont été suffisamment qualifiés pour être repris dans des tickets plus ciblés.

### BL-027 — Gérer une ouverture du système explicite pour Banque et Caisse

- **Dates** : `created=2026-04-15`, `started=2026-04-15`, `completed=2026-04-16`
- **Pourquoi** : pendant la validation `BL-026`, il apparaît que le premier exercice importé a besoin d'un point de départ explicite côté gestion pour `Banque` et `Caisse`, distinct de l'ouverture comptable de l'exercice. Aujourd'hui, les lignes Excel de `solde initial` sont traitées comme des lignes ignorées, ce qui ne permet pas de représenter proprement l'état hérité du système avant le premier exercice suivi.
- **Résultat attendu** : définir puis implémenter une notion d'`ouverture du système` pour `Banque` et `Caisse`, injectée une seule fois sur le plus ancien exercice importé, contribuant aux soldes cumulés, et identifiée visiblement comme donnée spéciale dans l'interface (badge, type ou rendu distinct).
- **Résultat livré** : une ouverture du système dédiée peut être configurée côté paramètres pour la `Banque` et la `Caisse`, avec une date par défaut calée sur le plus ancien exercice ; ces écritures sont stockées avec une source explicite `system_opening`, intégrées aux soldes, affichées distinctement dans les vues de trésorerie, et exclues des comparaisons d'import pour éviter les doublons ; le constat `BL-026` confirme ensuite le comportement attendu sur les chiffres visibles.
- **Périmètre initial** :
	- gérer explicitement un solde d'ouverture `Banque` sur le premier exercice importé ;
	- gérer explicitement un solde d'ouverture `Caisse` sur le premier exercice importé ;
	- rendre ces lignes distinguables des mouvements normaux dans les écrans de trésorerie ;
	- éviter toute réinjection automatique du même concept sur les exercices suivants.
- **Critère d'acceptation** : après import du plus ancien exercice, les écrans `Banque` et `Caisse` affichent un point de départ cohérent et identifié comme `ouverture du système`, les soldes des exercices suivants héritent correctement de ce point de départ sans doublon, et les chiffres `BL-026` peuvent être remesurés proprement pour la trésorerie.
- **Livré parce que** : le commit `1faa72a` du `2026-04-15` introduit l'ouverture du système et sa gestion d'import, puis le constat `BL-026` du `2026-04-16` documente explicitement son application sur `Banque` et `Caisse`.

### BL-029 — Saisie des factures clients pilotée par types de lignes

- **Dates** : `created=2026-04-16`, `started=2026-04-16`, `completed=2026-04-19`
- **Pourquoi** : le modèle actuel demande encore un label global de facture (`cs`, `a`, `cs+a`, `general`) alors que le besoin métier cible est plus fin : l'utilisateur pense d'abord en lignes de facture, chacune portant un type métier (`cours`, `adhésion`, `autres`), puis attend que Solde calcule le total et la ventilation comptable à partir de cette saisie ; les remises doivent rester visibles sur la facture mais être portées par des lignes négatives du même type métier, pas par une catégorie séparée. Le sous-sujet exploré auparavant comme `BL-028` est absorbé ici, car il n'est pas testable isolément sur `Gestion 2024` faute de détail source exploitable pour des factures mixtes.
- **Résultat attendu** : une création de facture client où l'utilisateur saisit le client et les lignes, choisit un type par ligne, voit le total calculé automatiquement, et obtient à validation des écritures comptables dérivées de la composition réelle de la facture sans dépendre d'un label global saisi à la main.
- **Règle métier cible actuellement privilégiée** :
	- les seuls types de lignes métier exposés sont `cours`, `adhésion` et `autres` ;
	- une remise est saisie comme une seconde ligne négative du même type métier que la ligne remisée ;
	- le client voit toutes les lignes, y compris la remise, mais la ventilation comptable travaille sur le net agrégé par type métier ;
	- une facture ne doit jamais aboutir à un total négatif.
- **Conséquence de cadrage** :
	- on ne garde plus de ticket autonome pour une ventilation `cs+a` dépendant d'un détail explicite dans `Gestion 2024` ;
	- le travail utile déjà engagé sur la ventilation à partir des lignes de facture est poursuivi directement dans `BL-029` ;
	- la logique future d'enrichissement a posteriori depuis `Comptabilité` reste traitée séparément dans `BL-030`.
- **Comportement d'import cible** :
	- import `Gestion` : si le libellé indique `cs`, créer une ligne `cours` ; s'il indique `a`, créer une ligne `adhésion` ; sinon créer une ligne `autres` ;
	- import `Gestion` : ne pas inventer de remise ni de ventilation détaillée absente de la source ;
	- import `Comptabilité` : quand une facture déjà présente porte une ligne `autres`, autoriser un enrichissement ou une clarification automatique de cette ligne si les comptes produits utilisés dans les écritures permettent une déduction sûre ;
	- en cas de rapprochement ambigu entre `Gestion` et `Comptabilité`, ne rien réécrire silencieusement.
- **Questions à trancher** :
	- faut-il supprimer complètement le label global utilisateur au profit d'un calcul depuis les lignes ;
	- comment modéliser les lignes `autres` côté comptable ;
	- jusqu'où autoriser l'import `Comptabilité` à requalifier automatiquement une ligne `autres` ;
	- quelle traçabilité garder entre ligne créée depuis `Gestion`, ligne enrichie via `Comptabilité` et ligne corrigée manuellement ;
	- quelle règle appliquer si une facture mélange `cours`, `adhésion` et `autres`, avec ou sans lignes négatives de remise.
- **Critère d'acceptation** : un utilisateur peut créer une facture client complète sans se poser de question sur le label comptable global ; le total affiché correspond exactement aux lignes saisies et les écritures générées à validation reflètent cette décomposition ligne par ligne.
- **Point d'attention** : l'import `Comptabilité` deviendrait alors non seulement un import d'écritures, mais aussi un mécanisme d'enrichissement métier des factures déjà créées ; il faudra l'encadrer par des règles de sûreté et de coexistence explicites.
- **Résultat livré** : l'implémentation a été fusionnée dans `develop` via le merge de la PR `#18`, puis la recette métier utilisateur a été confirmée sur les scénarios prévus ; la saisie par lignes typées sert désormais de source de vérité pour le total, le libellé dérivé et la ventilation comptable des factures clientes.
- **Implémenté dans ce lot** :
	- ajout d'un type de ligne de facture client (`cours`, `adhésion`, `autres`) en base, API et logique métier ;
	- calcul du total, du label dérivé et de la ventilation comptable directement à partir des lignes, avec support des remises via lignes négatives ;
	- import `Gestion` revu pour créer systématiquement des lignes typées sans inventer de détail absent ;
	- import `Comptabilité` revu pour clarifier de façon sûre une facture mixte existante quand les écritures permettent d'en déduire la ventilation ;
	- formulaire frontend de facture client revu pour supprimer la saisie du label global et piloter la facture par types de lignes ;
	- migration Alembic, tests backend/frontend et backlog mis à jour.
- **Validation technique réalisée** : la suite `pytest tests/`, le `type-check` frontend, `eslint` ciblé et `prettier --check` sur les fichiers frontend touchés sont passés localement avant push.
- **Validation métier réalisée** : la recette utilisateur a été confirmée après fusion, ce qui clôt le ticket côté backlog.

### BL-030 — Politique de modification des objets métier validés

- **Dates** : `created=2026-04-16`, `started=2026-04-20`, `completed=2026-04-20`
- **Pourquoi** : plusieurs objets métier ont déjà un cycle de vie implicite (`draft`, `sent`, `paid`, écritures auto-générées, imports historiques), mais la règle cible de modification reste floue dès qu'un objet a déjà produit des effets comptables ou des dépendances fonctionnelles.
- **Résultat attendu** : une politique explicite qui dit, selon le type d'objet et son statut, ce qui est modifiable directement, ce qui doit régénérer des effets dérivés, ce qui doit être historisé, et ce qui doit être interdit ou remplacé par une opération métier distincte.
- **Arbitrages actés au 2026-04-20** :
	- une facture `sent` non réglée reste éditable, mais seulement avec garde-fous explicites et régénération contrôlée des effets dérivés ;
	- un paiement devient quasi immuable après création ; hors besoin contraire plus tard, seules des corrections mineures sans impact structurel doivent rester possibles ;
	- un objet issu d'un import puis retouché manuellement sort du `rejeu strict` de l'import réversible ; l'historique d'import reste consultable, mais `undo/redo` peut alors être bloqué par divergence d'état.
- **Questions à trancher** :
	- peut-on modifier librement une facture `draft`, `sent` ou `paid` ;
	- faut-il régénérer, annuler puis recréer, ou historiser les écritures comptables dérivées après modification ;
	- quelle différence de traitement entre correction mineure, changement de montant et annulation métier ;
	- faut-il prévoir plus tard des mécanismes dédiés (`avoir`, annulation, revalidation, journal d'audit`) au lieu d'une édition directe uniforme ;
	- qu'a-t-on le droit de réécrire automatiquement lorsqu'un import `Comptabilité` vient clarifier une facture créée plus tôt depuis `Gestion`.
- **Critère d'acceptation** : pour chaque grande famille d'objets métier, un utilisateur et un développeur peuvent répondre sans ambiguïté à la question "que se passe-t-il si je modifie cet objet maintenant ?".
- **Point d'attention** : la traçabilité et la cohérence comptable doivent primer sur la simplicité apparente d'une édition directe, y compris quand la modification vient d'un rapprochement automatique entre imports `Gestion` et `Comptabilité`.
- **Livré** :
	- l'API facture autorise désormais l'édition d'une facture `sent` non réglée, avec régénération transactionnelle des écritures `INVOICE` dérivées ;
	- l'API paiement rend les paiements quasi immuables après création, en ne laissant éditables que les champs mineurs sans impact structurel et en bloquant la suppression standard ;
	- l'UI des paiements reflète cette politique en verrouillant les champs structurels dans la boîte d'édition ;
	- le rejeu strict des imports réversibles bloque bien `undo/redo` dès qu'un objet importé a divergé, y compris après une retouche via l'API contact, avec un test d'intégration couvrant aussi le cas d'instance ORM expirée.
- **Validation technique réalisée** : `ruff check .`, `ruff format --check .`, `mypy .`, `pytest tests/`, `npx vue-tsc --noEmit -p tsconfig.app.json`, `npx vue-tsc --noEmit`, `npx eslint src/` et `npx vitest run` sont passés localement sur la branche de travail.

## Prêt

- Aucun sujet pour le moment.

## En cours

- **BL-019** — `created=2026-04-13`, `started=2026-04-21` — Le socle README + doc d'exploitation est livré, mais le ticket reste ouvert jusqu'à validation complète sur les vrais parcours d'installation, mise à jour et exploitation, avec corrections éventuelles.
- **BL-020** — `created=2026-04-13`, `started=2026-04-21` — La documentation de contribution est structurée, mais le ticket reste ouvert jusqu'à relecture et validation sur un cycle réel `setup -> checks -> PR`, avec ajustements éventuels.
- **BL-021** — `created=2026-04-13`, `started=2026-04-13` — Le manuel utilisateur FR/EN a maintenant une structure pas à pas consolidée et un meilleur aiguillage vers les guides complémentaires ; l'enrichissement visuel réel reste à réaliser pour clôturer le ticket.

## Fait

- **BL-001** — `created=2026-04-12`, `completed=2026-04-12` — Le backlog sert désormais de support de suivi versionné avec priorités, statuts et mises à jour explicites.
- **BL-002** — `created=2026-04-12`, `completed=2026-04-12` — La documentation utilisateur import/reset a été rédigée dans `doc/user/import-excel-et-reinitialisation.md`.
- **BL-003** — `created=2026-04-12`, `completed=2026-04-12` — La campagne de retest sur imports réels 2024/2025 a été rejouée sans écart bloquant.
- **BL-004** — `created=2026-04-12`, `started=2026-04-20`, `completed=2026-04-20` — L'import Excel dispose maintenant d'un historique réversible avec opérations persistées, effets détaillés, exécution en deux temps `prepare -> execute`, et `undo/redo` par opération ou par import complet dans l'UI et l'API.
- **BL-005** — `created=2026-04-12`, `started=2026-04-19`, `completed=2026-04-19` — La politique de coexistence effectivement implémentée pour les imports `Comptabilite` est désormais documentée, testée et intégrée dans `develop`, avec distinction explicite entre doublon exact, ligne déjà couverte par Solde et proximité non bloquante avec une écriture `MANUAL`.
- **BL-006** — `created=2026-04-12`, `started=2026-04-21`, `completed=2026-04-21` — Le ticket est clos après vérification de l'état réel du dépôt : les routes backend utilisent `HTTP_422_UNPROCESSABLE_CONTENT`, aucune occurrence de l'ancienne constante ne subsiste dans le code Python, et `pytest tests/ -W default::DeprecationWarning -q` ne remonte plus le warning FastAPI visé.
- **BL-007** — `created=2026-04-12`, `completed=2026-04-13` — La convention est arrêtée pour le mode de travail actuel : `doc/backlog.md` reste la source de vérité, sans synchronisation systématique avec des issues GitHub à ce stade.
- **BL-008** — `created=2026-04-12`, `started=2026-04-18`, `completed=2026-04-18` — Le premier lot de convergence BL-008 est désormais intégré dans `develop` avec preview bidirectionnelle par domaine, détails `extra_in_solde`, filtre de période dédié à la comparaison et recette locale rejouable.
- **BL-009** — `created=2026-04-12`, `completed=2026-04-12` — Le plan comptable par défaut a été enrichi à partir des comptes réellement rencontrés dans les imports historiques.
- **BL-010** — `created=2026-04-12`, `completed=2026-04-12` — Une stratégie sûre de clôture administrative des exercices historiques importés a été définie et livrée.
- **BL-011** — `created=2026-04-12`, `completed=2026-04-12` — L'exercice courant global et son sélecteur partagé ont été livrés sur les écrans comptables concernés.
- **BL-012** — `created=2026-04-12`, `completed=2026-04-12` — La liste des paiements affiche la référence métier et permet l'édition directe.
- **BL-013** — `created=2026-04-12`, `completed=2026-04-12` — Le journal de caisse propose désormais référence, détail et édition directe.
- **BL-014** — `created=2026-04-12`, `completed=2026-04-12` — Le journal comptable est enrichi pour la lecture métier, le détail et la navigation vers les factures.
- **BL-015** — `created=2026-04-13`, `started=2026-04-20`, `completed=2026-04-20` — L'administration propose désormais un reset sélectif par filière d'import et exercice, avec prévisualisation, suppression des objets importés et des dépendances métier dérivées explicitement cadrées, branchement complet dans `Paramètres`, documentation utilisateur mise à jour et validation locale complète passée.
- **BL-016** — `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14` — Les microcopies et états visibles les plus incohérents ont été harmonisés sur `Banque`, `Caisse` et `Salaires` via des clés i18n dédiées.
- **BL-017** — `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14` — L'affichage des mois et périodes métier est maintenant uniformisé au format français sur `Salaires` et le `Dashboard` sans changer les formats d'échange ISO.
- **BL-018** — `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14` — Les écrans de liste principaux partagent maintenant un socle commun de tri, filtres et compteurs d'état, avec filtres de date FR/ISO et exclusion explicite des tableaux fixes `bilan` / `résultat`.
- **BL-022** — `created=2026-04-13`, `started=2026-04-13`, `completed=2026-04-19` — La gestion des comptes couvre désormais l'administration, l'espace `Mon profil`, le changement de mot de passe utilisateur, la réinitialisation administrateur adaptée au contexte auto-hébergé et l'invalidation des anciennes sessions après changement de mot de passe.
- **BL-023** — `created=2026-04-13`, `started=2026-04-14`, `completed=2026-04-14` — Les rôles métier `Gestionnaire` / `Comptable` / `Administrateur` sont maintenant alignés entre docs, navigation, guards frontend et permissions backend, avec séparation visible `Gestion` / `Comptabilité` et couverture de test ciblée.
- **BL-024** — `created=2026-04-13`, `started=2026-04-19`, `completed=2026-04-19` — Le workflow de paiement est désormais clarifié et fusionné dans `develop` : `chèque` et `espèces` restent saisis côté facture/paiement avec traitement de trésorerie cohérent, tandis que les `virements` sont explicitement renvoyés au futur flux `banque -> paiement` de `BL-031`.
- **BL-025** — `created=2026-04-13`, `started=2026-04-13`, `completed=2026-04-13` — Le grand livre est maintenant borné à l'exercice choisi, sans option multi-exercices, avec un solde d'ouverture cohérent quand la période démarre en cours d'exercice.
- **BL-026** — `created=2026-04-15`, `started=2026-04-15`, `completed=2026-04-16` — Le ticket a livré un cadrage de recette et un constat exploitable sur la reprise `2024`, puis a été clos une fois les écarts résiduels requalifiés en différences de modélisation assumées ou en suites dédiées (`BL-008`, `BL-029`).
- **BL-029** — `created=2026-04-16`, `started=2026-04-16`, `completed=2026-04-19` — La saisie des factures clients par lignes typées, le calcul dérivé du total et de la ventilation comptable, et les adaptations d'import `Gestion` / `Comptabilité` sont maintenant intégrés dans `develop` et validés côté recette métier utilisateur.
- **BL-030** — `created=2026-04-16`, `started=2026-04-20`, `completed=2026-04-20` — La politique cadrée est désormais appliquée et testée : facture `sent` non réglée éditable avec régénération des écritures, paiements quasi immuables après création, et blocage du rejeu strict dès qu'un objet importé a divergé.
- **BL-031** — `created=2026-04-19`, `started=2026-04-19`, `completed=2026-04-20` — La branche `feature/bl-031-bank-reconciliation` livre maintenant une vraie chaîne de rapprochement bancaire exploitable pour le MVP : import `CSV` / `OFX` / `QIF`, catégorisation initiale, suggestions de rapprochement, création ou confirmation de virements clients et fournisseurs depuis l'écran `Banque`, support des virements clients ventilés sur plusieurs règlements, traçabilité `transaction <-> payment(s)` et validation automatisée ciblée passée. Les écarts de recette encore observés, comme certains soldes banque, sont explicitement renvoyés à la recette finale de qualification MVP plutôt qu'à une suite bloquante de BL-031.
- **BL-032** — `created=2026-04-21`, `started=2026-04-21`, `completed=2026-04-21` — La documentation technique historique restante a été migrée en anglais, en cohérence avec la convention documentaire du projet.
- **BL-044** — `created=2026-04-21`, `started=2026-04-21`, `completed=2026-04-21` — Les synthèses factures client distinguent maintenant clairement l'encours de l'exercice et l'encours adhérents total, avec mise en évidence explicite du report historique encore ouvert.
