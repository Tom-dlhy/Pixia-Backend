"""Copilot tools for retrieving document context.

Provides tools for agents to fetch and analyze course and exercise content.
"""

from .fetch_context_deep_course_tool import fetch_context_deep_course_tool
from .fetch_context_tool import fetch_context_tool

__all__ = ["fetch_context_tool", "fetch_context_deep_course_tool"]
