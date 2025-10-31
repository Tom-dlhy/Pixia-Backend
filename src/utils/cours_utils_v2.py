"""
Course generation utilities with integrated Mermaid diagrams.

Optimized architecture: single LLM call generates complete course content
with Mermaid schemas in one pass, then generates diagrams asynchronously.
"""

import asyncio
import base64
import hashlib
import logging
import os
import subprocess
import sys
from typing import Any, Dict, Optional
from uuid import uuid4

from src.config import gemini_settings
from src.models.cours_models import (
    CourseOutput,
    CourseSynthesis,
    Part,
)
from src.prompts import SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE
from src.utils.mermaid_validator import MermaidValidator

logger = logging.getLogger(__name__)


def generate_schema_mermaid(mermaid_code: str) -> Optional[str]:
    """
    Send Mermaid code to Kroki API, retrieve PNG and return as base64.

    Validates Mermaid syntax before sending, sanitizes code, and handles
    temporary file cleanup automatically.

    Args:
        mermaid_code: Validated Mermaid code

    Returns:
        PNG image encoded as base64 string, or None on failure

    Raises:
        No exceptions raised; all errors logged and None returned
    """
    try:

        is_valid, error_msg = MermaidValidator.validate(mermaid_code)
        if not is_valid:
            logger.error(f"[KROKI-INVALID] Invalid Mermaid code: {error_msg}")
            return None

        mermaid_code = MermaidValidator.sanitize(mermaid_code)
        digest = hashlib.sha256(mermaid_code.encode("utf-8")).hexdigest()[:16]
        out_path = os.path.join(".", f"mermaid_{digest}.png")

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

        proc = subprocess.run(
            cmd,
            input=mermaid_code.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=10,
        )

        logger.debug(f"[KROKI-RESPONSE] Return code: {proc.returncode}")

        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="ignore")
            logger.error(f"[KROKI-ERROR] Kroki error (exit {proc.returncode}): {err or 'unknown'}")
            return None

        try:
            with open(out_path, "wb") as f:
                f.write(proc.stdout)

            with open(out_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("ascii")

            return image_b64

        finally:
            try:
                os.remove(out_path)
            except Exception as e:
                logger.warning(f"[KROKI-CLEANUP] Could not remove {out_path}: {e}")

    except subprocess.TimeoutExpired:
        logger.error("[KROKI-TIMEOUT] Timeout (10s) on Kroki call")
        return None
    except Exception as e:
        logger.error(f"[KROKI-EXCEPTION] Error: {e}", exc_info=True)
        return None


def generate_complete_course(
    synthesis: CourseSynthesis,
) -> Optional[CourseOutput]:
    """
    Generate complete course with content and Mermaid diagrams in single LLM call.

    Calls Gemini once to generate all course parts with diagram specifications,
    then generates diagrams asynchronously.

    Args:
        synthesis: CourseSynthesis with description, difficulty, detail level

    Returns:
        Generated CourseOutput with all parts and Mermaid schemas, or None on failure
    """
    try:
        if isinstance(synthesis, dict):
            synthesis = CourseSynthesis.model_validate(synthesis)

        try:
            response = gemini_settings.CLIENT.models.generate_content(
                model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
                contents=f"""
                        Description: {synthesis.description}
                        Difficulté: {synthesis.difficulty}
                        Niveau de détail: {synthesis.level_detail}
                    """,
                config={
                    "system_instruction": SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE,
                    "response_mime_type": "application/json",
                    "response_schema": CourseOutput,
                },
            )
        except Exception as gemini_err:
            logger.error(f"[LLM-GEMINI-ERROR] Gemini API error: {gemini_err}", exc_info=True)
            raise

        course_output = (
            response.parsed if hasattr(response, "parsed") else response.text
        )

        if isinstance(course_output, str):
            course_output = CourseOutput.model_validate_json(course_output)
        elif isinstance(course_output, dict):
            course_output = CourseOutput.model_validate(course_output)

        if not isinstance(course_output, CourseOutput):
            raise ValueError(f"Invalid response type: {type(course_output)}")

        if not course_output.id:
            course_output.id = str(uuid4())

        for part in course_output.parts:
            if not part.id_part:
                part.id_part = str(uuid4())
            if not part.id_schema:
                part.id_schema = str(uuid4())

        return course_output

    except Exception as e:
        logger.error(f"[LLM-ERROR] Fatal error: {e}", exc_info=True)
        return None


async def generate_all_schemas(
    course_output: CourseOutput,
) -> CourseOutput:
    """
    Generate all Mermaid diagrams in parallel.

    Asynchronously generates diagrams for all course parts using thread pool
    to avoid blocking the event loop.

    Args:
        course_output: Course with Mermaid code (text) to generate from

    Returns:
        CourseOutput with generated diagram base64 strings
    """
    try:

        tasks: list[tuple[int, Part, Any]] = []
        for i, part in enumerate(course_output.parts):
            if hasattr(part, 'content') and part.content:
                logger.debug(f"[ASYNC-TASK-{i}] Creating task for: {part.title[:30]}")
                task = asyncio.to_thread(generate_schema_mermaid, part.content)
                tasks.append((i, part, task))

        if tasks:
            results = await asyncio.gather(
                *[task for _, _, task in tasks], return_exceptions=True
            )

            for (i, part, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.warning(f"[ASYNC-ERROR-{i}] Error for part {i+1}: {result}")
                elif result and isinstance(result, str):
                    logger.info(f"[ASYNC-SUCCESS-{i}] Diagram {i+1} generated ({len(result)} chars)")
                else:
                    logger.warning(f"[ASYNC-EMPTY-{i}] Diagram {i+1} empty (Kroki failed)")

        return course_output

    except Exception as e:
        logger.error(f"[ASYNC-EXCEPTION] Parallelization error: {e}", exc_info=True)
        return course_output


# ===== COMPATIBILITY HELPERS =====
# Kept for backwards compatibility with legacy code


def generate_part(title: str, content: str, difficulty: str) -> Dict[str, Any]:
    """
    DEPRECATED: Use generate_complete_course() instead.

    Legacy function kept for backward compatibility.

    Args:
        title: Section title
        content: Section content
        difficulty: Difficulty level

    Returns:
        Empty dict (deprecated)
    """
    logger.warning("generate_part() is deprecated. Use generate_complete_course() instead.")
    return {}


def generate_mermaid_schema_description(course_part: Any) -> Optional[Dict[str, Any]]:
    """
    DEPRECATED: Use generate_complete_course() instead.

    Legacy function kept for backward compatibility.

    Args:
        course_part: Course part object

    Returns:
        None (deprecated)
    """
    logger.warning(
        "generate_mermaid_schema_description() is deprecated. Use generate_complete_course() instead."
    )
    return None

