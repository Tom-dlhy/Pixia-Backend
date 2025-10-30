"""Dual LLM Pipeline v2: 4 specialized agents - single attempt per part.

Workflow:
1. LLM #1: Generate course content + select diagram type
2. LLM #2 (specialized): Generate diagram code - no retry
3. Kroki: Convert to PNG - no prior test
4. If error: continue without diagram for that part
5. Async: Full parallelization of all parts
"""

import asyncio
import base64
import logging
import subprocess
import sys
from typing import Any, Dict, Optional, Union, cast
from uuid import uuid4

from src.config import gemini_settings
from src.models.cours_models import CourseOutput, CourseSynthesis, Part
from src.prompts import SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE
from src.prompts.diagram_agents_prompts import (
    SPECIALIZED_PROMPTS,
    SYSTEM_PROMPTS,
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
) -> Optional[Union[CourseOutput, Dict[str, Any]]]:
    """Generate complete course asynchronously with content + recommended diagram type per part.

    Uses Google's async client without blocking thread.

    Returns:
        Dict with structure: { title, parts: [{ title, content, diagram_type }, ...] }
    """

    response = await gemini_settings.CLIENT.aio.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
        contents=f"""Description: {synthesis.description}
Difficulty: {synthesis.difficulty}
Detail level: {synthesis.level_detail}""",
        config={
            "system_instruction": SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE,
            "response_mime_type": "application/json",
            "response_schema": CourseOutput,
        },
    )
    try:
        data = cast(Union[CourseOutput, Dict[str, Any]], response.parsed)
        if not data:
            logger.error("[LLM #1] response.parsed is None")
            return None
        return data
    except Exception as err:
        logging.error(f"[LLM #1] Parsing error {err}")
        return None


# ============================================================================
# STEP 2: LLM #2 (specialized) - Generate diagram code
# ============================================================================


async def generate_diagram_code(diagram_type: str, content: str) -> Optional[str]:
    """Generate diagram code - single attempt, no retry.

    If fails, continue without diagram for this part.
    Async version - uses CLIENT.aio without blocking.
    """
    with Timer(f"Generate {diagram_type} code"):
        try:
            if diagram_type not in SPECIALIZED_PROMPTS:
                logger.error(f"[DIAGRAM-GEN] Unsupported type: {diagram_type}")
                return None

            # Single generation
            base_prompt = SPECIALIZED_PROMPTS[diagram_type]
            full_prompt = base_prompt.replace("%%CONTENT_PLACEHOLDER%%", content[:800])

            # LLM #2: Specialized call with CLIENT.aio (async)
            response = await gemini_settings.CLIENT.aio.models.generate_content(
                model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
                contents=full_prompt,
                config={
                    "system_instruction": SYSTEM_PROMPTS.get(diagram_type, ""),
                },
            )

            code = (response.text or "").strip()

            # Clean backticks
            if code.startswith("```"):
                parts = code.split("```")
                if len(parts) >= 2:
                    code = parts[1]
                    if code.startswith(diagram_type):
                        code = code[len(diagram_type) :].lstrip("\n")
                    code = code.rstrip("`").strip()

            if not code or len(code.strip()) < 5:
                logger.warning(f"[DIAGRAM-GEN] Empty code ({len(code)} chars)")
                return None

            return code

        except Exception as e:
            logger.error(f"[DIAGRAM-GEN-ERROR] Error: {e}", exc_info=False)
            return None


# ============================================================================
# STEP 3: Kroki - Convert to PNG
# ============================================================================


def generate_schema_png(diagram_code: str, diagram_type: str) -> Optional[str]:
    """Send diagram code to Kroki, return PNG as base64."""
    with Timer(f"Kroki PNG {diagram_type}"):
        try:
            if not diagram_code or len(diagram_code.strip()) < 5:
                logger.error(f"[KROKI] Empty or too short code")
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

            # Success
            image_b64 = base64.b64encode(proc.stdout).decode("ascii")
            return image_b64

        except subprocess.TimeoutExpired:
            logger.error(f"[KROKI-TIMEOUT] Timeout (15s) for {diagram_type}")
            return None
        except Exception as e:
            logger.error(f"[KROKI-EXCEPTION] Error: {e}")
            return None


# ============================================================================
# STEP 4: Complete pipeline for one part (async)
# ============================================================================


async def process_course_part(part_data: Dict[str, Any], index: int) -> Optional[Part]:
    """Process one course part:
    
    1. Get diagram type
    2. Generate diagram code (LLM #2 specialized - single attempt)
    3. Convert to PNG (Kroki)
    4. Return complete Part object
    """
    try:
        title = part_data.get("title", f"Part {index}")
        content = part_data.get("content", "")

        # Step 1: Select type (4 types)
        diagram_type = part_data.get("diagram_type", "mermaid")

        # Step 2: Generate code (specialized) - single attempt async
        diagram_code = await generate_diagram_code(diagram_type, content)

        if not diagram_code:
            logger.warning(f"[PART-{index}] Diagram code not generated, PNG skipped")
            img_base64 = None
        else:
            # Step 3: Generate PNG
            img_base64 = await asyncio.to_thread(
                generate_schema_png, diagram_code, diagram_type
            )

        # Create Part object with all fields (content + diagram_type + code + PNG)
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
        logger.error(f"[PART-{index}] Error: {e}", exc_info=True)
        return None


# ============================================================================
# MAIN PIPELINE - Complete orchestration
# ============================================================================


async def generate_course_complete(
    synthesis: CourseSynthesis,
) -> Optional[CourseOutput]:
    """Complete DUAL LLM v2 pipeline - single attempt:

    1. LLM #1: Generate content + diagram type
    2. In PARALLEL for each part:
       a. LLM #2 (specialized): Diagram code - single attempt
       b. Kroki: Convert to PNG
    3. Return complete CourseOutput

    Result: { title, id, parts: [{ title, id, content, img_base64 }] }
    """
    with Timer("TOTAL Complete course"):
        try:

            course_data = await generate_course_with_diagram_types_async(synthesis)

            if not course_data:
                logger.error("[PIPELINE] LLM #1 failed")
                return None

            if isinstance(course_data, CourseOutput):
                parts_data = [p.model_dump() for p in course_data.parts]
            else:
                parts_data = course_data.get("parts", [])

            # Create async tasks for ALL parts IN PARALLEL
            tasks = [
                process_course_part(part_data, i)
                for i, part_data in enumerate(parts_data, 1)
            ]

            parts = await asyncio.gather(*tasks, return_exceptions=False)

            # Filter None values (errors)
            parts = [p for p in parts if p is not None]

            if not parts:
                logger.error("[PIPELINE] No parts generated")
                return None

            # Create final CourseOutput
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
            logger.error(f"[PIPELINE] Fatal error: {e}", exc_info=True)
            return None
