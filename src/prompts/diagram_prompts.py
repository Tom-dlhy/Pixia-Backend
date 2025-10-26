"""
Prompts spécialisés pour la génération de code de diagrammes syntaxiquement correct.
Un prompt expert par type pour maximiser la qualité et minimiser les erreurs.

Architecture:
- LLM #1 choisit le type optimal (5 types: Mermaid, PlantUML, GraphViz, C4, D2)
- LLM #2 (spécialisé) génère le code valide pour ce type
"""

# ============================================================================
# SÉLECTION DU TYPE DE DIAGRAMME (LLM #1)
# ============================================================================

PROMPT_SELECT_DIAGRAM_TYPE = """Vous êtes un expert en visualisation pédagogique.

Analysez le contenu pédagogique et sélectionnez LE TYPE DE DIAGRAMME LE PLUS PERTINENT parmi:

1. **Mermaid**: Pour algo, flowcharts, processus, état machines
   - Meilleur pour: étapes logiques, flux de décision, cycles

2. **PlantUML**: Pour UML, architecture, interactions entre objets
   - Meilleur pour: design patterns, hiérarchie de classes, relations

3. **GraphViz**: Pour graphes, dépendances, arbres, structures hiérarchiques
   - Meilleur pour: arbres binaires, graphes de dépendances, relations complexes

4. **C4**: Pour architecture système d'entreprise
   - Meilleur pour: microservices, architecture logicielle, système complexe

5. **D2**: Pour concepts abstraits modernes et intuitifs
   - Meilleur pour: frameworks, relations bidirectionnelles, concepts

**CONTENU À ANALYSER:**
Titre: {title}
Contenu: {content}

**RÉPONDEZ UNIQUEMENT EN JSON:**
{{
  "type": "<mermaid|plantuml|graphviz|c4|d2>",
  "reasoning": "1-2 phrases expliquant le choix"
}}
"""

# ============================================================================
# GÉNÉRATEURS SPÉCIALISÉS (LLM #2)
# ============================================================================

PROMPT_GENERATE_MERMAID = """Vous êtes expert Mermaid. Générez un diagramme Mermaid SYNTAXIQUEMENT CORRECT pour visualiser:

{content}

**RÈGLES STRICTES MERMAID:**
1. Commencer par: flowchart TD (ou graph TD)
2. Nœuds: [texte] ou {{texte}} ou ((texte))
3. Connecteurs: --> ou -->|label|
4. PAS de backticks ni ''' dans le code
5. PAS de guillemets autour des labels (sauf si nécessaire)
6. Pas de caractères spéciaux non échappés
7. Chaque lien doit lier deux nœuds existants
8. Nœuds avec espaces: utiliser des crochets [Mon Nœud]

**EXEMPLE VALIDE (copier ce style):**
```
flowchart TD
    A[Début]
    B{{Décision?}}
    C[Action 1]
    D[Action 2]
    E[Fin]
    
    A --> B
    B -->|Oui| C
    B -->|Non| D
    C --> E
    D --> E
```

**RETOURNEZ UNIQUEMENT LE CODE MERMAID (sans ``` , sans explications, directement du code exécutable):**
"""

PROMPT_GENERATE_PLANTUML = """Vous êtes expert PlantUML UML. Générez un diagramme PlantUML SYNTAXIQUEMENT CORRECT pour:

{content}

**RÈGLES STRICTES PlantUML:**
1. @startuml en début, @enduml en fin (OBLIGATOIRE)
2. Classes: class NomClasse {{ 
   - attribut : Type
   + methode(param) : ReturnType
}}
3. Relations: NomClasse1 --> NomClasse2 (héritage)
4. NomClasse1 "*" -- "1" NomClasse2 (composition)
5. interface IName {{ }}
6. Pas de backticks, pas d'apostrophes mal formées
7. Chaque accolade fermée

**EXEMPLE VALIDE:**
```
@startuml
class Animal {{
  - name : String
  + move()
}}
class Dog {{
  + bark()
}}
Animal <|-- Dog
@enduml
```

**RETOURNEZ UNIQUEMENT LE CODE COMPLET (entre @startuml et @enduml):**
"""

