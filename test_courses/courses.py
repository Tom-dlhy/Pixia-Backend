import asyncio
import json
import logging
import time
import uuid
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from mermaid_function import run_mermaid_prompt

logging.basicConfig(level=logging.INFO)

from src.config import gemini_settings


class CourseSynthesis(BaseModel):
    description: str = Field(
        ..., description="Description détaillée du sujet du cours à générer."
    )
    difficulty: str = Field(..., description="Niveau de difficulté du cours.")
    type: Literal["flash", "standard", "detailed"] = Field(
        "standard", description="Niveau de détail du cours."
    )


class CoursePlan(BaseModel):
    title: str = Field(..., description="Titre du cours généré.")
    chapters: List[tuple[str, str]] = Field(
        ...,
        description="Plan du cours sous forme de liste de sections ou chapitres [titre, explication du contenu du chapitre].",
    )
    estimated_duration: Optional[str] = Field(
        None, description="Durée estimée du cours."
    )


class Course_Schema(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique du schéma")
    description: str = Field(..., description="Description du schéma à générer")
    svg_base64: str = Field(..., description="Schéma Mermaid SVG encodé en base64")


class Chapter(BaseModel):
    title: str = Field(..., description="Titre du chapitre.")
    content: str = Field(..., description="Contenu détaillé du chapitre.")
    schemas: Optional[List[Course_Schema]] = Field(
        None,
        description="Liste de schémas Mermaid SVG encodés en base64 pour illustrer le chapitre.",
    )


class StandardCourse(BaseModel):
    type: Literal["standard"] = Field("standard", description="Toujours standard.")
    title: str = Field(..., description="Titre du cours généré.")
    outline: List[str] = Field(
        ..., description="Plan du cours sous forme de liste de sections ou chapitres."
    )
    chapters: List[Chapter] = Field(
        ..., description="Liste des chapitres détaillés du cours."
    )
    estimated_duration: Optional[str] = Field(
        None, description="Durée estimée du cours."
    )


class DetailedCourse(BaseModel):
    type: Literal["detailed"] = Field("detailed", description="Toujours detailed.")
    title: str = Field(..., description="Titre du cours généré.")
    outline: List[str] = Field(
        ..., description="Plan du cours sous forme de liste de sections ou chapitres."
    )
    chapters: List[Chapter] = Field(
        ..., description="Liste des chapitres détaillés du cours."
    )
    estimated_duration: Optional[str] = Field(
        None, description="Durée estimée du cours."
    )


class FlashCourse(BaseModel):
    type: Literal["flash"] = Field("flash", description="Toujours flash.")
    title: str = Field(..., description="Titre du cours généré.")
    chapter: Chapter = Field(..., description="Chapitre du cours.")
    estimated_duration: Optional[str] = Field(
        None, description="Durée estimée du cours."
    )


SYS_PROMPT_COURSE_PLAN_FLASH = """
Tu es un assistant pédagogique spécialisé dans la création de cours flash (≤ 10 minutes).

Objectif : produire un JSON conforme au schéma suivant, sans texte additionnel :
{
    "type": "flash",
    "title": "Titre du cours",
    "chapter": {
        "title": "Titre du chapitre",
        "content": "Contenu rédigé en Markdown, concis et pédagogique",
        "schemas": [
            {
                "id": null,
                "description": "Description précise du schéma Mermaid à générer",
                "svg_base64": ""
            }
        ]
    },
    "estimated_duration": "Durée totale (ex. '8 minutes')"
}

Contraintes :
- Toujours respecter le format JSON indiqué et le schéma Pydantic associé.
- Le contenu doit être cohérent avec la description et la difficulté fournies dans le prompt utilisateur.
- Le chapitre doit aller à l'essentiel tout en proposant des exemples concrets ou des mini exercices pour favoriser l'assimilation rapide.
- Génère entre 0 et 3 schémas maximum. Pour chaque schéma, écris une description opérationnelle (objectif, éléments clés, relations) et laisse le champ "svg_base64" vide. Il sera rempli dynamiquement par l'application.
- Utilise le Markdown pour structurer le contenu (titres, listes, formules si nécessaire).
- N'ajoute aucun commentaire ou texte hors du JSON final.
"""

SYS_PROMPT_COURSE_PLAN_STANDARD = """
Tu es un assistant pédagogique spécialisé dans la création de plans de cours clairs et détaillés.
"""

SYS_PROMPT_COURSE_PLAN_DETAILED = """
Tu es un assistant pédagogique spécialisé dans la création de plans de cours très détaillés et approfondis.
"""


def _run_mermaid_diagram(prompt: str) -> List[str]:
    try:
        logging.debug("Lancement asynchrone run_mermaid_prompt (len=%d)", len(prompt))
        return asyncio.run(run_mermaid_prompt(prompt))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            logging.debug("Boucle dédiée run_mermaid_prompt (len=%d)", len(prompt))
            return loop.run_until_complete(run_mermaid_prompt(prompt))
        finally:
            loop.close()


def generate_flash_course(description: str, difficulty: str) -> FlashCourse:
    user_prompt = f"""
    Sujet du cours : {description}
    Niveau : {difficulty}
    Contrainte : produire le JSON d'un cours flash conforme aux instructions du système.
    """

    start_time = time.time()

    logging.info(
        "Début génération cours flash (description='%s', difficulty='%s')",
        description,
        difficulty,
    )

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
        contents=user_prompt.strip(),
        config={
            "system_instruction": SYS_PROMPT_COURSE_PLAN_FLASH,
            "response_mime_type": "application/json",
            "response_schema": FlashCourse,
        },
    )

    logging.debug(
        "Réponse brute reçue pour le cours flash: %s",
        getattr(response, "parsed", None) or getattr(response, "text", None),
    )

    raw = response.parsed if hasattr(response, "parsed") else response

    try:
        if isinstance(raw, FlashCourse):
            course = raw
        elif isinstance(raw, dict):
            course = FlashCourse.model_validate(raw)
        else:
            course = FlashCourse.model_validate_json(str(raw))
    except Exception as err:
        logging.error("Erreur de validation du cours flash: %s", err)
        raise

    schemas = list(course.chapter.schemas or [])
    logging.debug("Nombre de schémas demandés: %d", len(schemas))
    for schema in schemas:
        schema.id = schema.id or uuid.uuid4().hex
        logging.debug("Préparation schéma '%s' (id=%s)", schema.description, schema.id)
        diagram_prompt = (
            f"{SYS_PROMPT_COURSE_PLAN_FLASH}\n\n"
            "Génère un schéma Mermaid correspondant à la description suivante :\n"
            f"- Cours : {course.title}\n"
            f"- Niveau : {difficulty}\n"
            f"- Description du schéma : {schema.description}\n"
            "Utilise uniquement l'outil `generate_mermaid_diagram` avec `outputType`='svg', "
            "`theme`='default' et `backgroundColor`='white'."
        )

        try:
            logging.debug(
                "Appel run_mermaid_prompt pour schéma '%s'", schema.description
            )
            diagrams = _run_mermaid_diagram(diagram_prompt)
            logging.debug(
                "Résultat schéma '%s': %d diagrammes", schema.description, len(diagrams)
            )
        except Exception as err:
            logging.error(
                "Erreur lors de la génération du schéma '%s': %s",
                schema.description,
                err,
            )
            diagrams = []

        if diagrams:
            schema.svg_base64 = f"data:image/svg+xml;base64,{diagrams[0]}"
        else:
            logging.warning("Aucun schéma généré pour '%s'", schema.description)
            schema.svg_base64 = ""

    course.chapter.schemas = schemas or None

    end_time = time.time()
    logging.info(
        "Temps de génération du cours flash : %.2f secondes", end_time - start_time
    )

    return course


if __name__ == "__main__":
    description = "Les bases des nombres complexes"
    difficulty = "Licence 1"

    course = generate_flash_course(description, difficulty)

    # Sauvegarde JSON dans test_courses/json_preview
    JSON_OUTPUT_DIR = Path(__file__).resolve().parent / "json_preview"
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = JSON_OUTPUT_DIR / f"{timestamp}_flash_course.json"
    try:
        output_path.write_text(
            json.dumps(course.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logging.info("Prévisualisation JSON sauvegardée dans %s", output_path)
    except Exception as e:
        logging.error("Erreur lors de la sauvegarde JSON: %s", e)

    print(json.dumps(course.model_dump(), indent=2, ensure_ascii=False))
