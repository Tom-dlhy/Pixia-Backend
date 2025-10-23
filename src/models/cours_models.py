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
    """Partie de cours avec contenu markdown, diagramme intelligent et SVG généré."""

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
        None, description="SVG du schéma encodé en base64 (généré par Kroki)"
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

################################################
### Fonction de validation de l'CourseOutput ###
################################################


def _validate_course_output(data: dict | str) -> CourseOutput | None:
    """Valide et parse les données en tant que CourseOutput."""
    try:
        if isinstance(data, CourseOutput):
            return data
        elif isinstance(data, dict):
            # Si les données sont imbriquées dans une clé 'result', les extraire
            if "result" in data and isinstance(data["result"], dict):
                data = data["result"]
            return CourseOutput.model_validate(data)
        elif isinstance(data, str):
            # Essayer de parser en JSON d'abord
            import json

            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict) and "result" in parsed:
                    parsed = parsed["result"]
                return CourseOutput.model_validate(parsed)
            except (json.JSONDecodeError, ValueError):
                # Si ce n'est pas du JSON valide, essayer la validation directe
                return CourseOutput.model_validate_json(data)
        else:
            return None
    except Exception as e:
        import logging

        logging.error(f"Erreur lors de la validation CourseOutput: {e}")
        return None
