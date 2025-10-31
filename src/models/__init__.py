"""Output models for agents and API responses.

This package contains Pydantic models representing the outputs of various
agents (exercise, course, deep course) and tool results.
"""

from .cours_models import (
    CoursePlan,
    CourseOutput,
    CourseSynthesis,
    Part,
    PartPlanItem,
    PartSchema,
)
from .deepcourse_models import (
    Chapter,
    ChapterSynthesis,
    DeepCourseOutput,
    DeepCourseSynthesis,
)
from .exercise_models import (
    ClassifiedPlan,
    ExercicePlanItem,
    ExercisePlan,
    ExerciseSynthesis,
    ExerciseOutput,
    Open,
    QCM,
)
from .tool_models import GenerativeToolOutput

__all__ = [
    "Chapter",
    "ChapterSynthesis",
    "ClassifiedPlan",
    "CourseOutput",
    "CoursePlan",
    "CourseSynthesis",
    "DeepCourseOutput",
    "DeepCourseSynthesis",
    "ExercicePlanItem",
    "ExercisePlan",
    "ExerciseSynthesis",
    "ExerciseOutput",
    "GenerativeToolOutput",
    "Open",
    "Part",
    "PartPlanItem",
    "PartSchema",
    "QCM",
]
