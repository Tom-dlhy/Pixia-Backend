"""
Tests et validation de l'architecture refactorisée.
"""

import asyncio
import json
from src.models.cours_models import CourseSynthesis, CourseOutputWithMermaid
from src.utils.mermaid_validator import MermaidValidator
from src.tools.cours_tools.generate_cours_tool_v2 import generate_courses


# ===== TESTS DE VALIDATION MERMAID =====


def test_mermaid_validator():
    """Teste le validateur Mermaid."""
    print("\n🧪 TESTS VALIDATEUR MERMAID")
    print("=" * 60)

    # Test 1: Code valide
    valid_code = """graph TD
    A[Début] --> B{Condition}
    B -->|Oui| C[Action 1]
    B -->|Non| D[Action 2]
    C --> E[Fin]
    D --> E"""

    is_valid, msg = MermaidValidator.validate(valid_code)
    print(f"✓ Test 1 - Code valide: {is_valid} {msg}")
    assert is_valid, "Code valide devrait passer"

    # Test 2: Code avec backticks
    invalid_code = """```
    graph TD
    A --> B
    ```"""

    is_valid, msg = MermaidValidator.validate(invalid_code)
    print(f"✓ Test 2 - Code avec backticks: {not is_valid} (attendu: invalid)")
    assert not is_valid, "Code avec backticks devrait échouer"

    # Test 3: Code vide
    is_valid, msg = MermaidValidator.validate("")
    print(f"✓ Test 3 - Code vide: {not is_valid} (attendu: invalid)")
    assert not is_valid, "Code vide devrait échouer"

    # Test 4: Nettoyage
    messy_code = "```graph TD\nA --> B```"
    cleaned = MermaidValidator.sanitize(messy_code)
    print(f"✓ Test 4 - Nettoyage: '{messy_code}' -> '{cleaned}'")
    assert "```" not in cleaned, "Les backticks devraient être supprimés"

    print("=" * 60)
    print("✅ Tous les tests Mermaid passent!\n")


# ===== TESTS DE GÉNÉRATION =====


async def test_generation_simple():
    """Test simple de génération (ne pas exécuter en prod)."""
    print("\n🧪 TEST GÉNÉRATION (EXEMPLE)")
    print("=" * 60)

    synthesis = CourseSynthesis(
        description="Les fractions: concepts de base et opérations",
        difficulty="Collège 5e",
        level_detail="standard",
    )

    print(f"Synthèse créée:")
    print(json.dumps(synthesis.model_dump(), indent=2, ensure_ascii=False))
    print("\nNote: Appel réel à Gemini (ne pas exécuter en test automatisé)")
    print("=" * 60 + "\n")


# ===== DOCUMENTATION =====


