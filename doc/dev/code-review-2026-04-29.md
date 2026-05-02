# Revue de code — Solde v1.1.0

**Date** : 2026-04-29  
**Périmètre** : backend Python (FastAPI/SQLAlchemy), frontend TypeScript (Vue 3), infrastructure  
**Suite de tests** : 999/999 ✅

---

## Résumé exécutif

L'architecture générale est solide : séparation claire routeurs → services → modèles, migrations Alembic, audit log complet, tests d'intégration couvrant les parcours critiques. Les problèmes identifiés se concentrent sur trois catégories : sécurité de l'authentification, atomicité des transactions, et dette technique mineure.

| Sévérité | Nb | Tickets |
|---|---|---|
| 🔴 Critique | 3 | TEC-133, TEC-134, TEC-135 |
| 🟠 Modéré | 5 | TEC-136, TEC-137, TEC-138, TEC-139, TEC-140 |
| 🟡 Mineur | 2 | TEC-141, TEC-142 |

---

## 🔴 Problèmes critiques

### TEC-133 — Access token stocké en `localStorage` (vulnérabilité XSS)

**Fichier :** `frontend/src/stores/auth.ts` (lignes 34–36, 58–59)

```ts
function saveAccessToken(access: string): void {
  accessToken.value = access
  localStorage.setItem(ACCESS_TOKEN_KEY, access)  // ← accessible via JS
}
```

Le refresh token est correctement protégé (cookie `HttpOnly`), mais l'access token persisté dans `localStorage` est accessible à tout script JS de la page. Une XSS (via une dépendance compromise, un template mal échappé, etc.) permet de voler ce token et d'usurper la session.

**Pattern recommandé :** stocker l'access token **uniquement en mémoire** (`ref` Pinia, non persisté). Au rechargement de page, déclencher un appel silencieux à `POST /api/auth/refresh` (le cookie HttpOnly est envoyé automatiquement) pour obtenir un nouveau token. Le `initFromStorage()` actuel et le `localStorage` côté auth deviennent inutiles.

**Impact :** compromission de session sans interaction utilisateur si XSS exploitée.

---

### TEC-134 — Atomicité brisée entre modification et audit log

**Fichiers :** `backend/routers/auth.py` (lignes 437–447), `backend/routers/invoice.py` (lignes 159–166)

Exemple dans `update_user` :

```python
changes = body.model_dump(exclude_unset=True)
await db.commit()       # ← transaction 1 : modification utilisateur commitée
await db.refresh(user)
await record_audit(...)  # ← ajouté à la session APRÈS le commit
return user
# La session se ferme : get_session() commite l'audit dans transaction 2
```

La modification de données et l'entrée d'audit vivent dans **deux transactions séparées**. Si la deuxième transaction échoue (panne réseau, redémarrage), la donnée est modifiée mais l'audit est perdu. Toute investigation de sécurité post-incident sera incomplète.

**Fix :** appeler `record_audit()` **avant** `await db.commit()`. Un seul commit suffit ; `get_session()` commite automatiquement à la sortie du contexte.

```python
# Correct
await record_audit(db, action=..., actor=..., ...)
await db.commit()
```

---

### TEC-135 — Race condition sur la numérotation des factures

**Fichier :** `backend/services/invoice.py` (lignes 154–168)

```python
result = await db.execute(
    select(Invoice.number).where(...).order_by(Invoice.id.desc()).limit(1)
)
last = result.scalar_one_or_none()
seq = int(m.group(1)) + 1 if m else 1
# ← pas de verrou entre SELECT et INSERT
```

Deux requêtes simultanées de création de facture obtiennent le même `last`, calculent le même `seq` et tentent d'insérer le même numéro. La contrainte `UNIQUE` sur `Invoice.number` lève alors une `IntegrityError` non gérée → réponse 500 pour l'utilisateur.

Pour le déploiement single-worker (NAS Synology), le risque est faible mais réel (onglets multiples, appels API parallèles depuis le frontend). Options :
1. Encapsuler la numérotation dans un `SELECT ... FOR UPDATE` / `BEGIN IMMEDIATE` sur SQLite.
2. Ajouter un retry loop avec catch `IntegrityError` (plus simple, moins élégant).
3. Déléguer à une séquence de base de données (SQLite ne supporte pas nativement).

---

## 🟠 Problèmes modérés

### TEC-136 — Chemins absolus de fichiers stockés en base de données

**Fichier :** `backend/routers/invoice.py` (lignes 532–536)

```python
upload_dir = Path("data/uploads/invoices").resolve()  # → chemin absolu /app/data/...
file_path = upload_dir / safe_name
# Stocké dans Invoice.file_path / Invoice.pdf_path
```

Les chemins absolus (ex. `/app/data/uploads/invoices/abc123.pdf`) deviennent obsolètes si le container est recréé dans un répertoire différent, si l'app est déplacée, ou si les données sont migrées. Tous les fichiers liés aux factures existantes seraient inaccessibles.

**Fix :** stocker des chemins relatifs à une racine configurable (ex. `uploads/invoices/abc123.pdf`), et résoudre le chemin complet à la lecture via un helper centralisé.

---

### TEC-137 — Double décodage JWT sur chaque requête API

**Fichiers :** `backend/main.py` (ligne 116), `backend/routers/auth.py` (ligne 76)

