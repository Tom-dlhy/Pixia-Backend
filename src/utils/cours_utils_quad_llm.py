"""
Pipeline DUAL LLM v2: 4 agents spécialisés avec retry intelligent.

Workflow:
1. LLM #1: Génère contenu du cours + sélectionne le type de diagramme (4 types: mermaid, plantuml, graphviz, vegalite)
2. LLM #2 (spécialisé): Génère le code du diagramme syntaxiquement correct
3. Kroki: Convertit en SVG (ou JSON pour Vega-Lite)
4. Retry intelligent: Max 3 tentatives avec réinjection d'erreur Kroki
5. Async: Parallélisation complète de toutes les parties
"""

import asyncio
import json
import logging
import sys
from typing import Optional, Dict, Any
from uuid import uuid4
import base64
import hashlib
import subprocess
import os

from src.config import gemini_settings
from src.models.cours_models import CourseSynthesis, Part, CourseOutput
from src.prompts import SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE
from src.prompts.diagram_agents_prompts import (
    PROMPT_SELECT_DIAGRAM_TYPE_V2,
    SYSTEM_PROMPTS,
    SPECIALIZED_PROMPTS,
)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ============================================================================
# UTILITAIRES: Réparation JSON
# ============================================================================


def repair_json(json_str: str) -> str:
    """Tente de réparer du JSON malformé (commas manquantes, quotes, etc.)"""
    import re

    # Essayer d'abord le parsing direct
    try:
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError as e:
        logger.warning(f"[JSON-REPAIR] Tentative de réparation: {e}")

    # Réparation basique:
    # 1. Ajouter les commas manquantes après } ou ]
    repaired = re.sub(r'(}|])\s*(["\'{])', r"\1, \2", json_str)

    # 2. Échapper les quotes non échappées à l'intérieur des chaînes
    # (pattern simple: quote suivi d'une virgule ou bracket sans échappement)
    repaired = re.sub(r'([^\\])"(\s*[,}\]])', r"\1\\\" \2", repaired)

    # 3. Essayer de parser
    try:
        json.loads(repaired)
        logger.info(f"[JSON-REPAIR] ✅ JSON réparé avec succès")
        return repaired
    except:
        logger.error(f"[JSON-REPAIR] ❌ Impossible de réparer le JSON")
        return json_str


# ============================================================================
# ÉTAPE 1: LLM #1 - Génère contenu + type de diagramme (4 types)
# ============================================================================


def generate_course_with_diagram_types(
    synthesis: CourseSynthesis,
) -> Optional[Dict[str, Any]]:
    """
    LLM #1: Génère le cours complet avec contenu + type de diagramme recommandé par partie.
    Avec retry intelligent en cas de JSON malformé.

    Returns:
        Dict avec structure: { title, parts: [{ title, content, diagram_type }, ...] }
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(
                f"[LLM1-START] Génération cours + types de diagramme (tentative {attempt+1}/{max_retries})"
            )

            response = gemini_settings.CLIENT.models.generate_content(
                model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
                contents=f"""Description: {synthesis.description}
