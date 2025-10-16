import os
import base64
import tempfile
from pathlib import Path
from dotenv import load_dotenv

def load_gcp_credentials() -> str:
    """
    Charge les credentials GCP à partir d'une variable d'environnement encodée en base64.
    Si GOOGLE_APPLICATION_CREDENTIALS_B64 est définie, on la décode et on crée un fichier temporaire .json.
    Sinon, on suppose que GOOGLE_APPLICATION_CREDENTIALS pointe déjà vers un vrai fichier JSON.

    Returns:
        str: chemin absolu du fichier credentials JSON utilisé.
    """
    load_dotenv()

    # 1️⃣ Priorité à la variable base64
    b64_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_B64")
    if b64_creds:
        decoded = base64.b64decode(b64_creds)
        tmp_dir = Path(tempfile.gettempdir())
        tmp_path = tmp_dir / "gcp_credentials.json"

        with open(tmp_path, "wb") as f:
            f.write(decoded)

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(tmp_path)
        print(f"🔐 GCP credentials chargés depuis variable B64 → {tmp_path}")
        return str(tmp_path)

    # 2️⃣ Fallback : fichier JSON standard
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and Path(creds_path).exists():
        print(f"✅ GCP credentials trouvés : {creds_path}")
        return creds_path

    raise FileNotFoundError(
        "Aucune clé GCP trouvée. "
        "Définis GOOGLE_APPLICATION_CREDENTIALS_B64 (Base64) ou GOOGLE_APPLICATION_CREDENTIALS (path)."
    )
