"""
Mermaid diagram code validator.

Validates Mermaid syntax before sending to Kroki to prevent rendering errors.
Provides sanitization and structural validation for various diagram types.
"""

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)


class MermaidValidator:
    """Validates Mermaid diagram syntax."""

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
        Validate Mermaid code syntax.

        Args:
            mermaid_code: Mermaid code to validate

        Returns:
            Tuple with (is_valid, error_message)
        """
        if not mermaid_code or not mermaid_code.strip():
            return False, "Mermaid code is empty."

        code_stripped = mermaid_code.strip()

        # Check for valid diagram type
        has_valid_start = any(
            re.match(pattern, code_stripped)
            for pattern in MermaidValidator.VALID_DIAGRAM_TYPES.values()
        )

        if not has_valid_start:
            return (
                False,
                f"Code must start with valid diagram type: {', '.join(MermaidValidator.VALID_DIAGRAM_TYPES.keys())}",
            )

        # Check for backticks
        if "```" in code_stripped:
            return (
                False,
                "Code must not contain backticks (```). Raw code only.",
            )

        # Warn about Mermaid comments
        if "%%" in code_stripped:
            logger.warning("Mermaid comments (%%) detected and will be removed.")

        # Check bracket balance
        if not MermaidValidator._check_brackets_balance(code_stripped):
            return False, "Unbalanced brackets or parentheses."

        # Warn about complex diagrams
        node_count = MermaidValidator._count_nodes(code_stripped)
        if node_count > 50:
            logger.warning(
                f"Complex diagram: {node_count} nodes (recommended limit: 50)"
            )

        return True, ""

    @staticmethod
    def _check_brackets_balance(code: str) -> bool:
        """
        Check if brackets and parentheses are balanced.

        Args:
            code: Code to check

        Returns:
            True if balanced, False otherwise
        """
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
        """
        Estimate node count using simple pattern matching.

        Args:
            code: Mermaid code

        Returns:
            Approximate number of nodes
        """
        matches = re.findall(r"\w+\s*(?:\[|\()", code)
        return len(set(matches))

    @staticmethod
    def sanitize(mermaid_code: str) -> str:
        """
        Clean Mermaid code for valid rendering.

        Removes backticks, comments, and excess whitespace.

        Args:
            mermaid_code: Raw code

        Returns:
            Cleaned Mermaid code
        """
        code = mermaid_code.replace("```", "").replace("`", "")
        code = re.sub(r"%%.*", "", code)
        code = code.strip()

        return code

