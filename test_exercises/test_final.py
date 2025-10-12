from src.tools.exercises_tools import generate_exercises
from src.models import ExerciseSynthesis

if __name__ == "__main__":
    import asyncio
    import json

    description = "Les bases des nombres complexes"
    difficulty = "Licence 1"
    number_of_exercises = 3
    exercise_type = "both"  # Options: "qcm", "open", "both"

    synthesis = ExerciseSynthesis(
        description=description,
        difficulty=difficulty,
        number_of_exercises=number_of_exercises,
        exercise_type=exercise_type
    )

    exercises = asyncio.run(
        generate_exercises(synthesis)
    )

    print("\n=== ✅ Exercices finaux générés ===\n")
    for idx, ex in enumerate(exercises, start=1):
        print(f"\n--- Exercice Final {idx} ---")
        if hasattr(ex, "model_dump"):
            data = ex.model_dump()
        else:
            data = ex if isinstance(ex, dict) else json.loads(ex)
        print(json.dumps(data, indent=2, ensure_ascii=False))
