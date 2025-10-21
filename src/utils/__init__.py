from .exercises_utils import (
    generate_plain, 
    generate_qcm, 
    planner_exercises, 
    generate_for_topic, 
    assign_uuids_to_output
)


from .get_db_url import create_db_pool, get_connection

from .cours_utils import (
    planner_cours,
    generate_for_chapter
    generate_for_part,
    assign_uuids_to_output_course
)

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

from .generate_title import generate_title_from_messages
from .correct_plain_question import agent_correct_plain_question


__all__ = [
    "generate_plain",
    "generate_qcm",
    "planner_exercises",
    "generate_for_topic",
    "assign_uuids_to_output",
    "assign_uuids_to_output_course",
    "create_db_pool",
    "get_connection",
    "planner_cours",
    "generate_for_part",
    "upload_file",
    "delete_file",
    "add_gemini_file",
    "add_gemini_file_name",
    "get_gemini_files",
    "get_gemini_file_names",
    "clear_session",
    "generate_title_from_messages",
    "agent_correct_plain_question",
]


