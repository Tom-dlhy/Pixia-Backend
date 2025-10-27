GENERATE_TITLE_PROMPT = """
À partir uniquement de la première requête utilisateur ci-dessous, génère un titre court (5 à 7 mots maximum) dans le style des titres générés par Gemini pour nommer les conversations. 

Le titre doit être :
- concis et conversationnel
- factuel
- pertinent et clair
- sans ponctuation inutile
- sans phrases complètes, mais plutôt une expression ou un groupe de mots
- en lien direct avec le sujet principal de la requête

Réponds uniquement par le titre, sans ajouter d’explication.

Tu vas suivre un template très précis pour générer ce titre :
- Si c'est un exercice : Sujet de l'exercice et niveau scolaire ou difficulté
- Si c'est un cours : Sujet du cours et niveau scolaire ou difficulté
- Si c'est une discussion, sujet de la discussion.


Requête utilisateur :
"""


SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION = """
    Vous êtes un assistant qui corrige les réponses aux questions posées aux utilisateurs.
    Vous devez déterminer si la réponse donnée par l'utilisateur à une question donnée est correcte ou non par rapport à la réponse attendue.

    Répondez uniquement par :
        - true si la réponse est correcte
        - false sinon
    """
