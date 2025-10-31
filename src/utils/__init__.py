"""Utility functions and helpers for the hackathon backend.

This package provides core utilities for:
- Database connection management
- Course and exercise generation
- Request context handling
- File operations and validation
"""

from .context_builder import final_context_builder
from .correct_plain_question import agent_correct_plain_question
from .cours_utils_quad_llm_integration import generate_courses_quad_llm
from .cours_utils_v2 import (
    generate_all_schemas,
    generate_complete_course,
    generate_schema_mermaid,
)
from .exercises_utils import (
    generate_for_topic,
    generate_plain,
    generate_qcm,
    planner_exercises_async,
)
from .get_db_url import create_db_pool, get_connection
from .mermaid_validator import MermaidValidator
from .request_context import (
    get_deep_course_id,
    get_document_id,
    get_session_id,
    get_user_id,
    set_request_context,
)
from .save_files import save_course_as_pdf

__all__ = [
    "agent_correct_plain_question",
    "create_db_pool",
    "final_context_builder",
    "generate_all_schemas",
    "generate_complete_course",
    "generate_courses_quad_llm",
    "generate_for_topic",
    "generate_plain",
    "generate_qcm",
    "generate_schema_mermaid",
    "get_connection",
    "get_deep_course_id",
    "get_document_id",
    "get_session_id",
    "get_user_id",
    "MermaidValidator",
    "planner_exercises_async",
    "save_course_as_pdf",
    "set_request_context",
]
