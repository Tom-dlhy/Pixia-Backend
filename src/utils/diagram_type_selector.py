from enum import Enum
from typing import Optional, Dict, Any
import logging
from src.config import gemini_settings
from google.genai import types

logger = logging.getLogger(__name__)


class DiagramType(str, Enum):
    """Types de diagrammes supportés par Kroki"""

    MERMAID = "mermaid"
    PLANTUML = "plantuml"
    C4 = "c4"  
    GRAPHVIZ = "graphviz"
    D2 = "d2"
    DITAA = "ditaa"

    def get_kroki_url(self) -> str:
        """Retourne l'URL Kroki pour ce type"""
        if self == DiagramType.C4:
            return "https://kroki.io/plantuml/svg"
        return f"https://kroki.io/{self.value}/svg"

    def get_mime_type(self) -> str:
        """Content-Type pour Kroki"""
        return "text/plain"


DIAGRAM_TYPE_SELECTOR_PROMPT = """Vous êtes un expert en diagrammes et visualisations pédagogiques.

Analysez le contenu du cours ci-dessous et sélectionnez le type de diagramme LE PLUS PERTINENT:

**Types disponibles:**
1. **Mermaid**: Pour flowcharts, diagrammes de sequence, état machines, mind maps
   - Utilisé pour: algorithmes, processus étape par étape, états, relations simples
   - Exemple: algorithme de tri, machine à états

2. **PlantUML**: Pour diagrammes UML complets (class, sequence, component, activity)
   - Utilisé pour: architecture logicielle, relations de classe, interactions d'objets
   - Exemple: design pattern, hiérarchie de classes

3. **C4**: Pour diagrammes d'architecture système (contexte, conteneurs, composants)
   - Utilisé pour: architecture logicielle d'entreprise, interactions système
   - Exemple: microservices, architecture cloud

4. **GraphViz**: Pour graphes dirigés et relations complexes
   - Utilisé pour: dépendances, arbres généalogiques, flux de données
   - Exemple: arbre binaire, graphe de dépendances

5. **D2**: Pour diagrammes modernes et intuitifs
   - Utilisé pour: concepts abstraits, relations bidirectionnelles
   - Exemple: frameworks, concepts abstraits

6. **Ditaa**: Pour diagrammes ASCII artistiques
   - Utilisé pour: schémas physiques, architectures, layouts
   - Exemple: architecture matérielle, layout de salle

**Contenu du cours:**
Titre: {title}
Description: {description}
Contenu: {content}

**Répondez UNIQUEMENT avec JSON:**
{{
  "diagram_type": "<mermaid|plantuml|c4|graphviz|d2|ditaa>",
  "reasoning": "Explication courte (1-2 phrases) du choix",
  "elements": ["élément 1", "élément 2", "..."],
  "recommended_title": "Titre court du diagramme"
}}
"""

DIAGRAM_CODE_GENERATOR_PROMPTS = {
    DiagramType.MERMAID: """Générez un diagramme Mermaid pour visualiser ce concept:

{content}

Retournez UNIQUEMENT le code Mermaid sans backticks, sans explications.
Assurez-vous que le code est valide et exécutable.""",
    DiagramType.PLANTUML: """Générez un diagramme PlantUML pour visualiser ce concept:

{content}

Retournez UNIQUEMENT le code PlantUML (commençant par @startuml, finissant par @enduml) sans backticks.""",
    DiagramType.C4: """Générez un diagramme C4 (avec PlantUML C4-PlantUML) pour visualiser ce concept:

{content}

Utilisez la syntaxe C4 de PlantUML. Retournez UNIQUEMENT le code (entre @startuml et @enduml).""",
    DiagramType.GRAPHVIZ: """Générez un diagramme GraphViz (DOT) pour visualiser ce concept:

{content}

Retournez UNIQUEMENT le code GraphViz (commençant par digraph ou graph) sans backticks.""",
    DiagramType.D2: """Générez un diagramme D2 pour visualiser ce concept:

{content}

Retournez UNIQUEMENT le code D2 sans backticks.""",
    DiagramType.DITAA: """Générez un diagramme DITAA (ASCII art) pour visualiser ce concept:

{content}

Retournez UNIQUEMENT le code DITAA valide.""",
}


