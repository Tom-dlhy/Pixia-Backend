# 🚀 Recommandations d'Amélioration pour la Route `/chat`

## Vue d'Ensemble

La route `/chat` intègre **bien** la nouvelle stack Quad LLM, mais il y a 3 domaines d'amélioration pour une meilleure UX et robustesse:

1. **Timeout pour DeepCourse long**
2. **Feedback progressif à l'utilisateur**
3. **Gestion d'erreurs Quad LLM renforcée**

---

## 1. 🔴 URGENT: Timeout Configuration

### Problème

Pour un deepcourse avec 5 chapitres:
- Chaque chapitre = ~54s (3 générations parallèles × ~18s)open course_output.htmlopen course_output.html
- 5 chapitres exécutés séquentiellement = **~270 secondes (4.5 minutes)**
- FastAPI timeout par défaut = **60 secondes**
- **Résultat:** Erreur timeout avant la fin

### Solution Proposée

**Fichier:** `src/app/main.py`

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Configuration du timeout au niveau de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

# Dans le router /chat ou au niveau de l'app:
# Option 1: Augmenter le timeout global (non recommandé)
# Option 2: Utiliser un pattern Background Task (RECOMMANDÉ)
```

**Pattern Recommandé: Background Task avec Polling**

```python
# src/app/api/chat.py (modifications)

from fastapi import BackgroundTasks
from src.bdd import DBManager

# Dictionnaire en mémoire pour stocker l'état (ou utiliser Redis)
chat_tasks = {}  # {task_id: {"status": "processing", "result": None, "error": None}}

@router.post("/chat", response_model=ChatResponse)
async def chat(
    user_id: str = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    background_tasks: BackgroundTasks = None,
):
    """Traite un message utilisateur - version rapide."""
    
    task_id = str(uuid4())
    
    # Pour les cours normaux: exécuter en sync (rapide: ~54s)
    if "cours normal" in message.lower():
        # ... exécution rapide ...
        return ChatResponse(...)
    
    # Pour les deepcourse: exécuter en background (peut dépasser 60s)
    else:
        # Créer une task en background
        background_tasks.add_task(
            process_deepcourse_task,
            task_id=task_id,
            user_id=user_id,
            message=message,
            session_id=session_id
        )
        
        # Retourner immédiatement avec task_id
        return ChatResponse(
            session_id=session_id,
            answer="DeepCourse en préparation...",
            agent="deep-course",
            redirect_id=task_id  # ← Task ID pour polling
        )

@router.get("/chat/status/{task_id}")
async def get_chat_status(task_id: str):
    """Polling endpoint pour connaître l'état de la task."""
    
    if task_id not in chat_tasks:
        return {"error": "Task not found"}
    
    task = chat_tasks[task_id]
    
    return {
        "task_id": task_id,
        "status": task["status"],  # "processing" | "completed" | "error"
        "result": task.get("result"),  # DeepCourseOutput si completed
        "error": task.get("error"),
        "progress": task.get("progress", 0)  # 0-100%
    }

async def process_deepcourse_task(task_id: str, user_id: str, ...):
    """Exécute le deepcourse en background."""
    
    try:
        chat_tasks[task_id] = {
            "status": "processing",
            "result": None,
            "error": None,
            "progress": 0
        }
        
        # ... exécutation du deepcourse ...
        result = await generate_deepcourse(synthesis)
        
        # Stockage
        await bdd_manager.store_deepcourse(...)
        
        chat_tasks[task_id]["status"] = "completed"
        chat_tasks[task_id]["result"] = result
        chat_tasks[task_id]["progress"] = 100
        
    except Exception as e:
        chat_tasks[task_id]["status"] = "error"
        chat_tasks[task_id]["error"] = str(e)
        logger.exception("❌ DeepCourse background task failed")
```

### Avantage

✅ Pas de timeout
✅ UX progressive
✅ Peut exécuter plusieurs deepcourse en parallèle
✅ Client peut faire du polling ou WebSocket

---

## 2. 🟡 IMPORTANT: Feedback Progressif

### Problème

L'utilisateur attend 54s+ sans savoir ce qui se passe

### Solution Proposée

**Utiliser des Server-Sent Events (SSE) ou WebSocket**

```python
# src/app/api/chat.py (avec SSE)

from fastapi.responses import StreamingResponse
import asyncio

