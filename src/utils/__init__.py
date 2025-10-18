from .exercises_utils import (
    generate_plain, 
    generate_qcm, 
    planner_exercises, 
    generate_for_topic, 
    assign_uuids_to_output
)

from .get_db_url import create_db_pool, get_connection

from .import_fichier import (
    is_pdf_ext, is_pdf_content_type, starts_with_pdf_magic,
    sha256_hex, decode_b64_to_bytes, write_unique, count_pages,
    extract_text_from_pdf_bytes, chunk_text, sanitize_filename,
    session_upload_dir, session_text_dir
)


from .cours_utils import (
    planner_cours,
    generate_for_chapter
)


__all__ = [
    "generate_plain",
    "generate_qcm",
    "planner_exercises",
    "generate_for_topic",
    "assign_uuids_to_output",
    "create_db_pool",
    "get_connection",
    "is_pdf_ext",
    "is_pdf_content_type",
    "starts_with_pdf_magic",
    "sha256_hex",
    "decode_b64_to_bytes",
    "write_unique",
    "count_pages",
    "extract_text_from_pdf_bytes",
    "chunk_text",
    "sanitize_filename",
    "session_upload_dir",
    "session_text_dir",
    "planner_cours",
    "generate_for_chapter"
]