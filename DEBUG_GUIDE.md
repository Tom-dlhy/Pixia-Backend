# 🐛 DEBUG - Hang et Performance

## 🆘 Problème identifié

Le hang "interminable" était probablement dû à :

1. **LLM timeout invisible** - Gemini API peut prendre 20-30s sans feedback
2. **Pas de logging** - Impossible de voir où ça pend
3. **asyncio.to_thread sur subprocess** - Peut causer des problèmes

## ✅ Solutions appliquées

### 1. Logging massif ajouté

Tous les appels importants ont du logging DEBUG avec préfixes clairs:

```python
[LLM-START]       Début d'une opération LLM
[LLM-REQUEST]     Envoi requête à Gemini
[LLM-RESPONSE]    Réponse reçue
[LLM-SUCCESS]     Opération réussie

[KROKI-START]     Début appel Kroki
[KROKI-EXECUTE]   Exécution curl
[KROKI-TIMEOUT]   Timeout (10s)
[KROKI-SUCCESS]   Schéma généré

[ASYNC-START]     Début parallelisation
[ASYNC-GATHER]    Attente gather()
[ASYNC-SUCCESS-N] Schéma N généré
```

### 2. Timeouts explicites

- **Kroki**: 10s timeout (subprocess)
- **LLM**: Dépend de Gemini (pas controllable)

### 3. Structure de debug améliorée

```python
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)-8s] %(message)s',
    stream=sys.stdout  # Force flush immédiat
)
```

## 🧪 Comment tester

### Option 1: Tests simples (RECOMMANDÉ - rapide)

```bash
# Lance les 4 tests de debug
python3 TEST_DEBUG.py
```

Cela teste:
1. Création CourseSynthesis ✅ (immédiat)
2. LLM seul (10-30s) - peut être long
3. LLM async (même temps)
4. **3 LLM en parallèle** (gain de ~60%)

### Option 2: Exemples complets (avec Kroki)

```bash
python3 EXAMPLES_USAGE.py
```

Décommentez les exemples async pour tester.

### Option 3: Tests avec timeout

```bash
# Timeout après 60s
timeout 60 python3 TEST_DEBUG.py
```

## 📊 Temps attendus

Pour un cours "flash" (1-2 parties):

| Étape | Temps |
|-------|-------|
| LLM   | 15-30s |
| Kroki (1 schéma) | 2-5s |
| Kroki (parallelisé 2) | 3-5s (gain!) |

**Total pour 1 cours**: ~20-35s  
**Total pour 3 cours (parallèle)**: ~25-40s (au lieu de 60-105s!)

## 🔍 Logs clés à surveiller

### ✅ Bon flux

```
[INFO] [MAIN] ⏳ ÉTAPE 1/2: Génération contenu + Mermaid (1 appel LLM)...
[DEBUG] [LLM-REQUEST] Envoi requête à Gemini avec timeout...
[DEBUG] [LLM-RESPONSE] Réponse reçue, parsing...
[INFO] [LLM-SUCCESS] Cours généré: 2 parties (Mermaid: 2)
[INFO] [MAIN] ⏳ ÉTAPE 2/2: Génération parallèle schémas Mermaid via Kroki...
[DEBUG] [ASYNC-GATHER] Attente de 2 tâches en parallèle...
[INFO] [KROKI-SUCCESS] Schéma généré: abc123 (15000 chars base64)
[INFO] [MAIN] ✅✅✅ GÉNÉRATION COMPLÉTÉE
```

### ⚠️  Problèmes à détecter

```
[ERROR] [LLM-GEMINI-ERROR] Erreur Gemini API: timeout
        ↑ LLM a timeout (probablement quota dépassé)

[ERROR] [KROKI-TIMEOUT] Timeout (10s) lors de l'appel à Kroki
        ↑ Kroki a échoué (diagramme trop complexe?)

[ERROR] [KROKI-ERROR] Kroki error (exit 1): ...
        ↑ Code Mermaid invalide
```

## 💡 Si c'est toujours lent

### 1. Vérifier les quotas Gemini

```bash
# Logs Gemini Cloud
gcloud logging read "resource.type=api" --format=json
```

### 2. Tester Kroki directement

```bash
# Test Kroki manuellement
echo "graph TD\nA[Test]" | curl -X POST -H "Content-Type: text/plain" \
  "https://kroki.io/mermaid/svg" --data-binary "@-"
```

### 3. Vérifier le réseau

```bash
# Ping Kroki
curl -I https://kroki.io
```

## 🚀 Optimisations futures

- [ ] Cache Kroki (par hash MD5)
- [ ] Pool de connexions Gemini
- [ ] Batch Kroki (requête groupée)
- [ ] Local Mermaid rendering (pas Kroki cloud)

## ✅ Checklist debug

- [x] Logging massif ajouté (DEBUG level)
- [x] Timeouts explicites (10s Kroki)
- [x] asyncio.gather() pour parallelisation
- [x] TEST_DEBUG.py pour tests isolés
- [x] Flush stdout immédiat (stream=sys.stdout)
- [ ] Tester avec vraie API Gemini
- [ ] Monitorer quotas
- [ ] Vérifier latence réseau Kroki

## 📞 Support

Rapportez les logs complets si hang:
```bash
python3 TEST_DEBUG.py 2>&1 | tee debug.log
```

Attachez `debug.log` avec timestamps!
