"""AccountingAccount model — chart of accounts."""

from enum import StrEnum

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class AccountType(StrEnum):
    ACTIF = "actif"
    PASSIF = "passif"
    CHARGE = "charge"
    PRODUIT = "produit"


class AccountingAccount(Base):
    __tablename__ = "accounting_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[AccountType] = mapped_column(String(20), nullable=False, index=True)
    parent_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


# Default chart of accounts for a French non-profit (loi 1901)
DEFAULT_ACCOUNTS: list[dict[str, str | bool]] = [
    # Actif — Immobilisations
    {"number": "211000", "label": "Terrains", "type": "actif", "is_default": True},
    {
        "number": "215000",
        "label": "Installations techniques",
        "type": "actif",
        "is_default": True,
    },
    # Actif — Trésorerie
    {
        "number": "511200",
        "label": "Chèques à encaisser",
        "type": "actif",
        "is_default": True,
    },
    {
        "number": "512100",
        "label": "Compte courant",
        "type": "actif",
        "is_default": True,
    },
    {"number": "531000", "label": "Caisse", "type": "actif", "is_default": True},
    # Actif — Créances
    {"number": "411100", "label": "Adhérents", "type": "actif", "is_default": True},
    {
        "number": "416000",
        "label": "Clients douteux",
        "type": "actif",
        "is_default": True,
    },
    # Passif — Dettes fournisseurs
    {"number": "401000", "label": "Fournisseurs", "type": "passif", "is_default": True},
    # Passif — Dettes sociales
    {
        "number": "421000",
        "label": "Rémunérations dues",
        "type": "passif",
        "is_default": True,
    },
    {"number": "431100", "label": "URSSAF", "type": "passif", "is_default": True},
    # Passif — Fonds propres
    {
        "number": "110000",
        "label": "Report à nouveau",
        "type": "passif",
        "is_default": True,
    },
    {
        "number": "120000",
        "label": "Résultat de l'exercice (excédent)",
        "type": "passif",
        "is_default": True,
    },
    {
        "number": "129000",
        "label": "Résultat de l'exercice (déficit)",
        "type": "passif",
        "is_default": True,
    },
    # Charges
    {
        "number": "602250",
        "label": "Fournitures de bureau",
        "type": "charge",
        "is_default": True,
    },
    {
        "number": "611100",
        "label": "Sous-traitance cours",
        "type": "charge",
        "is_default": True,
    },
    {"number": "616000", "label": "Assurances", "type": "charge", "is_default": True},
    {
        "number": "626000",
        "label": "Frais postaux et télécom",
        "type": "charge",
        "is_default": True,
    },
    {
        "number": "627000",
        "label": "Services bancaires",
        "type": "charge",
        "is_default": True,
    },
    {
        "number": "641000",
        "label": "Rémunérations du personnel",
        "type": "charge",
        "is_default": True,
    },
    {
        "number": "645100",
        "label": "Cotisations URSSAF",
        "type": "charge",
        "is_default": True,
    },
    # Produits
    {
        "number": "706110",
        "label": "Cours de soutien",
        "type": "produit",
        "is_default": True,
    },
    {
        "number": "706120",
        "label": "Cours de soutien — autres",
        "type": "produit",
        "is_default": True,
    },
    {"number": "756000", "label": "Cotisations", "type": "produit", "is_default": True},
    {
        "number": "758000",
        "label": "Produits divers de gestion",
        "type": "produit",
        "is_default": True,
    },
]
