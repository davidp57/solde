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
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
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
    {
        "number": "512102",
        "label": "Compte d'épargne",
        "type": "actif",
        "parent_number": "512100",
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
    {
        "number": "416001",
        "label": "Client litigieux 1",
        "type": "actif",
        "parent_number": "416000",
        "description": "Sous-compte historique conservé pour les imports Excel.",
        "is_default": True,
        "is_active": False,
    },
    {
        "number": "416002",
        "label": "Client litigieux 2",
        "type": "actif",
        "parent_number": "416000",
        "description": "Sous-compte historique conservé pour les imports Excel.",
        "is_default": True,
        "is_active": False,
    },
    # Passif — Dettes fournisseurs
    {"number": "401000", "label": "Fournisseurs", "type": "passif", "is_default": True},
    {
        "number": "401103",
        "label": "PayPal",
        "type": "passif",
        "parent_number": "401000",
        "description": "Sous-compte historique conservé pour les imports Excel.",
        "is_default": True,
        "is_active": False,
    },
    {
        "number": "401104",
        "label": "Google",
        "type": "passif",
        "parent_number": "401000",
        "description": "Sous-compte historique conservé pour les imports Excel.",
        "is_default": True,
        "is_active": False,
    },
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
        "number": "106800",
        "label": "Autres réserves (dont réserves pour projet associatif)",
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
    {
        "number": "613200",
        "label": "Locations immobilières",
        "type": "charge",
        "is_default": True,
    },
    {"number": "616000", "label": "Assurances", "type": "charge", "is_default": True},
    {
        "number": "616100",
        "label": "Multirisques",
        "type": "charge",
        "parent_number": "616000",
        "is_default": True,
    },
    {
        "number": "623000",
        "label": "Publicité, publications, relations publiques",
        "type": "charge",
        "is_default": True,
    },
    {
        "number": "623400",
        "label": "Cadeaux",
        "type": "charge",
        "parent_number": "623000",
        "is_default": True,
    },
    {
        "number": "625000",
        "label": "Déplacements, missions et réceptions",
        "type": "charge",
        "is_default": True,
    },
    {
        "number": "625700",
        "label": "Réceptions",
        "type": "charge",
        "parent_number": "625000",
        "is_default": True,
    },
    {
        "number": "626000",
        "label": "Frais postaux et télécom",
        "type": "charge",
        "is_default": True,
    },
    {
        "number": "626500",
        "label": "Téléphone",
        "type": "charge",
        "parent_number": "626000",
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
    {
        "number": "443000",
        "label": (
            "Opérations particulières avec l'Etat, les collectivités publiques, "
            "les organismes internationaux"
        ),
        "type": "passif",
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
        "number": "740000",
        "label": "Subventions d'exploitation",
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
    {
        "number": "768100",
        "label": "Intérêts des comptes financiers débiteurs",
        "type": "produit",
        "is_default": True,
    },
]
