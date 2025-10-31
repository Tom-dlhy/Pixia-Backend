"""Exercise output models.

Pydantic models for exercise types (QCM and open questions), exercise
synthesis, planning, and complete exercise output.
"""

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field, StringConstraints

###########################################################################
### Pydantic Models for Open Questions ####################################
###########################################################################


class OpenQuestion(BaseModel):
    """Single open-ended question."""

    id: Optional[str] = Field(None, description="Identifiant unique de la question")
    question: Annotated[str, StringConstraints(max_length=1000)]
    answers: str = Field(
        "",
        description="Champ réservé pour la réponse de l'utilisateur, à laisser vide.",
    )
    is_correct: bool = Field(
        False,
        description="Indique si la réponse est correcte, à laisser vide lors de la génération.",
    )
    is_corrected: bool = Field(
        False,
        description="Indique si la question a été corrigée, à laisser vide lors de la génération.",
    )
    explanation: Annotated[str, StringConstraints(max_length=2000)]


class Open(BaseModel):
    """Block of open-ended questions."""

    id: Optional[str] = Field(
        None, description="Identifiant unique du bloc de questions"
    )
    type: Literal["open"] = Field("open", description="Toujours 'open'")
    topic: Annotated[str, StringConstraints(max_length=1000)] = Field(
        ..., description="Titre du bloc de questions"
    )
    questions: List[OpenQuestion] = Field(..., min_length=1, max_length=3)


################################################################
### Pydantic Models for QCM                       ##############
################################################################


class QCMAnswer(BaseModel):
    """Single answer option in a QCM question."""

    id: Optional[str] = Field(None)
    text: str
    is_correct: bool
    is_selected: bool = Field(
        False,
        description="Indique si la réponse a été sélectionnée par l'utilisateur, à laisser vide lors de la génération.",
    )


class QCMQuestion(BaseModel):
    """Single multiple choice question."""

    id: Optional[str] = Field(None, description="Identifiant unique de la question")
    question: str
    answers: List[QCMAnswer] = Field(..., max_length=5)
    explanation: str
    multi_answers: bool = Field(
        ..., description="true si la question a plusieurs réponses correctes"
    )
    is_corrected: bool = Field(
        False,
        description="Indique si la question a été corrigée, à laisser vide lors de la génération.",
    )


class QCM(BaseModel):
    """Block of multiple choice questions."""

    id: Optional[str] = Field(
        None, description="Identifiant unique du bloc de questions"
    )
    type: Literal["qcm"] = Field("qcm", description="Toujours 'qcm'")
    topic: str = Field(..., description="Titre du bloc de questions")
    questions: List[QCMQuestion] = Field(..., min_length=1, max_length=5)


################################################################
### Pydantic Models for Exercise Plan Generation  ##############
################################################################


class ExercicePlanItem(BaseModel):
    """Single exercise item in exercise plan."""

    type: Literal["qcm", "open"]
    topic: Annotated[str, StringConstraints(max_length=200)]


class ExercisePlan(BaseModel):
    """Plan of exercises to generate."""

    difficulty: Annotated[str, StringConstraints(max_length=100)]
    exercises: List[ExercicePlanItem] = Field(
        ..., min_length=1, max_length=20, description="Liste des exercices à générer."
    )


class ClassifiedPlan(BaseModel):
    qcm: List[ExercicePlanItem] = Field(default_factory=List)
    open: List[ExercicePlanItem] = Field(default_factory=List)


############################################################################
### Pydantic Models for Exercise Synthesis Planning #######################
############################################################################


class ExerciseSynthesis(BaseModel):
    """Synthesis for exercise generation planning."""

    description: str = Field(
        ..., description="Description détaillé du sujet des exercices à générer."
    )
    title: str = Field(
        ..., description="Titre global du sujet des exercices à générer."
    )
    difficulty: str = Field(
        ..., description="Niveau de difficulté de l'exercice"
    )
    number_of_exercises: Annotated[int, Field(ge=1, le=20)] = Field(
        ..., description="Nombre d'exercices à générer (entre 1 et 20)."
    )
    exercise_type: Literal["qcm", "open", "both"] = Field(
        ..., description="Type d'exercice à générer : qcm / open / both"
    )


############################################################
### Pydantic Models for Exercise Output   ##################
############################################################


class ExerciseOutput(BaseModel):
    """Complete exercise output with all generated exercises."""

    id: Optional[str] = Field(
        None, description="Identifiant unique de la sortie d'exercice"
    )
    title: str = Field(..., description="Titre de l'exercice généré.")
    exercises: List[Annotated[Union[QCM, Open], Field(discriminator="type")]] = Field(
        ..., min_length=1, description="Liste des exercices générés."
    )

