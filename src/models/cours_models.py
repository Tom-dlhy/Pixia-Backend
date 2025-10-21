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


class PartSchema(BaseModel):
    id_schema: Optional[str] = Field(None, description="Identifiant unique du schéma")
    id_part: Optional[str] = Field(
        None, description="Identifiant unique de la partie associée"
    )
    img_base64: str = Field(None, description="Image du schéma encodée en base64")


class Part(BaseModel):
    id_part: Optional[str] = Field(
        None, description="Identifiant unique de la partie"
    )
    id_schema: Optional[str] = Field(
        None, description="Identifiant unique du schéma associé à la partie"
    )
    title: str = Field(..., description="Titre de la partie.")
    content: str = Field(..., description="Contenu détaillé de la partie.")
    schema_description: Optional[str] = Field(
        None,
        description="Description précise du contenu du schéma associé à la partie.",
    )


###############################################
### Modèle Pydantic pour l'Output du Cours ####
###############################################


class CourseOutput(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique de la sortie de cours")
    title: str = Field(..., description="Titre du cours généré.")
    parts: List[Part] = Field(
        ..., min_length=1, description="Liste des parties générées."
    )

################################################
### Fonction de validation de l'CourseOutput ###
################################################


def _validate_course_output(data: dict | str) -> CourseOutput | None:
    """Valide et parse les données en tant que CourseOutput."""
    if isinstance(data, dict):
        return CourseOutput.model_validate(data)
    elif isinstance(data, str):
        return CourseOutput.model_validate_json(data)
    else:
        return None
