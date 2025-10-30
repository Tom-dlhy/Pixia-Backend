"""Course output models.

Pydantic models for course synthesis, planning, and complete course output
with sections, diagrams, and schema representations.
"""

from typing import List, Optional

from pydantic import BaseModel, Field
from typing import Literal, List, Optional


##################################################
### Pydantic Models for Course Synthesis #########
##################################################


class CourseSynthesis(BaseModel):
    """Synthesis of course content for generation planning."""

    description: str = Field(
        ..., description="Description détaillée du sujet du cours à générer."
    )
    difficulty: str = Field(..., description="Niveau de difficulté du cours.")
    level_detail: Literal["flash", "standard", "detailed"] = Field(
        "standard", description="Niveau de détail du cours."
    )


#############################################################
### Pydantic Models for Course Plan Generation ##############
#############################################################


class PartPlanItem(BaseModel):
    """Single part item in course plan."""

    title: str = Field(..., description="Titre de la partie générée.")
    content: str = Field(..., description="Explication du contenu de la partie.")


class CoursePlan(BaseModel):
    """Plan of course parts to generate."""

    title: str = Field(..., description="Titre du cours généré.")
    parts: List[PartPlanItem] = Field(
        ...,
        description="Liste des parties à générer.",
    )


##########################################
### Pydantic Models for Course Part #####
##########################################


class Part(BaseModel):
    """Course section with markdown content, diagram, and PNG schema."""

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


# Legacy alias for backward compatibility
PartSchema = Part


###############################################
### Pydantic Models for Course Output   #######
###############################################


class CourseOutput(BaseModel):
    """Complete course output with all parts and diagrams."""

    id: Optional[str] = Field(
        None, description="Identifiant unique de la sortie de cours"
    )
    title: str = Field(..., description="Titre du cours généré.")
    parts: List[Part] = Field(
        ...,
        description="Liste des parties générées avec contenu et diagrammes.",
    )