@router.post("/chat/stream")
async def chat_stream(
    user_id: str = Form(...),
    message: str = Form(...),
    # ... autres paramètres
):
    """Version streaming avec feedback progressif."""
    
    async def event_generator():
        
        try:
            # Étape 1: Session creation
            yield f"data: {{'status': 'creating_session'}}\n\n"
            session = await inmemory_service.create_session(...)
            session_id = session.id
            
            # Étape 2: ADK Runner
            yield f"data: {{'status': 'analyzing_request'}}\n\n"
            runner = Runner(agent=root_agent, ...)
            
            # Étape 3: Exécution du runner
            step = 0
            async for event in runner.run_async(...):
                step += 1
                
                if event.is_final_response():
                    yield f"data: {{'status': 'generating_response'}}\n\n"
                
                elif hasattr(event, "get_function_responses"):
                    func_responses = event.get_function_responses()
                    for fr in func_responses:
                        
                        if fr.name == "generate_courses":
                            yield f"data: {{'status': 'generating_courses', 'progress': 20}}\n\n"
                            
                        elif fr.name == "generate_deepcourse":
                            yield f"data: {{'status': 'generating_deepcourse', 'progress': 10}}\n\n"
                            # Pour chaque chapitre:
                            for ch_num in range(1, num_chapters + 1):
                                progress = 10 + (ch_num / num_chapters) * 80
                                yield f"data: {{'status': 'generating_chapter', 'chapter': {ch_num}, 'progress': {progress}}}\n\n"
                                await asyncio.sleep(0.1)
            
            # Étape 4: Success
            yield f"data: {{'status': 'completed', 'progress': 100}}\n\n"
            
        except Exception as e:
            yield f"data: {{'status': 'error', 'message': '{str(e)}'}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

**Côté Client (JavaScript):**

```javascript
const eventSource = new EventSource('/chat/stream?user_id=user123&message=...');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.status) {
        case 'creating_session':
            console.log('📝 Création de session...');
            break;
        case 'analyzing_request':
            console.log('🔍 Analyse de la demande...');
            break;
        case 'generating_courses':
            console.log('📚 Génération du cours...');
            updateProgressBar(data.progress);
            break;
        case 'generating_chapter':
            console.log(`📖 Chapitre ${data.chapter}/${totalChapters}...`);
            updateProgressBar(data.progress);
            break;
        case 'completed':
            console.log('✅ Généré avec succès!');
            break;
        case 'error':
            console.error('❌ Erreur:', data.message);
            break;
    }
};
```

### Avantage

✅ UX améliorée (utilisateur voit la progression)
✅ Pas de sensation d'attente bloquée
✅ Peut annuler la requête si souhaité
✅ Compatible avec tous les clients

---

## 3. 🟡 IMPORTANT: Gestion d'Erreurs Quad LLM Renforcée

### Problème

Si un chapitre de deepcourse échoue, **tout le deepcourse échoue**

Exemple:
```
Ch1: ✅ Succès
Ch2: ❌ Erreur Quad LLM
Ch3: ❌ Annulée (par asyncio.gather)
```

### Solution Proposée

**Ajouter des retries et fallbacks**

```python
# src/tools/deepcourse_tools/generate_deep_course_tool.py

import asyncio
from typing import Union, Optional

async def generate_deepcourse_with_retry(
    synthesis: DeepCourseSynthesis,
    max_retries: int = 3,
    allow_partial: bool = True
) -> DeepCourseOutput:
    """Génère un deepcourse avec retry et fallback partiel."""
    
    synthesis_chapters = synthesis.synthesis_chapters
    chapters = []
    failed_chapters = []
    
    async def process_chapter_with_retry(chapter: ChapterSynthesis, ch_num: int):
        """Traite un chapitre avec retry."""
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Ch{ch_num} - Tentative {attempt + 1}/{max_retries}")
                
                # Exécuter les 3 générations en parallèle
                exercise, course, evaluation = await asyncio.gather(
                    generate_exercises(chapter.synthesis_exercise),
                    generate_courses(chapter.synthesis_course),      # ← Peut échouer
                    generate_exercises(chapter.synthesis_evaluation)
                )
                
                # Si success, retourner
                return (ch_num, Chapter(
                    id_chapter=str(uuid4()),
                    title=chapter.chapter_title,
                    course=course,
                    exercice=exercise,
                    evaluation=evaluation
                ))
                
            except Exception as e:
                logger.warning(f"Ch{ch_num} - Tentative {attempt + 1} échouée: {e}")
                
                if attempt == max_retries - 1:
                    # Dernière tentative
                    if allow_partial:
                        logger.error(f"Ch{ch_num} - Génération PARTIELLE en fallback")
                        
                        # Créer un CourseOutput minimal/générique
                        fallback_course = create_fallback_course(
                            title=chapter.chapter_title,
                            description=chapter.chapter_description
                        )
                        
                        return (ch_num, Chapter(
                            id_chapter=str(uuid4()),
                            title=chapter.chapter_title,
                            course=fallback_course,
                            exercice=await generate_exercises(chapter.synthesis_exercise),
                            evaluation=await generate_exercises(chapter.synthesis_evaluation)
                        ))
                    else:
                        raise
                
                # Attendre avant retry
                await asyncio.sleep(2 ** attempt)
    
    # Exécuter tous les chapitres en parallèle
    results = await asyncio.gather(
        *[process_chapter_with_retry(ch, i) for i, ch in enumerate(synthesis_chapters, 1)],
        return_exceptions=True
    )
    
    # Traiter les résultats
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"❌ Chapitre généré avec erreur: {result}")
            if not allow_partial:
                raise result
        else:
            ch_num, chapter = result
            chapters.append(chapter)
    
    if not chapters and not allow_partial:
        raise RuntimeError("Aucun chapitre n'a pu être généré")
    
    # Créer le DeepCourseOutput
    return DeepCourseOutput(
        id=str(uuid4()),
        title=synthesis.title,
        chapters=chapters
    )

def create_fallback_course(title: str, description: str) -> CourseOutput:
    """Crée un CourseOutput minimal en cas d'échec."""
    
    return CourseOutput(
        id=str(uuid4()),
        title=title,
        parts=[
            Part(
                id_part=str(uuid4()),
                id_schema=str(uuid4()),
                title="Contenu temporaire",
                content=f"## {title}\n\n{description}\n\n*Note: Contenu généré en mode fallback*",
                schema_description=description,
                diagram_type="mermaid",
                diagram_code="graph LR\n    A[Sujet: " + title + "] --> B[À développer]",
                img_base64=None  # Pas de SVG en fallback
            )
        ]
    )
```

