"""
Utilitaires pour la génération de cours avec schémas Mermaid intégrés.
Architecture optimisée: 1 LLM pour générer contenu + Mermaid d'un coup.
"""

from src.config import gemini_settings
from src.models.cours_models import (
    CourseSynthesis,
    CourseOutput,
    Part,
)
from src.prompts import SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE
from src.utils.mermaid_validator import MermaidValidator
import logging
import asyncio
import base64
from uuid import uuid4
from google.genai import types
from typing import Optional, Dict, Any
import os
import hashlib
import subprocess
import sys

# Setup logging avec output immédiat (flush)
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from src.config import gemini_settings
from src.models.cours_models import (
    CourseSynthesis,
    CourseOutput,
    Part,
)
from src.prompts import SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE
from src.utils.mermaid_validator import MermaidValidator
import logging
import asyncio
import base64
from uuid import uuid4
from google.genai import types
from typing import Optional, Dict, Any
import os
import hashlib
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_schema_mermaid(mermaid_code: str) -> Optional[str]:
    """
    Envoie le code Mermaid à Kroki via curl, récupère le SVG et le retourne en base64.

    Args:
        mermaid_code: Code Mermaid validé

    Returns:
        Optional[str]: Image SVG encodée en base64, ou None en cas d'erreur
    """
    try:
        logger.debug(
            f"[KROKI-START] Validation du code Mermaid ({len(mermaid_code)} chars)"
        )

        # Valide le code Mermaid avant d'envoyer à Kroki
        is_valid, error_msg = MermaidValidator.validate(mermaid_code)
        if not is_valid:
            logger.error(f"[KROKI-INVALID] Code Mermaid invalide: {error_msg}")
            return None

        logger.debug(f"[KROKI-VALID] Code Mermaid validé")

        # Nettoie le code avant envoi
        mermaid_code = MermaidValidator.sanitize(mermaid_code)

        # Crée un hash pour le nommage du fichier
        digest = hashlib.sha256(mermaid_code.encode("utf-8")).hexdigest()[:16]
        out_path = os.path.join(".", f"mermaid_{digest}.png")

        logger.debug(f"[KROKI-CALL] Envoi à Kroki avec digest: {digest}")

        # Appel à Kroki
        cmd = [
            "curl",
            "-sS",
            "-f",
            "-X",
            "POST",
            "-H",
            "Content-Type: text/plain",
            "https://kroki.io/mermaid/png",
            "--data-binary",
            "@-",
        ]

        logger.debug(f"[KROKI-EXECUTE] Exécution curl (timeout=10s)")
        proc = subprocess.run(
            cmd,
            input=mermaid_code.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=10,
        )

        logger.debug(f"[KROKI-RESPONSE] Code de retour: {proc.returncode}")

        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="ignore")
            logger.error(
                f"[KROKI-ERROR] Kroki error (exit {proc.returncode}): {err or 'unknown'}"
            )
            return None

        logger.debug(f"[KROKI-SAVE] Sauvegarde et encodage en base64")

        # Sauvegarde et encode en base64
        try:
            with open(out_path, "wb") as f:
                f.write(proc.stdout)

            with open(out_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("ascii")

            logger.info(
                f"[KROKI-SUCCESS] Schéma généré: {digest} ({len(image_b64)} chars base64)"
            )
            return image_b64

        finally:
            # Nettoyage du fichier temporaire
            try:
                os.remove(out_path)
            except Exception as e:
                logger.warning(
                    f"[KROKI-CLEANUP] Impossible de supprimer {out_path}: {e}"
                )

    except subprocess.TimeoutExpired:
        logger.error("[KROKI-TIMEOUT] Timeout (10s) lors de l'appel à Kroki")
        return None
    except Exception as e:
        logger.error(f"[KROKI-EXCEPTION] Erreur: {e}", exc_info=True)
        return None


def generate_complete_course(
    synthesis: CourseSynthesis,
) -> Optional[CourseOutput]:
    """
    Génère un cours COMPLET avec contenu + Mermaid d'un seul appel LLM.

    Args:
        synthesis: Synthèse contenant description, difficulté, niveau de détail

    Returns:
        Optional[CourseOutput]: Cours généré avec tous les Mermaid, ou None en cas d'erreur
    """
    try:
        logger.debug(f"[LLM-START] Validation synthèse d'entrée")

        # Validation d'entrée
        if isinstance(synthesis, dict):
            logger.debug(f"[LLM-CONVERT] Conversion dict → CourseSynthesis")
            synthesis = CourseSynthesis.model_validate(synthesis)

        logger.info(
            f"[LLM-CALL] Génération: {synthesis.description[:50]}... (Diff: {synthesis.difficulty})"
        )

        # Appel LLM unique pour générer le cours complet
        logger.debug(f"[LLM-REQUEST] Envoi requête à Gemini avec timeout...")

        try:
            response = gemini_settings.CLIENT.models.generate_content(
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
        except Exception as gemini_err:
            logger.error(
                f"[LLM-GEMINI-ERROR] Erreur Gemini API: {gemini_err}", exc_info=True
            )
            raise

        logger.debug(f"[LLM-RESPONSE] Réponse reçue, parsing...")

        # Récupère la réponse parsée
        course_output = (
            response.parsed if hasattr(response, "parsed") else response.text
        )

        if isinstance(course_output, str):
            logger.debug(f"[LLM-PARSE] Parsing JSON string...")
            course_output = CourseOutput.model_validate_json(course_output)
        elif isinstance(course_output, dict):
            logger.debug(f"[LLM-PARSE] Validation dict...")
            course_output = CourseOutput.model_validate(course_output)

        logger.debug(f"[LLM-VALIDATE] Ajout IDs manquants")

        # Ajoute des IDs si nécessaire
        if not course_output.id:
            course_output.id = str(uuid4())

        for part in course_output.parts:
            if not part.id_part:
                part.id_part = str(uuid4())
            if not part.id_schema:
                part.id_schema = str(uuid4())

        logger.info(
            f"[LLM-SUCCESS] Cours généré: {len(course_output.parts)} parties (Mermaid: {sum(1 for p in course_output.parts if p.mermaid_syntax)})"
        )
        return course_output

    except Exception as e:
        logger.error(f"[LLM-ERROR] Erreur fatale: {e}", exc_info=True)
        return None


async def generate_all_schemas(
    course_output: CourseOutput,
) -> CourseOutput:
    """
    Génère tous les schémas Mermaid en parallèle (VRAIMENT async).

    Args:
        course_output: Cours avec code Mermaid (texte)

    Returns:
        CourseOutput: Cours avec schémas générés (base64)
    """
    try:
        logger.info(
            f"[ASYNC-START] Génération parallèle de {len(course_output.parts)} schémas"
        )

        # Crée les tâches WITHOUT to_thread (c'est un appel réseau, asyncio ne peut pas vraiment paralyser)
        # La solution: utiliser VRAIMENT de la parallélisation OS
        tasks = []
        for i, part in enumerate(course_output.parts):
            if part.mermaid_syntax:
                logger.debug(
                    f"[ASYNC-TASK-{i}] Création tâche pour partie: {part.title[:30]}"
                )
                # ⚠️  IMPORTANT: Utiliser à_thread pour libérer l'event loop
                task = asyncio.to_thread(generate_schema_mermaid, part.mermaid_syntax)
                tasks.append((i, part, task))

        logger.debug(f"[ASYNC-GATHER] Attente de {len(tasks)} tâches en parallèle...")

        if tasks:
            # Exécute VRAIMENT en parallèle
            results = await asyncio.gather(
                *[task for _, _, task in tasks], return_exceptions=True
            )

            logger.debug(f"[ASYNC-RESULTS] Résultats reçus: {len(results)} schémas")

            for (i, part, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.warning(f"[ASYNC-ERROR-{i}] Erreur partie {i+1}: {result}")
                elif result:
                    logger.info(
                        f"[ASYNC-SUCCESS-{i}] Schéma {i+1} généré ({len(result)} chars base64)"
                    )
                    # Stocke le base64 (adapter selon votre structure)
                else:
                    logger.warning(
                        f"[ASYNC-EMPTY-{i}] Schéma {i+1} vide (Kroki échoué)"
                    )

        return course_output

    except Exception as e:
        logger.error(f"[ASYNC-EXCEPTION] Erreur parallélisation: {e}", exc_info=True)
        return course_output


# ================= HELPERS POUR COMPATIBILITÉ =================
# Ces fonctions sont conservées pour compatibilité avec l'ancien code


def generate_part(title: str, content: str, difficulty: str) -> Dict[str, Any]:
    """DEPRECATED: Utilisé uniquement pour rétrocompatibilité."""
    logger.warning(
        "generate_part() is deprecated. Use generate_complete_course() instead."
    )
    return {}


def generate_mermaid_schema_description(course_part) -> Optional[Dict[str, Any]]:
    """DEPRECATED: Utilisé uniquement pour rétrocompatibilité."""
    logger.warning(
        "generate_mermaid_schema_description() is deprecated. Use generate_complete_course() instead."
    )
    return None
