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

class ChaptersPlanItem(BaseModel):
    title: str = Field(..., description="Titre du chapitre généré.")
    content: str = Field(..., description="Explication du contenu du chapitre.")


class CoursePlan(BaseModel):
    title: str = Field(..., description="Titre du cours généré.")
    chapters: List[ChaptersPlanItem] = Field(
        ...,
        description="Liste des chapitres à générer.",
    )


##########################################
### Modèles Pydantic pour un Chapitre ####
##########################################

class Chapter_Schema(BaseModel):
    id_schema: Optional[str] = Field(None, description="Identifiant unique du schéma")
    id_chapter: Optional[str] = Field(None, description="Identifiant unique du chapitre associé")
    img_base64: str = Field(None, description="Image du schéma encodée en base64")

class Chapter(BaseModel):
    id_chapter: Optional[str] = Field(None, description="Identifiant unique du chapitre")
    id_schema: Optional[str] = Field(None, description="Identifiant unique du schéma associé au chapitre")
    title: str = Field(..., description="Titre du chapitre.")
    content: str = Field(..., description="Contenu détaillé du chapitre.")


###############################################
### Modèle Pydantic pour l'Output du Cours ####
###############################################

class CoursOutput(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique de la sortie de cours")
    title: str = Field(..., description="Titre du cours généré.")
    chapters: List[Chapter] = Field(..., min_length=1, description="Liste des chapitres générés.")
