import os, io, re, base64, hashlib, textwrap
from typing import Optional, Tuple, List

try:
    from pypdf import PdfReader
    _PYPDF = True
except Exception:
    _PYPDF = False

PDF_MAGIC = b"%PDF-"
_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


# --- Vérifications basiques ---
def is_pdf_ext(nom: str) -> bool:
    return nom.lower().endswith(".pdf")

def is_pdf_content_type(ct: Optional[str]) -> bool:
    ct = (ct or "").lower().split(";")[0].strip()
    return ct == "application/pdf"

def starts_with_pdf_magic(b: bytes) -> bool:
    return len(b) >= len(PDF_MAGIC) and b[:len(PDF_MAGIC)] == PDF_MAGIC


# --- Utilitaires fichiers / sécurité ---
def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def sanitize_filename(nom: str) -> str:
    """Retire les chemins et caractères spéciaux non sûrs."""
    return _SAFE_NAME_RE.sub("_", os.path.basename(nom))


# --- Gestion Base64 ---
def decode_b64_to_bytes(b64: str, size_limit_mib: int = 50) -> Tuple[bool, Optional[bytes], str]:
    """Décode du base64 avec vérification et limite de taille."""
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception:
        return False, None, "Le contenu base64 est invalide."
    if len(raw) == 0:
        return False, None, "Fichier vide."
    if len(raw) > size_limit_mib * 1024 * 1024:
        return False, None, f"Le fichier dépasse {size_limit_mib} MiB."
    return True, raw, "OK"


# --- Écriture avec anti-collision ---
def write_unique(path_dir: str, desired_name: str, content: bytes) -> str:
    """Écrit le fichier et ajoute un suffixe hash si un fichier du même nom existe."""
    ensure_dir(path_dir)
    chemin = os.path.join(path_dir, desired_name)
    if os.path.exists(chemin):
        h8 = sha256_hex(content)[:8]
        base, ext = os.path.splitext(desired_name)
        chemin = os.path.join(path_dir, f"{base}_{h8}{ext}")
    with open(chemin, "wb") as f:
        f.write(content)
    return os.path.abspath(chemin)


# --- Lecture PDF / extraction texte ---
def count_pages(b: bytes) -> Optional[int]:
    if not _PYPDF:
        return None
    try:
        return len(PdfReader(io.BytesIO(b)).pages)
    except Exception:
        return None

def extract_text_from_pdf_bytes(b: bytes) -> str:
    """Extrait tout le texte du PDF (naïf mais efficace)."""
    if not _PYPDF:
        return ""
    try:
        reader = PdfReader(io.BytesIO(b))
        textes = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(textes).strip()
    except Exception:
        return ""


# --- Découpage du texte en chunks ---
def chunk_text(s: str, max_chars: int = 6000, max_chunks: int = 5) -> List[str]:
    """Découpe un texte en morceaux exploitables par le LLM."""
    if not s:
        return []
    chunks = textwrap.wrap(s, width=max_chars, break_long_words=False, break_on_hyphens=False)
    if len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
    return chunks


# --- Dossiers de session ---
def session_upload_dir(session_id: str) -> str:
    return os.path.join("data", "sessions", sanitize_filename(session_id), "uploads")

def session_text_dir(session_id: str) -> str:
    return os.path.join("data", "sessions", sanitize_filename(session_id), "texts")