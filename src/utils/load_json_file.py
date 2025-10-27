import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

def load_json_file(filename: str) -> dict:
    """Charge un fichier JSON depuis le répertoire tests/"""
    # Path(__file__).parent.parent.parent est le répertoire racine du projet
    # de src/app/api/test.py -> src/app/api -> src/app -> src -> racine
    file_path = Path(__file__).parent.parent.parent.parent / "tests" / filename
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger_instance = logging.getLogger(__name__)
        logger_instance.error(f"❌ Error loading {filename} from {file_path}: {str(e)}")
        return {}