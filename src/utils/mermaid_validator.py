"""
Validateur pour le code Mermaid.
S'assure que le code est syntaxiquement valide avant d'être envoyé à Kroki.
"""

import re
import logging
from typing import Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MermaidValidator:
    """Valide la syntaxe du code Mermaid."""

    # Patterns de validation pour chaque type de diagramme
    VALID_DIAGRAM_TYPES = {
        "graph": r"^graph\s+(TD|LR|BT|RL)",
        "sequenceDiagram": r"^sequenceDiagram",
        "classDiagram": r"^classDiagram",
        "erDiagram": r"^erDiagram",
        "stateDiagram": r"^stateDiagram-v2",
        "gantt": r"^gantt",
        "journey": r"^journey",
    }

    @staticmethod
    def validate(mermaid_code: str) -> Tuple[bool, str]:
        """
        Valide le code Mermaid.

        Args:
            mermaid_code: Code Mermaid à valider

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not mermaid_code or not mermaid_code.strip():
            return False, "Le code Mermaid est vide."

        code_stripped = mermaid_code.strip()

        # Vérifie que le code commence par un type de diagramme valide
        has_valid_start = any(
            re.match(pattern, code_stripped)
            for pattern in MermaidValidator.VALID_DIAGRAM_TYPES.values()
        )

        if not has_valid_start:
            return (
                False,
                f"Le code doit commencer par un type de diagramme valide: {', '.join(MermaidValidator.VALID_DIAGRAM_TYPES.keys())}",
            )

        # Vérifie qu'il n'y a pas de backticks
        if "```" in code_stripped:
            return (
                False,
                "Le code ne doit pas contenir de backticks (```). Code brut uniquement.",
            )

        # Vérifie qu'il n'y a pas de commentaires Mermaid
        if "%%" in code_stripped:
            logger.warning("Code Mermaid avec commentaires (%%) détectés. Suppression.")

        # Vérifie la balance des accolades et parenthèses
        if not MermaidValidator._check_brackets_balance(code_stripped):
            return False, "Les accolades/parenthèses ne sont pas équilibrées."

        # Vérifie le nombre de nœuds (limite)
        node_count = MermaidValidator._count_nodes(code_stripped)
        if node_count > 50:
            logger.warning(
                f"Diagramme complexe: {node_count} nœuds (limite recommandée: 50)"
            )

        return True, ""

    @staticmethod
    def _check_brackets_balance(code: str) -> bool:
        """Vérifie que les accolades et crochets sont équilibrés."""
        brackets = {"[": "]", "{": "}", "(": ")"}
        stack = []

        for char in code:
            if char in brackets:
                stack.append(char)
            elif char in brackets.values():
                if not stack or brackets[stack.pop()] != char:
                    return False

        return len(stack) == 0

    @staticmethod
    def _count_nodes(code: str) -> int:
        """Compte approximativement le nombre de nœuds."""
        # Pattern simple pour compter les identifiants
        matches = re.findall(r"\w+\s*(?:\[|\()", code)
        return len(set(matches))

    @staticmethod
    def sanitize(mermaid_code: str) -> str:
        """
        Nettoie le code Mermaid pour le rendre valide.

        Args:
            mermaid_code: Code brut

        Returns:
            str: Code Mermaid nettoyé
        """
        # Supprime les backticks si présents
        code = mermaid_code.replace("```", "").replace("`", "")

        # Supprime les commentaires Mermaid
        code = re.sub(r"%%.*", "", code)

        # Supprime les espaces inutiles au début/fin
        code = code.strip()

        return code
