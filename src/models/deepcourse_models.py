"""Deep course output models.

Pydantic models for chapters, chapter synthesis, and complete deep course
output combining multiple chapters with exercises and evaluations.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from src.models.cours_models import CourseOutput, CourseSynthesis
from src.models.exercise_models import ExerciseOutput, ExerciseSynthesis


class Chapter(BaseModel):
    """Single chapter within a deep course."""

    id_chapter: Optional[str] = Field(None, description="Identifiant unique du chapitre")
    title: str = Field(..., description="Titre du chapitre.")
    course: CourseOutput = Field(..., description="Contenu du cours associé au chapitre")
    exercice: ExerciseOutput = Field(..., description="Exercices associés au chapitre")
    evaluation: ExerciseOutput = Field(..., description="Évaluation associée au chapitre")


class ChapterSynthesis(BaseModel):
    """Synthesis for generating a single chapter."""

    chapter_title: str = Field(..., description="Titre du chapitre à générer")
    chapter_description: str = Field(..., description="Description précise du plan du cours et des thèmes à aborder pour que cela soit cohérent avec le reste")
    synthesis_exercise: ExerciseSynthesis = Field(..., description="Description précise du plan de l'exercice à générer pour ce chapitre")
    synthesis_course: CourseSynthesis = Field(..., description="Description précise du plan du cours à générer pour ce chapitre")
    synthesis_evaluation: ExerciseSynthesis = Field(..., description="Description précise du plan de l'exercice qui sert d'évaluation à générer pour ce chapitre")


class DeepCourseSynthesis(BaseModel):
    """Synthesis for generating a complete deep course."""

    title: str = Field(..., description="Titre du deepcourse à générer")
    synthesis_chapters: List[ChapterSynthesis] = Field(..., min_length=1, max_length=16, description="Liste des plans de chapitres du deepcourse")


class DeepCourseOutput(BaseModel):
    """Complete deep course output with all chapters."""

    id: Optional[str] = Field(None, description="Identifiant unique du deepcourse")
    title: str = Field(..., description="Titre du deepcourse")
    chapters: List[Chapter] = Field(..., min_length=1, max_length=16, description="Liste des chapitres du deepcourse")
    