PROMPT_GENERATE_GRAPHVIZ = """Vous êtes expert GraphViz DOT. Générez un diagramme GraphViz SYNTAXIQUEMENT CORRECT pour:

{content}

**RÈGLES STRICTES GRAPHVIZ:**
1. Début: digraph G {{ ou graph G {{
2. Fin: }} (accolade fermée)
3. Nœuds: node_id [label="Texte du nœud"]
4. Connecteurs directed: node1 -> node2;
5. Connecteurs undirected: node1 -- node2;
6. Identifiants de nœuds: pas d'espaces (utiliser _ ou CamelCase)
7. Labels peuvent avoir des espaces: [label="Mon Label"]
8. TOUS les connecteurs doivent finir par ;

**EXEMPLE VALIDE:**
```
digraph G {{
  A [label="Racine"];
  B [label="Enfant 1"];
  C [label="Enfant 2"];
  A -> B;
  A -> C;
  B -> C;
}}
```

**RETOURNEZ UNIQUEMENT LE CODE VALIDE (digraph ... }}):**
"""

PROMPT_GENERATE_C4 = """Vous êtes expert C4 via PlantUML. Générez un diagramme C4 SYNTAXIQUEMENT CORRECT pour:

{content}

**RÈGLES STRICTES C4:**
1. @startuml en début, @enduml en fin
2. Include: !include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml
3. Persons: Person(id, "Name", "Description")
4. Systems: System(id, "Name", "Description")
5. Relations: Rel(source_id, target_id, "Label")
6. PAS de backticks, tout bien fermé

**EXEMPLE VALIDE:**
```
@startuml C4_Context
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml
Person(user, "User", "An end user")
System(sys, "System", "The main system")
Rel(user, sys, "Uses")
@enduml
```

**RETOURNEZ UNIQUEMENT LE CODE COMPLET:**
"""

PROMPT_GENERATE_D2 = """Vous êtes expert D2. Générez un diagramme D2 SYNTAXIQUEMENT CORRECT pour:

{content}

**RÈGLES STRICTES D2:**
1. Syntaxe: key: value ou key -> target
2. Relations: A -> B ou A <-> B
3. Groupes: container {{ key1; key2 }}
4. Labels texte: "Mon Label"
5. Pas de backticks, pas d'apostrophes mal fermées
6. Pas de caractères spéciaux non échappés

**EXEMPLE VALIDE:**
```
Client -> Server
Server -> Database
Database -> Server
Server -> Client
```

**RETOURNEZ UNIQUEMENT LE CODE D2 VALIDE:**
"""

# ============================================================================
# MAPPING PROMPT PAR TYPE
# ============================================================================

SPECIALIZED_PROMPTS = {
    "mermaid": PROMPT_GENERATE_MERMAID,
    "plantuml": PROMPT_GENERATE_PLANTUML,
    "graphviz": PROMPT_GENERATE_GRAPHVIZ,
    "c4": PROMPT_GENERATE_C4,
    "d2": PROMPT_GENERATE_D2,
}

# ============================================================================
# VALIDATEURS PAR TYPE
# ============================================================================

VALIDATORS = {
    "mermaid": {
        "start_keywords": ["flowchart", "graph"],
        "required_chars": ["-->", "[", "]"],
        "forbidden_chars": ["```"],
    },
    "plantuml": {
        "start_keywords": ["@startuml"],
        "end_keywords": ["@enduml"],
        "required_chars": ["@startuml", "@enduml"],
        "forbidden_chars": ["```"],
    },
    "graphviz": {
        "start_keywords": ["digraph", "graph"],
        "end_chars": "}",
        "required_chars": ["->", "{{", "}}"],
    },
    "c4": {
        "start_keywords": ["@startuml"],
        "end_keywords": ["@enduml"],
        "required_chars": ["@startuml", "@enduml"],
    },
    "d2": {
        "required_chars": ["->"],
        "forbidden_patterns": ["```"],
    },
}
