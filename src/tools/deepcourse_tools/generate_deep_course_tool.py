

from src.models import DeepCourseSynthesis


async def generate_deepcourse(synthesis: DeepCourseSynthesis) -> dict:
    if isinstance(synthesis, dict):
        synthesis = DeepCourseSynthesis(**synthesis)
    print(synthesis.model_dump())
    return synthesis.model_dump()