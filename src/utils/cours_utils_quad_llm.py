"""
Pipeline DUAL LLM v2: 4 agents spécialisés - UNE SEULE TENTATIVE PAR PARTIE.

Workflow:
1. LLM #1: Génère contenu du cours + sélectionne le type de diagramme
2. LLM #2 (spécialisé): Génère le code du diagramme - pas de retry
3. Kroki: Convertit en PNG - pas de test préalable
4. Si erreur: on continue sans le schéma pour cette partie
5. Async: Parallélisation complète de toutes les parties
"""

import asyncio
import json
import logging
import sys
from typing import Optional, Dict, Any, Union
from uuid import uuid4
import base64
import subprocess

from src.config import gemini_settings
from src.models.cours_models import CourseSynthesis, Part, CourseOutput
from src.prompts import SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE
from src.prompts.diagram_agents_prompts import (
    SYSTEM_PROMPTS,
    SPECIALIZED_PROMPTS,
)
from src.utils.timing import Timer

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def generate_course_with_diagram_types_async(
    synthesis: CourseSynthesis,
) -> Union[CourseOutput, Dict[str, Any]]:
    """
    Version async de LLM #1 - utilise le client async de Google.

    Génère le cours complet avec contenu + type de diagramme recommandé par partie
    sans bloquer le thread.

    Returns:
        Dict avec structure: { title, parts: [{ title, content, diagram_type }, ...] }
    """

    response = await gemini_settings.CLIENT.aio.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
        contents=f"""Description: {synthesis.description}
Difficulté: {synthesis.difficulty}
Niveau de détail: {synthesis.level_detail}""",
        config={
            "system_instruction": SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE,
            "response_mime_type": "application/json",
            "response_schema": CourseOutput,
        },
    )
    try:
        data = response.parsed
        if not data:
            logger.error("[LLM #1] response.parsed est None")
            return None
        return data
    except Exception as err:
        logging.error(f"[LLM #1] Erreur parsing {err}")
        return None


# ============================================================================
# ÉTAPE 2: LLM #2 (spécialisé) - Génère code du diagramme
# ============================================================================


async def generate_diagram_code(diagram_type: str, content: str) -> Optional[str]:
    """
    LLM #2: Génère le code du diagramme - UNE SEULE TENTATIVE, SANS RETRY.
    Si ça échoue, tant pis - on continue sans schéma pour cette partie.
    Version async - utilise CLIENT.aio sans bloquer.
    """
    with Timer(f"Génération code {diagram_type}"):
        try:
            if diagram_type not in SPECIALIZED_PROMPTS:
                logger.error(f"[DIAGRAM-GEN] Type non supporté: {diagram_type}")
                return None

            # Génération unique
            base_prompt = SPECIALIZED_PROMPTS[diagram_type]
            full_prompt = base_prompt.replace("%%CONTENT_PLACEHOLDER%%", content[:800])

            # LLM #2: Appel spécialisé avec CLIENT.aio (async)
            response = await gemini_settings.CLIENT.aio.models.generate_content(
                model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
                contents=full_prompt,
                config={
                    "system_instruction": SYSTEM_PROMPTS.get(diagram_type, ""),
                },
            )

            code = response.text.strip()

            # Nettoyage des backticks
            if code.startswith("```"):
                parts = code.split("```")
                if len(parts) >= 2:
                    code = parts[1]
                    if code.startswith(diagram_type):
                        code = code[len(diagram_type) :].lstrip("\n")
                    code = code.rstrip("`").strip()

            if not code or len(code.strip()) < 5:
                logger.warning(f"[DIAGRAM-GEN] Code vide ({len(code)} chars)")
                return None

            return code

        except Exception as e:
            logger.error(f"[DIAGRAM-GEN-ERROR] Erreur: {e}", exc_info=False)
            return None


# ============================================================================
# ÉTAPE 3: Kroki - Convertir en PNG
# ============================================================================


