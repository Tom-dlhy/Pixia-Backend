"""Integration of dual-LLM pipeline for course generation.

This module replaces simple part generation (1 LLM) with a specialized
dual-LLM pipeline featuring intelligent diagram type selection.

Pipeline architecture:
1. LLM #1: Generates markdown content + selects diagram type (4 types)
   for ALL course parts at once
2. LLM #2 (specialized) IN PARALLEL: Generates diagram code with up to 3 retries
3. Kroki IN PARALLEL: Converts code to PNG base64
4. CourseOutput: Returns complete course with content, diagram_type, diagram_code, img_base64
"""

import logging
from typing import Any

from src.models.cours_models import CourseSynthesis, CourseOutput
from src.utils.cours_utils_quad_llm import generate_course_complete


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_courses_quad_llm(
    course_synthesis: Any,
    planner_func=None,
) -> CourseOutput:
    """Generate complete course using dual-LLM specialized pipeline.

    Process:
    1. ADK agent obtains CourseSynthesis with description, difficulty, level_detail
    2. Optimized dual-LLM pipeline:
       - LLM #1: Generates content + diagram types for ALL parts
       - IN PARALLEL for each part:
         * LLM #2 (specialized): Diagram code based on type (max 3 retries)
         * Kroki: PNG base64
    3. CourseOutput returned with markdown content + complete diagrams

    Note: The planner is not used directly since LLM #1 already generates
    the structure. For integration with existing planner, see
    generate_courses_with_planner().

    Args:
        course_synthesis: CourseSynthesis with description, difficulty, level_detail
        planner_func: Optional (not used in this pipeline)

    Returns:
        CourseOutput with all generated parts

    Raises:
        ValueError: If pipeline fails or returns invalid data
    """
    if isinstance(course_synthesis, dict):
        course_synthesis = CourseSynthesis.model_validate(course_synthesis)

    try:
        # Use existing optimized dual-LLM pipeline
        # This pipeline already generates complete course structure
        result = await generate_course_complete(course_synthesis)

        if not result:
            logger.error("[PIPELINE] Dual-LLM pipeline failed - result is None")
            # Re-raise for caller to handle
            raise ValueError("Pipeline failed: no result")

        if not isinstance(result, CourseOutput):
            logger.error(
                f"[PIPELINE] Dual-LLM pipeline failed - wrong type: {type(result)}"
            )
            raise ValueError(f"Pipeline failed: wrong type {type(result)}")

        return result

    except Exception as e:
        logger.error(f"[PIPELINE] Error: {e}", exc_info=True)
        # Re-raise for caller to handle properly
        raise
