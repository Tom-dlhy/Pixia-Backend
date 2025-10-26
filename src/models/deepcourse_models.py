from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from src.models import ExerciseOutput, CourseOutput, ExerciseSynthesis, CourseSynthesis
import json
import logging

logger = logging.getLogger(__name__)

class Chapter(BaseModel):
    id_chapter: Optional[str] = Field(None, description="Identifiant unique du chapitre")
    title: str = Field(..., description="Titre du chapitre.")
    course: CourseOutput = Field(..., description="Contenu du cours associé au chapitre")
    exercice : ExerciseOutput = Field(..., description="Exercices associés au chapitre")
    evaluation : ExerciseOutput = Field(..., description="Évaluation associée au chapitre")

class ChapterSynthesis(BaseModel):
    chapter_title: str = Field(..., description="Titre du chapitre à générer")
    chapter_description: str = Field(..., description="Description précise du plan du cours et des thèmes à aborder pour que cela soit cohérent avec le reste")
    synthesis_exercise: ExerciseSynthesis = Field(..., description="Description précise du plan de l'exercice à générer pour ce chapitre")
    synthesis_course: CourseSynthesis = Field(..., description="Description précise du plan du cours à générer pour ce chapitre")
    synthesis_evaluation: ExerciseSynthesis = Field(..., description="Description précise du plan de l'exercice qui sert d'évaluation à générer pour ce chapitre")
    
class DeepCourseSynthesis(BaseModel):
    title: str = Field(..., description="Titre du deepcourse à générer")
    synthesis_chapters: List[ChapterSynthesis] = Field(..., min_length=1, max_length=16,description="Liste des plans de chapitres du deepcourse")
    
class DeepCourseOutput(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique du deepcourse")
    title: str = Field(..., description="Titre du deepcourse")
    chapters: List[Chapter] = Field(..., min_length=1, max_length=16,description="Liste des chapitres du deepcourse")
    

def _validate_chapter_output(data: dict | str | Dict[str, Any] | Chapter) -> Chapter | None:
    """Valide et parse les donnees en tant que Chapter."""

    try:
        if isinstance(data, Chapter):
            return data

        if isinstance(data, dict):
            extracted_data = data

            if "result" in data:
                result_data = data["result"]
                if isinstance(result_data, dict):
                    extracted_data = result_data
                elif isinstance(result_data, Chapter):
                    return result_data

            elif "chapter" in data and isinstance(data["chapter"], (dict, Chapter)):
                chapter_data = data["chapter"]
                if isinstance(chapter_data, dict):
                    extracted_data = chapter_data
                elif isinstance(chapter_data, Chapter):
                    return chapter_data

            return Chapter.model_validate(extracted_data)

        if isinstance(data, str):
            try:
                parsed = json.loads(data)

                if isinstance(parsed, dict):
                    if "result" in parsed:
                        parsed = parsed["result"]
                    elif "chapter" in parsed:
                        parsed = parsed["chapter"]

                return Chapter.model_validate(parsed)
            except (json.JSONDecodeError, ValueError) as err:
                return Chapter.model_validate_json(data)

        logger.warning("Unsupported data type for chapter validation: %s", type(data))
        return None

    except Exception as exc:
        logger.error("Error while validating Chapter output: %s", exc)
        return None


def _validate_deepcourse_output(data: dict | str | Dict[str, Any] | DeepCourseOutput) -> DeepCourseOutput | None:
    """Valide et parse les données en tant qu'DeepCourseOutput."""
    
    try:
        if isinstance(data, DeepCourseOutput):
            return data
        
        elif isinstance(data, dict):
            
            extracted_data = data
            if 'result' in data:
                if isinstance(data['result'], dict):
                    extracted_data = data['result']
                elif isinstance(data['result'], DeepCourseOutput):
                    return data['result']
            
            return DeepCourseOutput.model_validate(extracted_data)
        
        elif isinstance(data, str):
            try:
                parsed = json.loads(data)
                
                if isinstance(parsed, dict) and 'result' in parsed:
                    parsed = parsed['result']
                
                return DeepCourseOutput.model_validate(parsed)
            except (json.JSONDecodeError, ValueError) as je:
                return DeepCourseOutput.model_validate_json(data)
        
        else:
            logger.warning(f"Type non supporté: {type(data)}")
            return None
    
    except Exception as e:
        logger.error(f"Erreur lors de la validation DeepCourseOutput: {e}")
        return None
