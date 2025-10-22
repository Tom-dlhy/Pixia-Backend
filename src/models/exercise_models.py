from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, List, Union, Optional, Literal

###########################################################################
### Modèles Pydantic pour la génération d'exercices de types OpenText ####
###########################################################################

class OpenQuestion(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique de la question")
    question: Annotated[str, StringConstraints(max_length=1000)]
    answers: str = Field(
        "",
        description="Champ réservé pour la réponse de l'utilisateur, à laisser vide.",
    )
    is_correct: bool = Field(
        False, description="Indique si la réponse est correcte, à laisser vide lors de la génération."
    )
    is_corrected: bool = Field(
        False, description="Indique si la question a été corrigée, à laisser vide lors de la génération."
    )
    explanation: Annotated[str, StringConstraints(max_length=2000)]


class Open(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique du bloc de questions")
    type: Literal["open"] = Field("open", description="Toujours 'open'")
    topic: Annotated[str, StringConstraints(max_length=1000)] = Field(
        ..., 
        description="Titre du bloc de questions"
    )
    questions: List[OpenQuestion] = Field(..., min_length=1, max_length=3)

#####################################################################
### Modèles Pydantic pour la génération d'exercices de types QCM ####
#####################################################################

class QCMAnswer(BaseModel):
    id: Optional[str] = Field(None)
    text: str
    is_correct: bool
    is_selected: bool = Field(
        False, description="Indique si la réponse a été sélectionnée par l'utilisateur, à laisser vide lors de la génération."
    )


class QCMQuestion(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique de la question")
    question: str
    answers: List[QCMAnswer] = Field(
        ..., 
        max_length=5
    )
    explanation: str
    multi_answers: bool = Field(
        ..., 
        description="true si la question a plusieurs réponses correctes"
    )
    is_corrected: bool = Field(
        False, description="Indique si la question a été corrigée, à laisser vide lors de la génération."
    )


class QCM(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique du bloc de questions")
    type: Literal["qcm"] = Field("qcm", description="Toujours 'qcm'")
    topic: str = Field(
        ..., 
        description="Titre du bloc de questions"
    )
    questions: List[QCMQuestion] = Field(..., min_length=1, max_length=5)

################################################################
### Modèles Pydantic pour la génération du plan d'exercices ####
################################################################

class ExercicePlanItem(BaseModel):
    type: Literal["qcm", "open"]
    topic: Annotated[str, StringConstraints(max_length=200)]


class ExercisePlan(BaseModel):
    difficulty: Annotated[str, StringConstraints(max_length=100)]
    exercises: List[ExercicePlanItem] = Field(
        ..., min_length=1, max_length=20, description="Liste des exercices à générer."
    )


class ClassifiedPlan(BaseModel):
    qcm: List[ExercicePlanItem] = Field(default_factory=List)
    open: List[ExercicePlanItem] = Field(default_factory=List)

############################################################################
### Modèle Pydantic pour la synthèse pour générer le plan des exercices ####
############################################################################

class ExerciseSynthesis(BaseModel):
    description: Annotated[str, StringConstraints(max_length=500)] = (
        Field(..., description="Description détaillé du sujet des exercices à générer.")
    )
    title: Annotated[str, StringConstraints(max_length=200)] = Field(
        ..., description="Titre global du sujet des exercices à générer."
    )
    difficulty: Annotated[str, StringConstraints(max_length=100)] = Field(
        ..., description="Niveau de difficulté de l'exercice"
    )
    number_of_exercises: Annotated[int, Field(ge=1, le=20)] = Field(
        ..., description="Nombre d'exercices à générer (entre 1 et 20)."
    )
    exercise_type: Literal["qcm", "open", "both"] = (
        Field(..., description="Type d'exercice à générer : qcm / open / both")
    )


############################################################
### Modèle Pydantic pour la sortie des exercices générés ###
############################################################

class ExerciseOutput(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique de la sortie d'exercice")
    title: str = Field(..., description="Titre de l'exercice généré.")
    exercises: List[
        Annotated[
            Union[QCM, Open],
            Field(discriminator="type")
        ]
    ] = Field(..., min_length=1, description="Liste des exercices générés.")

##################################################
### Fonction de validation de l'ExerciseOutput ###
##################################################

def _validate_exercise_output(data: dict | str | None ) -> ExerciseOutput | None:
    """Valide et parse les données en tant qu'ExerciseOutput."""
    try:
        if isinstance(data, ExerciseOutput):
            return data
        elif isinstance(data, dict):
            # Si les données sont imbriquées dans une clé 'result', les extraire
            if 'result' in data and isinstance(data['result'], dict):
                data = data['result']
            return ExerciseOutput.model_validate(data)
        elif isinstance(data, str):
            # Essayer de parser en JSON d'abord
            import json
            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict) and 'result' in parsed:
                    parsed = parsed['result']
                return ExerciseOutput.model_validate(parsed)
            except (json.JSONDecodeError, ValueError):
                # Si ce n'est pas du JSON valide, essayer la validation directe
                return ExerciseOutput.model_validate_json(data)
        else:
            return None
    except Exception as e:
        import logging
        logging.error(f"Erreur lors de la validation ExerciseOutput: {e}")
        return None