Difficulté: {synthesis.difficulty}
Niveau de détail: {synthesis.level_detail}""",
                config={
                    "system_instruction": SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE,
                    "response_mime_type": "application/json",
                },
            )

            # Tenter de parser le JSON (avec réparation si besoin)
            try:
                course_data = json.loads(response.text)
            except json.JSONDecodeError:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"[LLM1-JSON-ERROR] JSON malformé, retry avec strictness accrue (tentative {attempt+2}/{max_retries})"
                    )
                    continue
                logger.warning(f"[LLM1-JSON-ERROR] Tentative de réparation du JSON")
                repaired = repair_json(response.text)
                course_data = json.loads(repaired)

            logger.info(
                f"[LLM1-SUCCESS] Cours généré: {len(course_data.get('parts', []))} parties"
            )
            return course_data

        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"[LLM1-RETRY] Erreur tentative {attempt+1}, retry...")
                continue
            logger.error(
                f"[LLM1-ERROR] Erreur finale après {max_retries} tentatives: {e}",
                exc_info=False,
            )
            return None


# ============================================================================
# ÉTAPE 1.5: Sélection du type de diagramme (4 types seulement)
# ============================================================================


def select_diagram_type(title: str, content: str) -> str:
    """
    LLM intermédiaire: Demande à Gemini de choisir parmi les 4 types.
    """
    try:
        logger.debug(f"[DIAGRAM-SELECT] Sélection type pour: {title[:40]}")

        prompt = PROMPT_SELECT_DIAGRAM_TYPE_V2.replace("{title}", title[:100]).replace(
            "{content}", content[:500]
        )

        response = gemini_settings.CLIENT.models.generate_content(
            model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )

        result = json.loads(response.text)
        diagram_type = result.get("type", "mermaid").lower()

        # Valide que c'est l'un des 4 types
        valid_types = ["mermaid", "plantuml", "graphviz", "vegalite"]
        if diagram_type not in valid_types:
            logger.warning(
                f"[DIAGRAM-SELECT] Type invalide: {diagram_type}, défaut: mermaid"
            )
            diagram_type = "mermaid"

        logger.info(
            f"[DIAGRAM-SELECT-SUCCESS] Type sélectionné: {diagram_type} pour '{title[:40]}'"
        )
        return diagram_type

    except Exception as e:
        logger.error(f"[DIAGRAM-SELECT-ERROR] Erreur: {e}, défaut: mermaid")
        return "mermaid"


# ============================================================================
# ÉTAPE 2: LLM #2 (spécialisé) - Génère code du diagramme AVEC RETRY
# ============================================================================


def _test_kroki(diagram_code: str, diagram_type: str) -> Optional[str]:
    """
    Teste le code auprès de Kroki SANS sauvegarder le fichier.
    Retourne le SVG/output en base64 si succès, None sinon.
    """
    try:
        if not diagram_code or len(diagram_code.strip()) < 5:
            logger.debug(f"[KROKI-TEST] Code trop court: {len(diagram_code)} chars")
            return None

        kroki_endpoints = {
            "mermaid": "https://kroki.io/mermaid/svg",
            "plantuml": "https://kroki.io/plantuml/svg",
            "graphviz": "https://kroki.io/graphviz/svg",
            "vegalite": "https://kroki.io/vegalite/svg",
        }

        url = kroki_endpoints.get(diagram_type, "https://kroki.io/mermaid/svg")

        logger.debug(
            f"[KROKI-TEST] Testing {diagram_type} code ({len(diagram_code)} chars)"
        )
        logger.debug(f"[KROKI-TEST] Code preview: {diagram_code[:100]}...")

        cmd = [
            "curl",
            "-sS",
            "-f",
            "-X",
            "POST",
            "-H",
            "Content-Type: text/plain",
            url,
            "--data-binary",
            "@-",
        ]

        proc = subprocess.run(
            cmd,
            input=diagram_code.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=15,
        )

        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="ignore")
            stdout_err = proc.stdout.decode("utf-8", errors="ignore")
            logger.error(f"[KROKI-TEST-ERROR] Exit code {proc.returncode}")
            logger.error(f"[KROKI-TEST-ERROR] stderr: {err or 'empty'}")
            logger.error(f"[KROKI-TEST-ERROR] stdout: {stdout_err[:500] or 'empty'}")
            return None

        # Retourne le SVG en base64
        logger.debug(f"[KROKI-TEST-SUCCESS] SVG générée ({len(proc.stdout)} bytes)")
        return base64.b64encode(proc.stdout).decode("ascii")

    except subprocess.TimeoutExpired:
        logger.error(f"[KROKI-TEST-TIMEOUT] 15s timeout for {diagram_type}")
        return None
    except Exception as e:
        logger.error(f"[KROKI-TEST-EXCEPTION] {e}", exc_info=True)
        return None


def generate_diagram_code_with_retry(
    diagram_type: str, content: str, max_retries: int = 3
) -> Optional[str]:
    """
    LLM #2 avec retry intelligent: génère code → teste Kroki → si erreur, feedback au LLM.

    Max 3 tentatives avec réinjection d'erreur Kroki pour correction.
    """
    try:
        if diagram_type not in SPECIALIZED_PROMPTS:
            logger.error(f"[DIAGRAM-GEN-RETRY] Type non supporté: {diagram_type}")
            return None

        kroki_error = None

        for attempt in range(1, max_retries + 1):
            logger.info(
                f"[DIAGRAM-GEN-RETRY-{attempt}] Tentative {attempt}/{max_retries} pour {diagram_type}"
            )

            try:
                if attempt == 1:
                    # Première génération - utilise placeholder safe
                    base_prompt = SPECIALIZED_PROMPTS[diagram_type]
                    full_prompt = base_prompt.replace(
                        "%%CONTENT_PLACEHOLDER%%", content[:800]
                    )
                else:
                    # Retry avec feedback d'erreur
                    base_prompt = SPECIALIZED_PROMPTS[diagram_type]
                    base_prompt_filled = base_prompt.replace(
                        "%%CONTENT_PLACEHOLDER%%", content[:800]
                    )
                    correction_prompt = f"""{base_prompt_filled}