def generate_schema_png(diagram_code: str, diagram_type: str) -> Optional[str]:
    """
    Envoie le code à Kroki, retourne PNG en base64.
    """
    with Timer(f"PNG Kroki {diagram_type}"):
        try:
            if not diagram_code or len(diagram_code.strip()) < 5:
                logger.error(f"[KROKI] Code vide ou trop court")
                return None

            kroki_endpoints = {
                "mermaid": "https://kroki.io/mermaid/png",
                "plantuml": "https://kroki.io/plantuml/png",
                "graphviz": "https://kroki.io/graphviz/png",
                "vegalite": "https://kroki.io/vegalite/png",
            }

            url = kroki_endpoints.get(diagram_type, "https://kroki.io/mermaid/png")

            cmd = [
                "curl",
                "-sS",
                "-f",
                "-X",
                "POST",
                "-H",
                "Content-Type: text/plain",
                url,
                "--data-binary",
                "@-",
            ]

            proc = subprocess.run(
                cmd,
                input=diagram_code.encode("utf-8"),
                capture_output=True,
                check=False,
                timeout=30,
            )

            if proc.returncode != 0:
                err = proc.stderr.decode("utf-8", errors="ignore")
                out = proc.stdout.decode("utf-8", errors="ignore")[:200]
                logger.error(f"[KROKI-ERROR] Exit code {proc.returncode}")
                logger.error(f"[KROKI-ERROR] stderr: {err or '(empty)'}")
                logger.error(f"[KROKI-ERROR] stdout: {out or '(empty)'}")
                return None

            # Succès
            image_b64 = base64.b64encode(proc.stdout).decode("ascii")
            return image_b64

        except subprocess.TimeoutExpired:
            logger.error(f"[KROKI-TIMEOUT] Timeout (15s) pour {diagram_type}")
            return None
        except Exception as e:
            logger.error(f"[KROKI-EXCEPTION] Erreur: {e}")
            return None


# ============================================================================
# ÉTAPE 4: Pipeline complet pour UNE partie (async)
# ============================================================================


async def process_course_part(part_data: Dict[str, Any], index: int) -> Optional[Part]:
    """
    Traite UNE partie du cours:
    1. Récupère le type de diagramme
    2. Génère le code du diagramme (LLM #2 spécialisé - UNE SEULE TENTATIVE)
    3. Convertit en PNG (Kroki)
    4. Retourne l'objet Part complet
    """
    try:
        title = part_data.get("title", f"Partie {index}")
        content = part_data.get("content", "")

        # Étape 1: Sélectionne le type (4 types)
        diagram_type = part_data.get("diagram_type", "mermaid")

        # Étape 2: Génère le code (spécialisé) - UNE SEULE TENTATIVE async
        diagram_code = await generate_diagram_code(diagram_type, content)

        if not diagram_code:
            logger.warning(f"[PART-{index}] Code diagramme non généré, PNG ignoré")
            img_base64 = None
        else:
            # Étape 3: Génère PNG
            img_base64 = await asyncio.to_thread(
                generate_schema_png, diagram_code, diagram_type
            )

        # Crée l'objet Part avec tous les champs (contenu + diagram_type + code + PNG)
        part = Part(
            id_part=str(uuid4()),
            id_schema=str(uuid4()),
            title=title,
            content=content,
            schema_description=part_data.get("schema_description", ""),
            diagram_type=diagram_type,
            diagram_code=diagram_code,
            img_base64=img_base64,
        )

        return part

    except Exception as e:
        logger.error(f"[PART-{index}] Erreur: {e}", exc_info=True)
        return None


# ============================================================================
# PIPELINE PRINCIPAL - Orchestration complète
# ============================================================================


async def generate_course_complete(
    synthesis: CourseSynthesis,
) -> Optional[CourseOutput]:
    """
    Pipeline complet DUAL LLM v2 - UNE SEULE TENTATIVE:

    1. LLM #1: Génère contenu + type de diagramme
    2. En PARALLÈLE pour chaque partie:
       a. LLM #2 (spécialisé): Code du diagramme - UNE SEULE TENTATIVE
       b. Kroki: Conversion en PNG
    3. Retourne CourseOutput complet

    Résultat: { titre, id, parties: [{ titre, id, contenu, img_base64 }] }
    """
    with Timer("TOTAL Cours complet"):
        try:

            course_data = await generate_course_with_diagram_types_async(synthesis)

            if not course_data:
                logger.error("[PIPELINE] LLM #1 échoué")
                return None

            if isinstance(course_data, CourseOutput):
                parts_data = [p.model_dump() for p in course_data.parts]
            else:
                parts_data = course_data.get("parts", [])

            # Crée les tâches async pour TOUTES les parties EN PARALLÈLE
            tasks = [
                process_course_part(part_data, i)
                for i, part_data in enumerate(parts_data, 1)
            ]

            parts = await asyncio.gather(*tasks, return_exceptions=False)

            # Filtre les None (erreurs)
            parts = [p for p in parts if p is not None]

            if not parts:
                logger.error("[PIPELINE] Aucune partie générée")
                return None

            # Crée le CourseOutput final
            course_output = CourseOutput(
                id=str(uuid4()),
                title=(
                    course_data.title
                    if isinstance(course_data, CourseOutput)
                    else course_data.get("title", "Cours")
                ),
                parts=parts,
            )

            return course_output

        except Exception as e:
            logger.error(f"[PIPELINE] Erreur fatale: {e}", exc_info=True)
            return None
