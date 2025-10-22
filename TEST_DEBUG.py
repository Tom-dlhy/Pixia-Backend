#!/usr/bin/env python3
"""
TESTS SIMPLIFÉS - Debug du hang
Ne teste que LLM (pas Kroki) pour identifier le problème
"""

import asyncio
import logging
import sys
from src.models.cours_models import CourseSynthesis
from src.utils.cours_utils_v2 import generate_complete_course, generate_all_schemas

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)-8s] %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def test_1_simple_synthesis():
    """Test 1: Créer une synthèse simple"""
    print("\n" + "=" * 80)
    print("TEST 1: Création CourseSynthesis")
    print("=" * 80)

    try:
        synthesis = CourseSynthesis(
            description="Les variables en Python",
            difficulty="Débutant",
            level_detail="flash",
        )
        print(f"✅ Synthèse créée: {synthesis.description}")
        return synthesis
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


def test_2_llm_only(synthesis):
    """Test 2: Appeler LLM SEUL (pas Kroki)"""
    print("\n" + "=" * 80)
    print("TEST 2: Appel LLM seul (generate_complete_course)")
    print("=" * 80)

    try:
        print("[INFO] Appel LLM... (peut prendre 10-30s)")
        result = generate_complete_course(synthesis)

        if result:
            print(f"✅ LLM répondu!")
            print(f"   Titre: {result.title}")
            print(f"   Parties: {len(result.parts)}")
            for i, part in enumerate(result.parts, 1):
                print(f"      {i}. {part.title[:50]}")
                print(
                    f"         Mermaid: {part.mermaid_syntax[:60] if part.mermaid_syntax else 'None'}..."
                )
            return result
        else:
            print(f"❌ LLM n'a pas retourné de résultat")
            return None
    except Exception as e:
        print(f"❌ Erreur LLM: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_3_async_wrapper(synthesis):
    """Test 3: Version ASYNC du LLM"""
    print("\n" + "=" * 80)
    print("TEST 3: LLM via async (asyncio.to_thread)")
    print("=" * 80)

    try:
        print("[INFO] Appel async LLM...")
        result = await asyncio.to_thread(generate_complete_course, synthesis)

        if result:
            print(f"✅ Async LLM répondu!")
            print(f"   Titre: {result.title}")
            print(f"   Parties: {len(result.parts)}")
            return result
        else:
            print(f"❌ Async LLM n'a pas retourné de résultat")
            return None
    except Exception as e:
        print(f"❌ Erreur async LLM: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_4_three_courses_async():
    """Test 4: Générer 3 cours en parallèle"""
    print("\n" + "=" * 80)
    print("TEST 4: 3 cours en parallèle (ASYNC)")
    print("=" * 80)

    syntheses = [
        CourseSynthesis(
            description="Les variables en Python",
            difficulty="Débutant",
            level_detail="flash",
        ),
        CourseSynthesis(
            description="Les boucles for et while",
            difficulty="Débutant",
            level_detail="flash",
        ),
        CourseSynthesis(
            description="Les fonctions Python",
            difficulty="Intermédiaire",
            level_detail="flash",
        ),
    ]

    try:
        print(f"[INFO] Lancement 3 appels LLM en parallèle...")

        tasks = [asyncio.to_thread(generate_complete_course, s) for s in syntheses]

        print(f"[INFO] Attente des résultats (gather)...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        print(f"\n✅ Résultats reçus:")
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                print(f"   {i}. ❌ Erreur: {result}")
            elif result:
                print(f"   {i}. ✅ {result.title} ({len(result.parts)} parties)")
            else:
                print(f"   {i}. ❌ Aucun résultat")

        # AFFICHE LES DÉTAILS COMPLETS
        print("\n" + "=" * 80)
        print("DÉTAILS COMPLETS DES COURS GÉNÉRÉS")
        print("=" * 80)
        for i, result in enumerate(results, 1):
            if result and not isinstance(result, Exception):
                print(f"\n📚 COURS {i}: {result.title}")
                print(f"   ID: {result.id}")
                for j, part in enumerate(result.parts, 1):
                    print(f"\n   PARTIE {j}: {part.title}")
                    print(f"   {'─' * 76}")
                    print(f"   Contenu ({len(part.content)} chars):")
                    print(f"   {part.content[:200]}...")
                    print(
                        f"\n   Mermaid code ({len(part.mermaid_syntax or '')} chars):"
                    )
                    print(f"   {(part.mermaid_syntax or 'N/A')[:200]}...")

        return results

    except Exception as e:
        print(f"❌ Erreur parallélisation: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_5_with_kroki(synthesis):
    """Test 5: Générer avec Kroki (schémas SVG en base64)"""
    print("\n" + "=" * 80)
    print("TEST 5: Génération complète avec Kroki")
    print("=" * 80)

    try:
        print("[INFO] Étape 1: LLM...")
        course = await asyncio.to_thread(generate_complete_course, synthesis)

        if not course:
            print("❌ LLM échoué")
            return None

        print(f"✅ LLM OK: {len(course.parts)} parties avec Mermaid")

        print("[INFO] Étape 2: Kroki parallelisé...")
        course = await generate_all_schemas(course)

        print(f"✅ Kroki OK")

        # Affiche les résultats avec base64
        print("\n" + "=" * 80)
        print("RÉSULTATS AVEC SCHÉMAS")
        print("=" * 80)

        for i, part in enumerate(course.parts, 1):
            print(f"\n📊 PARTIE {i}: {part.title}")
            print(f"   ID Schéma: {part.id_schema}")
            print(f"   Mermaid code length: {len(part.mermaid_syntax or '')} chars")

            # Sauvegarder le SVG localement
            if part.mermaid_syntax:
                filename = f"test_schema_{i}.txt"
                with open(filename, "w") as f:
                    f.write(part.mermaid_syntax)
                print(f"   ✅ Mermaid sauvegardé: {filename}")

        return course

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """Lance les tests"""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " TESTS SIMPLIFÉS - Debug du hang ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    # Test 1
    synthesis = test_1_simple_synthesis()
    if not synthesis:
        return

    # Test 2
    result = test_2_llm_only(synthesis)
    if not result:
        return

    # Test 3 & 4
    print("\n" + "=" * 80)
    print("TESTS ASYNC")
    print("=" * 80)

    asyncio.run(test_3_async_wrapper(synthesis))
    asyncio.run(test_4_three_courses_async())

    # Test 5: Avec Kroki
    asyncio.run(test_5_with_kroki(synthesis))

    print("\n" + "=" * 80)
    print("✅ TESTS TERMINÉS")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
