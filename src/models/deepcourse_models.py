from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, List, Union, Optional, Literal, Dict, Any
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
    

def _validate_deepcourse_output(data: dict | str | Dict[str, Any] | DeepCourseOutput) -> DeepCourseOutput | None:
    """Valide et parse les données en tant qu'DeepCourseOutput."""
    import logging
    import json
    
    logger = logging.getLogger(__name__)
    
    try:
        if isinstance(data, DeepCourseOutput):
            return data
        
        elif isinstance(data, dict):
            logger.debug(f"📊 Type détecté: dict, clés présentes: {list(data.keys())}")
            
            # Extraire les données si imbriquées dans 'result'
            extracted_data = data
            if 'result' in data:
                logger.debug(f"🔍 Clé 'result' détectée, extraction...")
                if isinstance(data['result'], dict):
                    extracted_data = data['result']
                    logger.debug(f"✓ Données extraites de 'result', clés: {list(extracted_data.keys())}")
                elif isinstance(data['result'], DeepCourseOutput):
                    logger.debug(f"✓ 'result' est déjà une instance DeepCourseOutput")
                    return data['result']
            
            logger.debug(f"📋 Tentative de validation avec données: {list(extracted_data.keys())}")
            return DeepCourseOutput.model_validate(extracted_data)
        
        elif isinstance(data, str):
            logger.debug(f"📊 Type détecté: str (JSON)")
            try:
                parsed = json.loads(data)
                logger.debug(f"✓ JSON parsé, clés: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}")
                
                # Extraire si nécessaire
                if isinstance(parsed, dict) and 'result' in parsed:
                    logger.debug(f"🔍 Clé 'result' détectée dans JSON")
                    parsed = parsed['result']
                    logger.debug(f"✓ Données extraites, clés: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}")
                
                return DeepCourseOutput.model_validate(parsed)
            except (json.JSONDecodeError, ValueError) as je:
                logger.debug(f"⚠️ Erreur JSON parsing: {je}, tentative avec model_validate_json")
                return DeepCourseOutput.model_validate_json(data)
        
        else:
            logger.warning(f"⚠️ Type non supporté: {type(data)}")
            return None
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la validation DeepCourseOutput: {e}")
        logger.debug(f"📦 Données brutes (type={type(data)}): {str(data)[:500]}...")
        return None