**TENTATIVE PRÉCÉDENTE #{attempt - 1} ÉCHOUÉE - CORRECTION REQUISE:**

Erreur Kroki reçue:
```
{kroki_error}
```

Corrigez le code pour éviter cette erreur. Vérifiez:
1. La syntaxe est EXACTEMENT conforme à {diagram_type}
2. Tous les éléments/nœuds/champs sont bien formés
3. Pas d'apostrophes ou guillemets mal fermés
4. Pas de caractères spéciaux non échappés
5. Tous les connecteurs/relations sont valides
6. Toutes les accolades/crochets sont fermés

Retournez UNIQUEMENT le code corrigé, prêt pour Kroki:
"""
                    full_prompt = correction_prompt
                    logger.debug(
                        f"[DIAGRAM-GEN-RETRY-{attempt}] Erreur injectée: {kroki_error[:100]}"
                    )
            except Exception as fmt_err:
                logger.error(
                    f"[DIAGRAM-GEN-RETRY-{attempt}] Erreur format prompt: {fmt_err}"
                )
                continue

            # LLM #2: Appel spécialisé
            logger.debug(f"[DIAGRAM-GEN-RETRY-{attempt}] Appel LLM spécialisé...")
            response = gemini_settings.CLIENT.models.generate_content(
                model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
                contents=full_prompt,
                config=(
                    {
                        "system_instruction": SYSTEM_PROMPTS.get(diagram_type, ""),
                    }
                    if attempt == 1
                    else {}
                ),
            )

            code = response.text.strip()

            # Nettoyage des backticks
            logger.info(
                f"[DIAGRAM-GEN-RETRY-{attempt}] Réponse LLM ({len(code)} chars)"
            )
            logger.debug(f"[DIAGRAM-GEN-RETRY-{attempt}] Preview: {code[:200]}")
            if code.startswith("```"):
                logger.debug(
                    f"[DIAGRAM-GEN-RETRY-{attempt}] Backticks détectés, nettoyage..."
                )
                parts = code.split("```")
                if len(parts) >= 2:
                    code = parts[1]
                    # Si commande commence par le type, nettoie
                    if code.startswith(diagram_type):
                        logger.debug(
                            f"[DIAGRAM-GEN-RETRY-{attempt}] Suppression préfixe {diagram_type}"
                        )
                        code = code[len(diagram_type) :].lstrip("\n")
                    if code.startswith(("json", "@", "digraph", "flowchart")):
                        # Déjà valide
                        pass
                    code = code.rstrip("`").strip()

            if not code or len(code.strip()) < 5:
                logger.warning(
                    f"[DIAGRAM-GEN-RETRY-{attempt}] Code vide après nettoyage ({len(code)} chars)"
                )
                continue

            logger.debug(
                f"[DIAGRAM-GEN-RETRY-{attempt}] Code final ({len(code)} chars): {code[:200]}"
            )

            # Teste le code avec Kroki (dry-run, sans sauvegarder)
            logger.info(f"[DIAGRAM-GEN-RETRY-{attempt}] Test Kroki...")
            test_svg = _test_kroki(code, diagram_type)

            if test_svg:
                logger.info(
                    f"[DIAGRAM-GEN-RETRY-SUCCESS] Code validé tentative {attempt}: {len(code)} chars"
                )
                return code
            else:
                # Récupère le dernier message d'erreur pour le prochain prompt
                kroki_error = f"Kroki a rejeté le code (test échoué à la tentative {attempt}). Corrigez la syntaxe."
                logger.warning(
                    f"[DIAGRAM-GEN-RETRY-{attempt}] Test Kroki échoué, réessai..."
                )
                continue

        logger.error(
            f"[DIAGRAM-GEN-RETRY] Toutes les tentatives échouées ({max_retries})"
        )
        return None

    except Exception as e:
        logger.error(f"[DIAGRAM-GEN-RETRY-ERROR] Erreur: {e}", exc_info=True)
        return None


# ============================================================================
# ÉTAPE 3: Kroki - Convertir en SVG
# ============================================================================


def generate_schema_svg(diagram_code: str, diagram_type: str) -> Optional[str]:
    """
    Envoie le code à Kroki, retourne SVG en base64.
    """
    try:
        if not diagram_code or len(diagram_code.strip()) < 5:
            logger.error(f"[KROKI] Code vide ou trop court")
            return None

        kroki_endpoints = {
            "mermaid": "https://kroki.io/mermaid/svg",
            "plantuml": "https://kroki.io/plantuml/svg",
            "graphviz": "https://kroki.io/graphviz/svg",
            "vegalite": "https://kroki.io/vegalite/svg",
        }

        url = kroki_endpoints.get(diagram_type, "https://kroki.io/mermaid/svg")

        logger.debug(f"[KROKI-CALL] Envoi {diagram_type} à {url}")

        cmd = [
            "curl",
            "-sS",
            "-f",
            "-X",
            "POST",
            "-H",
            "Content-Type: text/plain",
            url,
            "--data-binary",
            "@-",
        ]

        proc = subprocess.run(
            cmd,
            input=diagram_code.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=15,
        )

        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="ignore")
            out = proc.stdout.decode("utf-8", errors="ignore")[:200]
            logger.error(f"[KROKI-ERROR] Exit code {proc.returncode}")
            logger.error(f"[KROKI-ERROR] stderr: {err or '(empty)'}")
            logger.error(f"[KROKI-ERROR] stdout: {out or '(empty)'}")

            return None

        # Succès
        image_b64 = base64.b64encode(proc.stdout).decode("ascii")
        logger.info(f"[KROKI-SUCCESS] SVG généré: {len(image_b64)} chars base64")
        return image_b64

    except subprocess.TimeoutExpired:
        logger.error(f"[KROKI-TIMEOUT] Timeout (15s) pour {diagram_type}")
        return None
    except Exception as e:
        logger.error(f"[KROKI-EXCEPTION] Erreur: {e}")
        return None


# ============================================================================
# ÉTAPE 4: Pipeline complet pour UNE partie (async)
# ============================================================================


async def process_course_part(part_data: Dict[str, Any], index: int) -> Optional[Part]:
    """
    Traite UNE partie du cours:
    1. Sélectionne le type de diagramme (4 types)
    2. Génère le code du diagramme (LLM #2 spécialisé avec retry max 3)
    3. Convertit en SVG (Kroki)
    4. Retourne l'objet Part complet
    """
    try:
        title = part_data.get("title", f"Partie {index}")
        content = part_data.get("content", "")

        logger.info(f"[PART-{index}] Traitement: {title[:40]}")

        # Étape 1: Sélectionne le type (4 types)
        diagram_type = await asyncio.to_thread(select_diagram_type, title, content)

        # Étape 2: Génère le code (spécialisé) AVEC RETRY MAX 3
        diagram_code = await asyncio.to_thread(
            generate_diagram_code_with_retry, diagram_type, content
        )

        if not diagram_code:
            logger.warning(
                f"[PART-{index}] Code diagramme non généré après retry, SVG ignoré"
            )
            img_base64 = None
        else:
            # Étape 3: Génère SVG
            img_base64 = await asyncio.to_thread(
                generate_schema_svg, diagram_code, diagram_type
            )

        # Crée l'objet Part avec tous les champs (contenu + diagram_type + code + SVG)
        part = Part(
            id_part=str(uuid4()),
            id_schema=str(uuid4()),
            title=title,
            content=content,
            schema_description=part_data.get("schema_description", ""),
            diagram_type=diagram_type,
            diagram_code=diagram_code,
            img_base64=img_base64,
        )

        logger.info(f"[PART-{index}] ✅ Traitée avec {diagram_type}")
        return part

    except Exception as e:
        logger.error(f"[PART-{index}] Erreur: {e}", exc_info=True)
        return None


# ============================================================================
# PIPELINE PRINCIPAL - Orchestration complète
# ============================================================================


async def generate_course_complete(
    synthesis: CourseSynthesis,
) -> Optional[CourseOutput]:
    """
    Pipeline complet DUAL LLM v2:

    1. LLM #1: Génère contenu + type de diagramme (4 types: mermaid, plantuml, graphviz, vegalite)
    2. En PARALLÈLE pour chaque partie:
       a. LLM #2 (spécialisé): Code du diagramme avec retry max 3
       b. Kroki: Conversion en SVG
    3. Retourne CourseOutput complet

    Résultat: { titre, id, parties: [{ titre, id, contenu, img_base64 }] }
    """
    try:
        logger.info("[PIPELINE] Démarrage pipeline complet DUAL LLM v2")

        # ÉTAPE 1: LLM #1 - Génère le contenu + type
        logger.info("[PIPELINE] ÉTAPE 1/2: Génération contenu + types (4 types)")
        course_data = await asyncio.to_thread(
            generate_course_with_diagram_types, synthesis
        )

        if not course_data:
            logger.error("[PIPELINE] LLM #1 échoué")
            return None

        logger.info(
            f"[PIPELINE] ✅ ÉTAPE 1 complétée: {len(course_data.get('parts', []))} parties"
        )

        # ÉTAPE 2: Traitement parallèle de toutes les parties
        logger.info(
            "[PIPELINE] ÉTAPE 2/2: Traitement parallèle (LLM #2 spécialisé + Kroki)"
        )
        parts_data = course_data.get("parts", [])

        # Crée les tâches async pour TOUTES les parties EN PARALLÈLE
        tasks = [
            process_course_part(part_data, i)
            for i, part_data in enumerate(parts_data, 1)
        ]

        # Exécute en parallèle
        parts = await asyncio.gather(*tasks, return_exceptions=False)

        # Filtre les None (erreurs)
        parts = [p for p in parts if p is not None]

        if not parts:
            logger.error("[PIPELINE] Aucune partie générée")
            return None

        logger.info(f"[PIPELINE] ✅ ÉTAPE 2 complétée: {len(parts)} parties avec SVG")

        # Crée le CourseOutput final
        course_output = CourseOutput(
            id=str(uuid4()),
            title=course_data.get("title", "Cours"),
            parts=parts,
        )

        logger.info(
            f"[PIPELINE] ✅ PIPELINE COMPLET: {len(course_output.parts)} parties"
        )
        return course_output

    except Exception as e:
        logger.error(f"[PIPELINE] Erreur fatale: {e}", exc_info=True)
        return None
