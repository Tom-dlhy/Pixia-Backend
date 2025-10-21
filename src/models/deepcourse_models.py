from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, List, Union, Optional, Literal, Dict
from src.models import ExerciseOutput, CourseOutput, ExerciseSynthesis, CourseSynthesis

class Chapter(BaseModel):
    id_chapter: Optional[str] = Field(None, description="Identifiant unique du chapitre")
    title: str = Field(..., description="Titre du chapitre.")
    course: CourseOutput = Field(..., description="Contenu du cours associé au chapitre")
    exercice : ExerciseOutput = Field(..., description="Exercices associés au chapitre")
    evaluation : ExerciseOutput = Field(..., description="Évaluation associée au chapitre")

class ChapterSynthesis(BaseModel):
    chapter_title: Annotated[str, StringConstraints(max_length=100)] = Field(..., description="Titre du chapitre à générer")
    chapter_description: Annotated[str, StringConstraints(max_length=1000)] = Field(..., description="Description précise du plan du cours et des thèmes à aborder pour que cela soit cohérent avec le reste")
    synthesis_exercise: ExerciseSynthesis = Field(..., description="Description précise du plan de l'exercice à générer pour ce chapitre")
    synthesis_course: CourseSynthesis = Field(..., description="Description précise du plan du cours à générer pour ce chapitre")
    synthesis_evaluation: ExerciseSynthesis = Field(..., description="Description précise du plan de l'exercice qui sert d'évaluation à générer pour ce chapitre")
    
class DeepCourseSynthesis(BaseModel):
    title: Annotated[str, StringConstraints(max_length=200)] = Field(..., description="Titre du deepcourse à générer")
    synthesis_chapters : List[ChapterSynthesis] = Field(..., min_length=1, max_length=16,description="Liste des plans de chapitres du deepcourse")
    
class DeepCourseOutput(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique du deepcourse")
    title: str = Field(..., description="Titre du deepcourse")
    chapters: List[Chapter] = Field(..., min_length=1, max_length=16,description="Liste des chapitres du deepcourse")
    
