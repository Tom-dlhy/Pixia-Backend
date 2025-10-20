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
)

from .gemini_files import (
    upload_file as gemini_upload_file,
    delete_file as gemini_delete_file,
)

from .session_context import (
    add_gemini_file,
    get_gemini_files,
    clear_session,
)


__all__ = [
    "generate_plain",
    "generate_qcm",
    "planner_exercises",
    "generate_for_topic",
    "assign_uuids_to_output",
    "create_db_pool",
    "get_connection",
    "planner_cours",
    "generate_for_chapter",
    "gemini_upload_file",
    "gemini_delete_file",
    "add_gemini_file",
    "get_gemini_files",
    "clear_session",
]
