import os, hashlib, subprocess, base64
from src.models import PartSchema, Part
from src.config import gemini_settings
from google.genai import types
from uuid import uuid4
import logging
from src.prompts import SYSTEM_PROMPT_GENERATE_MERMAID_CODE

logging.basicConfig(level=logging.INFO)

def generate_schema_mermaid(mermaid_code: str) :
    """
    Envoie le code Mermaid à Kroki via curl, récupère le SVG et l'enregistre dans folder_path.
    Retourne le fichier SVG créé en base 64.
    """
    folder_path="."
    os.makedirs(folder_path, exist_ok=True)

    digest = hashlib.sha256(mermaid_code.encode("utf-8")).hexdigest()[:16]
    out_path = os.path.join(folder_path, f"mermaid_{digest}.svg")

    cmd = [
        "curl", "-sS", "-f",
        "-X", "POST",
        "-H", "Content-Type: text/plain",
        "https://kroki.io/mermaid/svg",
        "--data-binary", "@-",
    ]
    proc = subprocess.run(
        cmd,
        input=mermaid_code.encode("utf-8"),
        capture_output=True,
        check=False,
    )

    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"curl a échoué (exit {proc.returncode}) : {err or 'aucun message'}")
    try :
        with open(out_path, "wb") as f:
            f.write(proc.stdout)
        with open(out_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("ascii")
    finally:
        try: 
            os.remove(out_path)
        except Exception as e:
            logging.warning(f"Impossible de supprimer le {out_path}: {e}")
        
    return image_b64

def generate_mermaid_schema_description(course_part: Part):
    """
    Génère 
    """
    schema_description = ""
    if isinstance(course_part.schema_description, str):
        schema_description = course_part.schema_description
    try:
        response = gemini_settings.CLIENT.models.generate_content(
            model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
            contents=SYSTEM_PROMPT_GENERATE_MERMAID_CODE + "\n" + schema_description,
            config=types.GenerateContentConfig(
                response_modalities=['Text'],
            )
        )
        uuid_schema = str(uuid4())
        mermaid_code = ""
        if getattr(response, "candidates", None):
            for cand in response.candidates:
                content = getattr(cand, "content", None)
                if content and getattr(content, "parts", None):
                    for p in content.parts:
                        if getattr(p, "text", None):
                            mermaid_code += p.text

        mermaid_code = (mermaid_code or "").strip()
        if not mermaid_code:
            logging.error("Le modèle n'a pas renvoyé de code Mermaid.")
            return None

        img_b64 = generate_schema_mermaid(mermaid_code)

        return PartSchema(
            id_schema=uuid_schema,
            id_part=course_part.id_part,
            img_base64=img_b64
        )
    except Exception as e:
        logging.error(f"Erreur lors de la génération du schéma: {e}")
    
    return None