**Utilisation dans chat.py:**

```python
# Dans la route /chat
if tool_name == "generate_deepcourse":
    logger.info("✅ Tool 'generate_deepcourse' détecté")
    
    try:
        # Appeler avec allow_partial=True pour fallback
        result = await generate_deepcourse_with_retry(
            synthesis=synthesis,
            max_retries=3,
            allow_partial=True  # ← Fallback partiel autorisé
        )
        validated = _validate_deepcourse_output(result)
        
        if isinstance(final_response, DeepCourseOutput):
            # ... stockage ...
            
            # Alerter l'utilisateur si fallback
            if has_fallback_chapters(final_response):
                logger.warning(f"⚠️ DeepCourse avec chapitres en fallback")
                # Ajouter un flag dans la réponse?
                
    except Exception as e:
        logger.exception("❌ Erreur DeepCourse même avec fallback")
        raise
```

### Avantage

✅ Résilience accrue
✅ Ne pas perdre les chapitres réussis
✅ Fallback gracieux en cas d'erreur
✅ Meilleure UX (quelque chose plutôt que rien)

---

## 📋 Checklist d'Implémentation

### Priorité 1: Timeout Configuration

- [ ] Implémenter le pattern Background Task avec polling
- [ ] Créer l'endpoint `/chat/status/{task_id}`
- [ ] Tester avec deepcourse 5+ chapitres
- [ ] Documenter le comportement asynchrone

### Priorité 2: Feedback Progressif

- [ ] Implémenter l'endpoint `/chat/stream` (SSE)
- [ ] Ajouter des logs détaillés avec étapes
- [ ] Créer un client JavaScript de test
- [ ] Tester la UX avec vraies données

### Priorité 3: Gestion d'Erreurs Quad LLM

- [ ] Implémenter `generate_deepcourse_with_retry()`
- [ ] Ajouter la fonction `create_fallback_course()`
- [ ] Tester les scénarios d'erreur
- [ ] Ajouter des métriques d'erreur/fallback

---

## 🎯 Ordre de Priorité Recommandé

1. **URGENT (Sprint 1):** Timeout + Background Tasks
   - Impact: Évite les erreurs 503
   - Effort: Moyen (4-6h)
   - Risque: Faible

2. **Important (Sprint 2):** Feedback Progressif
   - Impact: Meilleure UX
   - Effort: Moyen (6-8h)
   - Risque: Faible

3. **Important (Sprint 2/3):** Retry + Fallback
   - Impact: Résilience
   - Effort: Moyen (4-6h)
   - Risque: Faible (dégradé gracieux)

---

## 📊 Impact Estimation

| Amélioratio | Timeout | Status | Ligne | Impact UX | Effort |
|-------------|---------|--------|-------|-----------|--------|
| Timeout Config | 🔴 URGENT | Background | ~50 | Critique | M |
| SSE Feedback | 🟡 Moyen | Stream | ~100 | Important | M |
| Retry+Fallback | 🟡 Moyen | Resilient | ~80 | Bonus | M |
| **Total** | | | ~230 | **Haute** | **6h** |

---

## ✅ Conclusion

La nouvelle stack Quad LLM **s'intègre bien** avec la route `/chat`, mais ces 3 améliorations rendront le système **production-ready** et **user-friendly**.

**Recommandation:** Implémenter dans cet ordre:
1. Timeout Configuration (critique)
2. Feedback Progressif (importante)
3. Retry + Fallback (résilience)
