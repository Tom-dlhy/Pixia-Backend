from pydantic import BaseModel, Field
from typing import Literal, List, Optional


##################################################
### Modèle Pydantic pour la Synthèse de Cours ####
##################################################


class CourseSynthesis(BaseModel):
    description: str = Field(
        ..., description="Description détaillée du sujet du cours à générer."
    )
    difficulty: str = Field(..., description="Niveau de difficulté du cours.")
    level_detail: Literal["flash", "standard", "detailed"] = Field(
        "standard", description="Niveau de détail du cours."
    )


#############################################################
### Modèles Pydantic pour la Génération du Plan du Cours ####
#############################################################


class PartPlanItem(BaseModel):
    title: str = Field(..., description="Titre de la partie générée.")
    content: str = Field(..., description="Explication du contenu de la partie.")


class CoursePlan(BaseModel):
    title: str = Field(..., description="Titre du cours généré.")
    parts: List[PartPlanItem] = Field(
        ...,
        description="Liste des parties à générer.",
    )


##########################################
### Modèles Pydantic pour une partie ####
##########################################


class Part(BaseModel):
    """Partie de cours avec contenu markdown, diagramme intelligent et PNG généré."""

    id_part: Optional[str] = Field(None, description="Identifiant unique de la partie")
    id_schema: Optional[str] = Field(
        None, description="Identifiant unique du schéma associé à la partie"
    )
    title: str = Field(..., description="Titre de la partie.")
    content: str = Field(..., description="Contenu détaillé de la partie en markdown.")
    schema_description: Optional[str] = Field(
        None,
        description="Description précise du contenu du schéma associé à la partie.",
    )
    diagram_type: str = Field(
        "mermaid",
        description="Type de diagramme sélectionné: mermaid, plantuml, graphviz, vegalite",
    )
    diagram_code: Optional[str] = Field(
        None, description="Code du diagramme généré (Mermaid, GraphViz, etc.)"
    )
    img_base64: Optional[str] = Field(
        None, description="PNG du schéma encodé en base64 (généré par Kroki)"
    )


# Alias pour compatibilité rétroactive (legacy)
PartSchema = Part


###############################################
### Modèle Pydantic pour l'Output du Cours ####
###############################################


class CourseOutput(BaseModel):
    """Sortie complète du cours avec toutes les parties et diagrammes générés."""

    id: Optional[str] = Field(
        None, description="Identifiant unique de la sortie de cours"
    )
    title: str = Field(..., description="Titre du cours généré.")
    parts: List[Part] = Field(
        ...,
        description="Liste des parties générées avec contenu et diagrammes.",
    )

