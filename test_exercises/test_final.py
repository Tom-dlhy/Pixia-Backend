from src.tools.exercises_tools import generate_exercises

if __name__ == "__main__":
    import asyncio
    import json

    description = "Les bases de la physique"
    difficulty = "college 4e"
    number_of_exercises = 2
    exercise_type = "both"  # Options: "qcm", "open", "both"

    exercises = asyncio.run(
        generate_exercises(description, difficulty, number_of_exercises, exercise_type)
    )

    print("\n=== ✅ Exercices finaux générés ===\n")
    for idx, ex in enumerate(exercises, start=1):
        print(f"\n--- Exercice Final {idx} ---")
        if hasattr(ex, "model_dump"):
            data = ex.model_dump()
        else:
            data = ex if isinstance(ex, dict) else json.loads(ex)
        print(json.dumps(data, indent=2, ensure_ascii=False))
