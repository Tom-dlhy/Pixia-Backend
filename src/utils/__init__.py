from .exercises_utils import (
    generate_plain,
    generate_qcm,
    generate_for_topic,
    planner_exercises_async
)

from .get_db_url import create_db_pool, get_connection

from .cours_utils_v2 import (
    generate_complete_course,
    generate_all_schemas,
    generate_schema_mermaid,
)

from .cours_utils_quad_llm_integration import (
    generate_courses_quad_llm,
)

from .mermaid_validator import MermaidValidator

from .gemini_files import (
    upload_file,
    delete_file,
)

from .session_context import (
    add_gemini_file,
    add_gemini_file_name,
    get_gemini_files,
    get_gemini_file_names,
    clear_session,
)

from .correct_plain_question import agent_correct_plain_question

from .request_context import (
    set_request_context,
    get_document_id,
    get_user_id,
    get_deep_course_id,
    get_session_id,
)


__all__ = [
    "generate_plain",
    "generate_qcm",
    "generate_for_topic",
    "create_db_pool",
    "get_connection",
    "generate_complete_course",
    "generate_all_schemas",
    "generate_schema_mermaid",
    "generate_courses_quad_llm",
    "MermaidValidator",
    "upload_file",
    "delete_file",
    "add_gemini_file",
    "add_gemini_file_name",
    "get_gemini_files",
    "get_gemini_file_names",
    "clear_session",
    "agent_correct_plain_question",
    "planner_exercises_async",
    "set_request_context",
    "get_document_id",
    "get_user_id",
    "get_deep_course_id",
    "get_session_id",
]