`MustChangePasswordMiddleware.dispatch()` décode le JWT sur **chaque** requête API non-exemptée, puis `get_current_user` le décode à nouveau dans le même cycle de vie de la requête. C'est un overhead inutile (bcrypt-like pour HS256 = négligeable, mais principe).

**Options :**
- Stocker le payload décodé dans `request.state` depuis le middleware et le lire dans `get_current_user`.
- Supprimer la logique de décodage dans le middleware et la déléguer uniquement à `get_current_user` (le guard `mcp` peut être vérifié après la validation du token).

---

### TEC-138 — Croissance illimitée du dictionnaire du rate limiter

**Fichier :** `backend/services/rate_limiter.py`

```python
self._attempts: dict[str, list[float]] = defaultdict(list)
```

Le nettoyage des tentatives expirées (`_attempts[key] = [t for t in ...]`) n'est déclenché que lorsque la **même clé** (IP) repasse dans `is_rate_limited()`. Les IPs qui tentent une ou deux fois puis disparaissent restent indéfiniment dans le dictionnaire. Lors d'un scan de masse (milliers d'IPs sources), cela peut consommer de la mémoire de façon non bornée.

**Fix :** ajouter une purge périodique (ex. toutes les 1000 appels ou via `asyncio.create_task` toutes les N minutes) qui supprime les clés dont toutes les tentatives sont expirées. Alternative : utiliser un LRU cache borné.

---

### TEC-139 — Tokens de consommation OpenAI non comptabilisés en streaming

**Fichier :** `backend/services/chat_service.py` (ligne 211)

```python
# Gemini → comptabilise prompt_tokens + completion_tokens ✅
# OpenAI → retourne toujours None ❌
yield delta.content, None
```

Le path Gemini remonte correctement les compteurs de tokens via `usage_metadata`. Le path OpenAI retourne systématiquement `None`, rendant les colonnes `prompt_tokens` / `completion_tokens` de `chat_log` inutilisables pour monitorer la consommation API OpenAI.

**Fix :** passer `stream_options={"include_usage": True}` dans `client.chat.completions.create()` et extraire `chunk.usage` sur le dernier événement.

---

### TEC-140 — Endpoint audit log sans pagination ni filtrage

**Fichier :** `backend/routers/settings.py` (ligne 410)

```python
result = await db.execute(select(AuditLog).order_by(...).limit(1000))
```

1 000 entrées retournées sans aucun filtre (par date, acteur, action) ni pagination. À mesure que les logs s'accumulent (login quotidiens, modifications, envois d'emails), cette réponse JSON devient volumineuse et le chargement de l'écran Administration ralentit.

**Fix :** ajouter paramètres `skip`, `limit`, `action`, `actor_id`, `from_date`, `to_date` sur `GET /api/settings/audit-logs`, avec une valeur par défaut raisonnable (`limit=100`).

---

## 🟡 Améliorations mineures

### TEC-141 — Rôles utilisateur hardcodés comme chaînes littérales dans le frontend

**Fichier :** `frontend/src/stores/auth.ts` (lignes 17–29) et composants

```ts
user.value?.role === 'admin'
user.value?.role === 'tresorier'
user.value?.role === 'secretaire'
```

Les valeurs de rôles sont répétées en dur dans le store, et probablement dans les composants (`v-if="isAdmin"`, etc.). Une faute de frappe silencieuse (ex. `'Admin'` au lieu de `'admin'`) passerait inaperçue à la compilation.

**Fix :** déclarer un objet de constantes ou un enum TypeScript partagé :
```ts
export const USER_ROLES = { ADMIN: 'admin', TRESORIER: 'tresorier', SECRETAIRE: 'secretaire', READONLY: 'readonly' } as const
```
Utiliser `USER_ROLES.ADMIN` partout plutôt que la chaîne littérale.

---

### TEC-142 — Suppressions `# type: ignore[return-value]` systématiques dans les routeurs

**Fichiers :** `backend/routers/invoice.py`, `contact.py`, `payment.py`, etc.

```python
return invoice  # type: ignore[return-value]
return updated  # type: ignore[return-value]
```

Ces suppressions indiquent un désalignement de types entre les modèles SQLAlchemy (`Invoice`) et les schémas Pydantic `response_model`. Elles masquent des erreurs mypy potentiellement légitimes.

**Fix :** s'assurer que les schémas Pydantic sont configurés avec `model_config = ConfigDict(from_attributes=True)` et utiliser `InvoiceRead.model_validate(invoice)` explicitement, ou annoter correctement les types de retour des fonctions service pour que mypy les accepte sans suppression.

---

## Points forts notables

- **Sécurité globalement solide** : headers HTTP défensifs (CSP, HSTS, X-Frame-Options), refresh token en cookie HttpOnly, validation par magic bytes des uploads, regex anti-path-traversal sur les backups.
- **Gestion du cycle de vie des mots de passe** : `must_change_password`, `password_changed_at` (invalidation des tokens antérieurs), complexité imposée.
- **Architecture de tests exemplaire** : 36 fichiers unitaires + 30 d'intégration, fixtures propres (truncation par test, bcrypt accéléré), 999 tests en 81 secondes.
- **Moteur comptable robuste** : machine d'état sur les statuts de facture, transitions validées, écritures comptables générées par règles configurables.
- **Pipeline d'import Excel** : correctement découpé en 16 sous-modules après le refactoring TEC-050, avec politique de coexistence explicite.
- **Service de backup** : `sqlite3.backup()` en thread worker, rotation FIFO, protection path-traversal, restart propre via SIGTERM.