class DiagramTypeSelector:
    """Sélecteur intelligent du type de diagramme via LLM"""

    @staticmethod
    def select_diagram_type(
        title: str, description: str, content: str
    ) -> Dict[str, Any]:
        """
        Demande à Gemini de choisir le type de diagramme le plus pertinent.

        Args:
            title: Titre de la partie du cours
            description: Description
            content: Contenu pédagogique

        Returns:
            Dict avec diagram_type, reasoning, elements, recommended_title
        """
        try:
            prompt = DIAGRAM_TYPE_SELECTOR_PROMPT.format(
                title=title,
                description=description,
                content=content[:500],  
            )

            logger.debug(f"[DIAGRAM-SELECT] Analyse du type optimal pour: {title[:40]}")

            response = gemini_settings.CLIENT.models.generate_content(
                model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )

            import json

            result = json.loads(response.text)
            diagram_type = DiagramType(result["diagram_type"])

            logger.info(
                f"[DIAGRAM-SELECT-SUCCESS] Type sélectionné: {diagram_type.value} pour '{title[:40]}'"
            )

            return {
                "diagram_type": diagram_type,
                "reasoning": result.get("reasoning", ""),
                "elements": result.get("elements", []),
                "recommended_title": result.get("recommended_title", title),
            }

        except Exception as e:
            logger.error(f"[DIAGRAM-SELECT-ERROR] Erreur sélection: {e}", exc_info=True)
            return {
                "diagram_type": DiagramType.MERMAID,
                "reasoning": "Type par défaut (erreur lors de la sélection)",
                "elements": [],
                "recommended_title": title,
            }

    @staticmethod
    def generate_diagram_code(diagram_type: DiagramType, content: str) -> Optional[str]:
        """
        Génère le code du diagramme selon son type.

        Args:
            diagram_type: Type de diagramme (DiagramType enum)
            content: Contenu pédagogique à visualiser

        Returns:
            str: Code du diagramme (Mermaid, PlantUML, GraphViz, etc.)
        """
        try:
            if diagram_type not in DIAGRAM_CODE_GENERATOR_PROMPTS:
                logger.error(
                    f"[DIAGRAM-CODEGEN-ERROR] Type non supporté: {diagram_type}"
                )
                return None

            prompt = DIAGRAM_CODE_GENERATOR_PROMPTS[diagram_type].format(
                content=content[:800]
            )

            logger.debug(f"[DIAGRAM-CODEGEN] Génération code {diagram_type.value}")

            response = gemini_settings.CLIENT.models.generate_content(
                model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
                contents=prompt,
            )

            code = response.text.strip()

            if code.startswith("```"):
                code = code.split("```", 2)[1]
                if code.startswith(diagram_type.value):
                    code = code[len(diagram_type.value) :].lstrip()

            logger.info(
                f"[DIAGRAM-CODEGEN-SUCCESS] {diagram_type.value}: {len(code)} chars"
            )
            return code

        except Exception as e:
            logger.error(
                f"[DIAGRAM-CODEGEN-ERROR] Erreur génération {diagram_type.value}: {e}"
            )
            return None

    @staticmethod
    def get_all_types() -> list:
        """Retourne tous les types disponibles"""
        return list(DiagramType)

    @staticmethod
    def get_diagram_info(diagram_type: DiagramType) -> Dict[str, str]:
        """Retourne des infos sur un type de diagramme"""
        info = {
            DiagramType.MERMAID: {
                "name": "Mermaid",
                "description": "Flowcharts, sequences, class diagrams, état machines",
                "use_cases": "Algorithmes, processus, workflows",
            },
            DiagramType.PLANTUML: {
                "name": "PlantUML",
                "description": "UML complet (class, sequence, activity, component)",
                "use_cases": "Design patterns, architecture logicielle, interactions d'objets",
            },
            DiagramType.C4: {
                "name": "C4",
                "description": "Diagrammes d'architecture système (contexte, conteneurs)",
                "use_cases": "Architecture d'entreprise, microservices, cloud",
            },
            DiagramType.GRAPHVIZ: {
                "name": "GraphViz",
                "description": "Graphes dirigés et relations complexes",
                "use_cases": "Arbres, dépendances, flux de données",
            },
            DiagramType.D2: {
                "name": "D2",
                "description": "Diagrammes modernes et intuitifs",
                "use_cases": "Concepts abstraits, frameworks",
            },
            DiagramType.DITAA: {
                "name": "DITAA",
                "description": "Diagrammes ASCII artistiques",
                "use_cases": "Architectures physiques, layouts, schémas",
            },
        }
        return info.get(diagram_type, {})
