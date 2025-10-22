#!/usr/bin/env python3
"""
Convertir le Mermaid généré en HTML visualisable
"""

import asyncio
import sys
from src.models.cours_models import CourseSynthesis
from src.utils.cours_utils_v2 import generate_complete_course, generate_all_schemas


async def generate_and_export_html():
    """Génère un cours et l'exporte en HTML"""

    synthesis = CourseSynthesis(
        description="Les variables en Python",
        difficulty="Débutant",
        level_detail="standard",
    )

    print("[1] Génération LLM...")
    course = await asyncio.to_thread(generate_complete_course, synthesis)

    if not course:
        print("❌ Erreur LLM")
        return

    print(f"[2] Génération Kroki...")
    course = await generate_all_schemas(course)

    # Crée HTML avec tous les diagrammes Mermaid
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{course.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .course {{ max-width: 1200px; margin: 0 auto; }}
        .part {{ background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .diagram {{ background: white; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        pre {{ background: #f9f9f9; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="course">
        <h1>📚 {course.title}</h1>
        <p><small>ID: {course.id}</small></p>
"""

    for i, part in enumerate(course.parts, 1):
        html += f"""
        <div class="part">
            <h2>Partie {i}: {part.title}</h2>
            <p>{part.content}</p>
            
            <div class="diagram">
                <h3>Schéma:</h3>
                <div class="mermaid">
{part.mermaid_syntax or "N/A"}
                </div>
            </div>
            
            <details>
                <summary>Code Mermaid brut</summary>
                <pre>{part.mermaid_syntax or "N/A"}</pre>
            </details>
        </div>
"""

    html += """
    </div>
    <script>
        mermaid.contentLoaded();
    </script>
</body>
</html>
"""

    # Sauvegarde
    filename = "course_output.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Cours exporté: {filename}")
    print(f"   Ouvre dans le navigateur: open {filename}")


if __name__ == "__main__":
    try:
        asyncio.run(generate_and_export_html())
    except KeyboardInterrupt:
        print("\n⏹️  Interruption utilisateur")
        sys.exit(0)
