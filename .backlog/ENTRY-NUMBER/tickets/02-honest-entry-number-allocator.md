# TEC-258 — `next_entry_number` : supprimer la fausse boucle de nouvelle tentative

Status: ⬜ ready
Type: chore · P2
Files: `backend/services/accounting_engine.py`, `tests/unit/test_accounting_engine.py`

## What to build

La boucle `for attempt in range(_ENTRY_NUMBER_MAX_RETRIES)` de `next_entry_number` renvoie
dès la première itération ; la docstring promet une gestion d'`IntegrityError` qui n'existe
pas. Deux options, à trancher au début du ticket :

- **a. Honnête et simple (reco)** — supprimer la boucle et `_ENTRY_NUMBER_MAX_RETRIES`,
  réécrire la docstring (« lit le plus grand numéro numérique ; l'unicité est garantie par
  l'index de 0052, une collision concurrente échoue au flush »), et transformer cette
  `IntegrityError` en erreur métier claire (409) au niveau des routers concernés. Un seul
  worker Uvicorn et un usage à quelques utilisateurs rendent la collision rare.
- **b. Vraie nouvelle tentative** — envelopper allocation + `flush` dans un savepoint
  (`begin_nested`) et réessayer sur `IntegrityError`. Plus lourd : l'allocateur ne fait pas
  le flush aujourd'hui, il faudrait déplacer la responsabilité chez chaque appelant
  (saisie manuelle, moteur, import, clôture).

## Acceptance criteria

- [ ] Plus de code inatteignable ni de docstring mensongère dans l'allocateur.
- [ ] Le comportement en cas de collision est celui de l'option retenue, couvert par un test.
- [ ] Les appels existants (saisie manuelle, moteur de règles, import salaires, clôture,
      report à nouveau) passent par le même allocateur.