def print_architecture_doc():
    """Affiche la documentation de la nouvelle architecture."""
    doc = """
╔════════════════════════════════════════════════════════════════╗
║        🏗️  ARCHITECTURE REFACTORISÉE - DOCUMENTATION          ║
╚════════════════════════════════════════════════════════════════╝

📋 RÉSUMÉ DES CHANGEMENTS
─────────────────────────────────────────────────────────────────

1. AVANT (Architecture 2 LLM)
   ├─ LLM1: Génère plan + contenu
   ├─ LLM2 (par partie): Génère Mermaid
   └─ KROKI: Génère SVG/Base64
   Problèmes: 2N+1 appels LLM, latence, coûts, risque d'incohérence

2. APRÈS (Architecture unifiée)
   ├─ LLM1: Génère TOUT (contenu + Mermaid) en 1 appel
   ├─ Validator: Valide Mermaid avant Kroki
   ├─ KROKI (parallélisé): Génère tous les SVG
   └─ Retour JSON complet
   Bénéfices: 1 appel LLM, latence réduite, cohérence garantie

📁 FICHIERS CRÉÉS/MODIFIÉS
─────────────────────────────────────────────────────────────────

NOUVEAUX FICHIERS:
  ✓ src/utils/mermaid_validator.py
    - MermaidValidator: Valide syntaxe Mermaid
    - Nettoie et détecte erreurs avant Kroki
    - Limite à 50 nœuds max

  ✓ src/utils/cours_utils_v2.py
    - generate_complete_course(): LLM unique (contenu + Mermaid)
    - generate_all_schemas(): Parallélise génération Kroki
    - generate_schema_mermaid(): Kroki + base64

  ✓ src/tools/cours_tools/generate_cours_tool_v2.py
    - generate_courses(): Pipeline complet async
    - generate_courses_sync(): Wrapper ADK
    - Logging structuré

MODIFIÉS:
  ✓ src/models/cours_models.py
    - CoursePartWithMermaid: Nouvelle structure avec mermaid_syntax
    - CourseOutputWithMermaid: Sortie complète

  ✓ src/prompts/cours_prompt.py
    - SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE: Prompt unifié
    - Instructions strictes pour Mermaid valide

  ✓ src/prompts/__init__.py
    - Imports mis à jour

🔄 FLUX DE GÉNÉRATION
─────────────────────────────────────────────────────────────────

1. Entrée: CourseSynthesis
   ├─ description: str
   ├─ difficulty: str
   └─ level_detail: "flash" | "standard" | "detailed"

2. LLM (1 appel)
   Input: Description + Difficulté + Niveau
   Output: JSON avec:
   {
     "title": "Titre du cours",
     "parts": [
       {
         "title": "Partie 1",
         "content": "Contenu structuré",
         "schema_description": "Description du schéma",
         "mermaid_syntax": "graph TD\\nA-->B"  // Code Mermaid brut
       }
     ]
   }

3. Validation Mermaid
   ├─ Vérifie type valide (graph, sequence, class, etc.)
   ├─ Détecte backticks et commentaires
   ├─ Vérifie équilibre des accolades
   └─ Compte les nœuds (warn si > 50)

4. Génération parallèle Kroki
   ├─ Pour chaque partie:
   │  ├─ Envoie Mermaid à Kroki
   │  ├─ Récupère SVG
   │  └─ Encode en base64
   └─ Await asyncio.gather(*tasks)

5. Retour: JSON complet avec base64

⚡ POINTS D'OPTIMISATION
─────────────────────────────────────────────────────────────────

✓ 1 seul appel LLM (vs N+1 avant)
✓ Parallelisation Kroki avec asyncio
✓ Validation Mermaid avant envoi
✓ Cache possible des SVG via hash
✓ Gestion d'erreur granulaire
✓ Logging structuré pour debug

📊 COMPARAISON COÛTS/PERF
─────────────────────────────────────────────────────────────────

Cours avec 4 parties:

AVANT:
  - Appels LLM: 1 (planner) + 4 (mermaid) = 5 appels
  - Coût: 5 × coût_appel
  - Temps: Sequential (plus lent)

APRÈS:
  - Appels LLM: 1 (complet)
  - Coût: 1 × coût_appel = 80% de réduction!
  - Temps: Parallélisé (plus rapide)

🚀 UTILISATION
─────────────────────────────────────────────────────────────────

1. Via ADK Agent:
   from src.tools.cours_tools.generate_cours_tool_v2 import generate_courses_sync
   
   result = generate_courses_sync(synthesis)

2. Async (recommandé):
   from src.tools.cours_tools.generate_cours_tool_v2 import generate_courses
   
   result = await generate_courses(synthesis)

3. Validation Mermaid manuelle:
   from src.utils.mermaid_validator import MermaidValidator
   
   is_valid, msg = MermaidValidator.validate(code)
   cleaned = MermaidValidator.sanitize(code)

✅ BEST PRACTICES APPLIQUÉES
─────────────────────────────────────────────────────────────────

✓ Single Responsibility: Chaque fichier a 1 responsabilité
✓ Async/Await: Parallelisation avec asyncio
✓ Type Hints: Full typing pour IDE et type checking
✓ Logging: Structuré avec contexte
✓ Error Handling: Try/except granulaire + logs
✓ Validation: Pydantic + custom validator
✓ Timeout: Protection contre hang (10s pour Kroki)
✓ Cleanup: Nettoyage des fichiers temporaires
✓ Docstrings: Documentation complète (RST style)
✓ Constants: Pas de magic strings/numbers
✓ Testability: Code découplé et testable
✓ Performance: Minimize requests, maximize parallelism

⚠️  MIGRATION DE L'ANCIEN CODE
─────────────────────────────────────────────────────────────────

ANCIEN FICHIER à GARDER POUR COMPATIBILITÉ:
  - src/tools/cours_tools/generate_cours_tool.py
  - src/utils/cours_utils.py

Les fonctions deprecated() redirigent avec warnings vers v2.

NOUVEAU CODE À UTILISER:
  - src/tools/cours_tools/generate_cours_tool_v2.py  ✨ NEW
  - src/utils/cours_utils_v2.py                      ✨ NEW

ÉTAPES DE MIGRATION:
  1. Tests (valider output v2)
  2. Update agents (changer imports)
  3. Monitor (logs en prod)
  4. Archiver old (après 2 sprints)

🔗 INTÉGRATION ADK
─────────────────────────────────────────────────────────────────

from google.adk.agents import LlmAgent, tool
from src.tools.cours_tools.generate_cours_tool_v2 import generate_courses_sync

course_agent = LlmAgent(
    name="course_generator",
    description="Agent pour générer des cours avec schémas",
    model="gemini-2.5-flash",
    tools=[
        tool(
            generate_courses_sync,
            "generate_courses",
            "Génère un cours complet avec schémas"
        )
    ]
)

═══════════════════════════════════════════════════════════════════
"""
    print(doc)


if __name__ == "__main__":
    print_architecture_doc()
    test_mermaid_validator()
    # asyncio.run(test_generation_simple())  # À décommenter pour test
    print("\n✅ Documentation et tests terminés!")
