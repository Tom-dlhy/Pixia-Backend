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
    exercises: list[ExercicePlanItem] = Field(
        ..., min_length=1, max_length=20, description="Liste des exercices à générer."
    )


class ClassifiedPlan(BaseModel):
    qcm: list[ExercicePlanItem] = Field(default_factory=list)
    open: list[ExercicePlanItem] = Field(default_factory=list)

############################################################################
### Modèle Pydantic pour la synthèse pour générer le plan des exercices ####
############################################################################

class ExerciseSynthesis(BaseModel):
    description: Annotated[str, StringConstraints(max_length=500)] = (
        Field(..., description="Description détaillé du sujet des exercices à générer.")
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
    exercises: List[
        Annotated[
            Union[QCM, Open],
            Field(discriminator="type")
        ]
    ] = Field(..., min_length=1, description="Liste des exercices générés.")