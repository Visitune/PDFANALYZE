"""
Configuration modulaire pour l'analyseur de fiches techniques.
Permet de définir différents templates pour différents types de documents.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class CriticityLevel(Enum):
    MINEUR = "Mineur"
    MAJEUR = "Majeur"
    CRITIQUE = "Critique"

class Status(Enum):
    CONFORME = "Conforme"
    DOUTEUX = "Douteux"
    NON_CONFORME = "Non Conforme"

@dataclass
class ControlPoint:
    """Point de contrôle configurable"""
    name: str
    description: str
    criticity: CriticityLevel
    synonyms: List[str] = field(default_factory=list)
    required: bool = True
    validation_rules: List[str] = field(default_factory=list)

@dataclass
class DocumentTemplate:
    """Template de document technique"""
    name: str
    description: str
    category: str  # ex: "agro", "electronique", "chimie", etc.
    control_points: List[ControlPoint]
    
# Templates prédéfinis

TEMPLATE_AGRO_ALIMENTAIRE = DocumentTemplate(
    name="Fiche Technique Agro-alimentaire",
    description="Analyse de fiches techniques produits agro-alimentaires",
    category="agro",
    control_points=[
        ControlPoint(
            name="Intitulé du produit",
            description="Dénomination légale du produit",
            criticity=CriticityLevel.MINEUR,
            synonyms=["Dénomination légale", "Nom du produit", "Nom commercial", "Produit"]
        ),
        ControlPoint(
            name="Estampille",
            description="Numéro d'agrément sanitaire",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Estampille sanitaire", "N° d'agrément", "Agrément sanitaire", "FR", "CE"]
        ),
        ControlPoint(
            name="Composition",
            description="Liste des ingrédients et composition",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Ingrédients", "Ingredients", "Composition", "Recette"]
        ),
        ControlPoint(
            name="DLC / DLUO",
            description="Durée de vie et date limite",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Durée de vie", "Date limite", "Use by", "DDM", "DLC"]
        ),
        ControlPoint(
            name="Température",
            description="Conditions de température",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Température de conservation", "Storage temperature", "À conserver à"]
        ),
        ControlPoint(
            name="Origine",
            description="Pays d'origine",
            criticity=CriticityLevel.MAJEUR,
            synonyms=["Pays d'origine", "Origine", "Provenance"]
        ),
        ControlPoint(
            name="Conditionnement",
            description="Type d'emballage",
            criticity=CriticityLevel.MAJEUR,
            synonyms=["Packaging", "Emballage", "Colisage", "Type de contenant"]
        ),
        ControlPoint(
            name="Fournisseur",
            description="Coordonnées du fournisseur",
            criticity=CriticityLevel.MINEUR,
            synonyms=["Adresse fournisseur", "Fabricant", "Contact"]
        ),
        ControlPoint(
            name="Certifications",
            description="Certifications qualité",
            criticity=CriticityLevel.MINEUR,
            synonyms=["VRF", "VVF", "BIO", "VPF", "Label"]
        ),
        ControlPoint(
            name="Critères microbiologiques",
            description="Normes microbiologiques",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Microbiologie", "Germes", "Bactéries"]
        ),
    ]
)

TEMPLATE_ELECTRONIQUE = DocumentTemplate(
    name="Fiche Technique Électronique",
    description="Analyse de fiches techniques composants électroniques",
    category="electronique",
    control_points=[
        ControlPoint(
            name="Référence produit",
            description="Numéro de référence",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Part Number", "Référence", "PN", "SKU"]
        ),
        ControlPoint(
            name="Spécifications électriques",
            description="Caractéristiques électriques",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Electrical Characteristics", "Specs", "Tension", "Courant"]
        ),
        ControlPoint(
            name="Dimensions",
            description="Dimensions physiques",
            criticity=CriticityLevel.MAJEUR,
            synonyms=["Package", "Footprint", "Dimensions", "Taille"]
        ),
        ControlPoint(
            name="Plage de température",
            description="Température de fonctionnement",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Operating Temperature", "Température", "Range"]
        ),
        ControlPoint(
            name="Conformité RoHS",
            description="Conformité environnementale",
            criticity=CriticityLevel.MAJEUR,
            synonyms=["RoHS", "REACH", "Conformité", "Environmental"]
        ),
        ControlPoint(
            name="Datasheet version",
            description="Version du document",
            criticity=CriticityLevel.MINEUR,
            synonyms=["Revision", "Version", "Date"]
        ),
    ]
)

TEMPLATE_CHIMIE = DocumentTemplate(
    name="Fiche de Sécurité Chimique",
    description="Analyse de fiches de données de sécurité (FDS)",
    category="chimie",
    control_points=[
        ControlPoint(
            name="Identification",
            description="Identification de la substance",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Product Identifier", "Identification", "Nom chimique", "CAS"]
        ),
        ControlPoint(
            name="Danger",
            description="Identification des dangers",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Hazards", "Pictogrammes", "H-phrases", "Danger"]
        ),
        ControlPoint(
            name="Composition",
            description="Composition chimique",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Composition", "Substances", "Mélange", "Ingrédients"]
        ),
        ControlPoint(
            name="Premiers secours",
            description="Mesures premiers secours",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["First Aid", "Secours", "Intervention"]
        ),
        ControlPoint(
            name="Manipulation",
            description="Précautions de manipulation",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["Handling", "Storage", "Manipulation", "Stockage"]
        ),
        ControlPoint(
            name="Protection",
            description="Équipements de protection",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["PPE", "Protection", "EPC", "Gants", "Lunettes"]
        ),
    ]
)

# Registre des templates
TEMPLATES = {
    "agro": TEMPLATE_AGRO_ALIMENTAIRE,
    "electronique": TEMPLATE_ELECTRONIQUE,
    "chimie": TEMPLATE_CHIMIE,
}

def get_template(name: str) -> Optional[DocumentTemplate]:
    """Récupère un template par son nom"""
    return TEMPLATES.get(name.lower())

def list_templates() -> Dict[str, str]:
    """Liste tous les templates disponibles"""
    return {k: v.description for k, v in TEMPLATES.items()}

def create_custom_template(name: str, description: str, category: str, control_points: List[ControlPoint]) -> DocumentTemplate:
    """Crée un template personnalisé"""
    return DocumentTemplate(
        name=name,
        description=description,
        category=category,
        control_points=control_points
    )
