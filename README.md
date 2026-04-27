# Solde ⚖️

Solde is a web application for bookkeeping and day-to-day financial management for a French loi 1901 non-profit.

## Français

Solde centralise la facturation, les paiements, la trésorerie, les imports historiques et la comptabilité en partie double dans une seule application.

### Liens rapides

- **Installation et administration** : [doc/admin/README.md](doc/admin/README.md)
  - [Installation Docker](doc/admin/installation.md)
  - [Configuration](doc/admin/configuration.md)
  - [Import Excel](doc/admin/excel-import.md)
  - [Administration système](doc/admin/administration.md)
- **Manuel utilisateur** : [doc/user/manuel.md](doc/user/manuel.md)
- **Documentation développeur** : [doc/dev/README.md](doc/dev/README.md)
- **Changelog** : [CHANGELOG.md](CHANGELOG.md)
- **Roadmap** : [doc/roadmap.md](doc/roadmap.md)

## English

Solde brings invoicing, payments, treasury workflows, historical imports, and double-entry accounting into a single application.

### Quick links

- **Installation and administration**: [doc/admin/README.md](doc/admin/README.md)
  - [Docker installation](doc/admin/installation.md)
  - [Configuration](doc/admin/configuration.md)
  - [Excel import](doc/admin/excel-import.md)
  - [System administration](doc/admin/administration.md)
- **User manual**: [doc/user/manuel.md](doc/user/manuel.md)
- **Developer documentation**: [doc/dev/README.md](doc/dev/README.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Roadmap**: [doc/roadmap.md](doc/roadmap.md)

## Documentation structure

```
doc/
├── admin/          Installation, configuration, Excel import, system administration (FR+EN)
├── dev/            Architecture, contributing, testing, development process (EN)
├── user/           User manual (FR)
├── llm/            LLM reference (EN)
├── backlog.md      Project backlog (FR)
└── roadmap.md      Delivery roadmap
```

## Repository layout

```
solde/
├── backend/        FastAPI application
├── frontend/       Vue.js 3 application
├── tests/          pytest test suite
├── data/           Runtime data (SQLite DB, PDFs, backups, logs)
├── doc/            Documentation
├── Dockerfile
├── docker-compose.yml
├── dev.ps1
└── pyproject.toml
```

## Licence / License

[Elastic License 2.0 (ELv2)](LICENSE) — auto-hébergement libre, redistribution et offre SaaS commerciale réservées.
