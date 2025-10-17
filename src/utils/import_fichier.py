from __future__ import annotations
import os, io, re, base64, hashlib
from typing import Optional, Tuple

try:
    from pypdf import PdfReader
    _PYPDF = True
except Exception:
    _PYPDF = False

    PDF_MAGIC = b"%PDF-"

# ---------- Helpers basiques ----------
def is_pdf_ext(nom: str) -> bool:
    return nom.lower().endswith(".pdf")

def is_pdf_content_type(ct: Optional[str]) -> bool:
    return (ct or "").lower() == "application/pdf"

def starts_with_pdf_magic(b: bytes) -> bool:
    return len(b) >= len(PDF_MAGIC) and b[:len(PDF_MAGIC)] == PDF_MAGIC

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def count_pages(b: bytes) -> Optional[int]:
    if not _PYPDF:
        return None
    try:
        return len(PdfReader(io.BytesIO(b)).pages)
    except Exception:
        return None

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

# ---------- Sécurité nom de fichier ----------
_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")
def sanitize_filename(nom: str) -> str:
    """
    Retire les chemins, épure les caractères suspects.
    Conserve uniquement [a-zA-Z0-9._-], remplace le reste par '_'.
    """
    nom = os.path.basename(nom)
    # garde l'extension d’origine si .pdf sinon on force .pdf plus bas
    return _SAFE_NAME_RE.sub("_", nom)

# ---------- Décodage base64 avec garde-fous ----------
def decode_b64_to_bytes(b64: str, size_limit_mib: int = 50) -> Tuple[bool, Optional[bytes], str]:
    """
    Décode du base64 en bytes + limite de taille (MiB).
    Retourne (ok, bytes|None, message).
    """
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception:
        return False, None, "Le contenu base64 est invalide."
    if len(raw) == 0:
        return False, None, "Fichier vide."
    if len(raw) > size_limit_mib * 1024 * 1024:
        return False, None, f"Le fichier dépasse {size_limit_mib} MiB."
    return True, raw, "OK"

# ---------- Écriture avec anti-collision ----------
def write_unique(path_dir: str, desired_name: str, content: bytes) -> str:
    """
    Écrit le fichier dans path_dir. Si le nom existe déjà, suffixe avec 8 hex du sha256.
    Retourne le chemin absolu écrit.
    """
    ensure_dir(path_dir)
    chemin = os.path.join(path_dir, desired_name)
    if os.path.exists(chemin):
        h8 = sha256_hex(content)[:8]
        base, ext = os.path.splitext(desired_name)
        chemin = os.path.join(path_dir, f"{base}_{h8}{ext}")
    with open(chemin, "wb") as f:
        f.write(content)
    return os.path.abspath(chemin)