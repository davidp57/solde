# Solde ⚖️

Solde is a web application for bookkeeping and day-to-day financial management for a French loi 1901 non-profit.

## Français

Solde centralise la facturation, les paiements, la trésorerie, les imports historiques et la comptabilité en partie double dans une seule application.

### Liens rapides

- **Installation et administration** : [docs/admin/README.md](docs/admin/README.md)
  - [Installation Docker](docs/admin/installation.md)
  - [Configuration](docs/admin/configuration.md)
  - [Import Excel](docs/admin/excel-import.md)
  - [Administration système](docs/admin/administration.md)
- **Manuel utilisateur** : [docs/user/manuel.md](docs/user/manuel.md)
- **Documentation développeur** : [docs/dev/README.md](docs/dev/README.md)
- **Changelog** : [CHANGELOG.md](CHANGELOG.md)
- **Roadmap** : [docs/roadmap.md](docs/roadmap.md)

## English

Solde brings invoicing, payments, treasury workflows, historical imports, and double-entry accounting into a single application.

### Quick links

- **Installation and administration**: [docs/admin/README.md](docs/admin/README.md)
  - [Docker installation](docs/admin/installation.md)
  - [Configuration](docs/admin/configuration.md)
  - [Excel import](docs/admin/excel-import.md)
  - [System administration](docs/admin/administration.md)
- **User manual**: [docs/user/manuel.md](docs/user/manuel.md)
- **Developer documentation**: [docs/dev/README.md](docs/dev/README.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Roadmap**: [docs/roadmap.md](docs/roadmap.md)

## Documentation structure

```
docs/
├── admin/          Installation, configuration, Excel import, system administration (FR+EN)
├── dev/            Architecture, contributing, testing, development process (EN)
├── user/           User manual (FR)
├── llm/            LLM reference (EN)
├── agents/         Agent-skill config (issue tracker, triage, domain)
├── adr/            Architecture decision records (EN)
└── roadmap.md      Delivery roadmap

.backlog/           Per-lot backlog — PRDs + tickets, active and archived (see .backlog/README.md)
```

## Repository layout

```
solde/
├── backend/        FastAPI application
├── frontend/       Vue.js 3 application
├── tests/          pytest test suite
├── data/           Runtime data (SQLite DB, PDFs, backups, logs)
├── docs/           Documentation
├── .backlog/        Per-lot backlog (PRDs + tickets)
├── Dockerfile
├── docker-compose.yml
├── dev.ps1
└── pyproject.toml
```

## Licence / License

[Elastic License 2.0 (ELv2)](LICENSE) — auto-hébergement libre, redistribution et offre SaaS commerciale réservées.
