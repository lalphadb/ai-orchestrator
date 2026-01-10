# Outils (Tools)

Documentation complète des 18 outils intégrés dans AI Orchestrator v6.2.1.

---

## Vue d'ensemble

Le système d'outils permet à l'IA d'interagir avec le système d'exploitation et d'effectuer des actions concrètes. Chaque outil est une fonction Python async qui peut être appelée par le moteur ReAct.

### Catégories

| Catégorie | Outils | Description |
|-----------|--------|-------------|
| **system** | 3 | Commandes système, infos et LLMs |
| **filesystem** | 5 | Manipulation de fichiers et recherche |
| **utility** | 2 | Date/heure et calculs |
| **network** | 1 | Requêtes HTTP |
| **qa** | 7 | Outils d'assurance qualité |

---

## Outils Système

### `execute_command`

Exécute une commande shell sur le système.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | system |
| **Risque** | ⚠️ Élevé |
| **Timeout** | 30 secondes |

**Paramètres:**

| Nom | Type | Requis | Défaut | Description |
|-----|------|--------|--------|-------------|
| `command` | string | ✅ | - | Commande shell à exécuter |
| `timeout` | int | ❌ | 30 | Timeout en secondes |

**Retour:**
```json
{
  "stdout": "Sortie standard",
  "stderr": "Sortie d'erreur",
  "returncode": 0
}
```

**Exemples d'utilisation:**

```json
// Lister les fichiers
{"tool": "execute_command", "params": {"command": "ls -la /home"}}

// Vérifier l'espace disque
{"tool": "execute_command", "params": {"command": "df -h"}}

// Processus en cours
{"tool": "execute_command", "params": {"command": "ps aux | head -20"}}

// Avec timeout personnalisé
{"tool": "execute_command", "params": {"command": "apt update", "timeout": 60}}
```

**⚠️ Sécurité:**
- Les commandes sont exécutées avec les permissions de l'utilisateur `lalpha`
- Éviter les commandes destructives (`rm -rf`, etc.)
- Le timeout empêche les commandes infinies

---

### `get_system_info`

Récupère les informations système (CPU, RAM, disque).

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | system |
| **Risque** | 🟢 Faible |
| **Timeout** | 5 secondes |

**Paramètres:** Aucun

**Retour:**
```json
{
  "hostname": "lalpha-server-1",
  "os": "Ubuntu 25.10",
  "kernel": "6.17.0-8-generic",
  "cpu": {
    "model": "AMD Ryzen 9 7900X",
    "cores": 24,
    "usage_percent": 15.2
  },
  "memory": {
    "total_gb": 64.0,
    "used_gb": 23.5,
    "percent": 36.7
  },
  "disk": {
    "total_gb": 2000,
    "used_gb": 244,
    "percent": 12.2
  },
  "uptime": "5 days, 3:42:00"
}
```

**Exemple:**
```json
{"tool": "get_system_info", "params": {}}
```

---

### `list_llm_models`

Liste les modèles LLM disponibles via Ollama avec catégorisation automatique.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | system |
| **Risque** | 🟢 Faible |
| **Timeout** | 10 secondes |

**Paramètres:** Aucun

**Retour:**
```json
{
  "total": 30,
  "local_count": 25,
  "cloud_count": 5,
  "total_size_gb": 150.5,
  "categories": {
    "general": [{"name": "llama3.2:3b", "size": 2000000000, "available": true}],
    "code": [{"name": "deepseek-coder:33b", "size": 18000000000, "available": true}],
    "vision": [{"name": "llava:7b", "size": 4000000000, "available": true}],
    "embedding": [{"name": "nomic-embed-text", "size": 300000000, "available": true}],
    "safety": [{"name": "llama-guard-3:1b", "size": 1000000000, "available": true}],
    "cloud": [{"name": "kimi-k2:1t-cloud", "size": 100, "available": true}]
  },
  "models": [...]
}
```

**Catégorisation automatique:**
- **general**: Modèles polyvalents (llama, qwen, etc.)
- **code**: Spécialisés programmation (coder, deepseek)
- **vision**: Multimodal/images (vision, -vl, vl:)
- **embedding**: Vectorisation (embed, nomic, bge, mxbai)
- **safety**: Modération (safeguard, guard)
- **cloud**: Proxies cloud (size < 1000, gemini, kimi)

**Exemple:**
```json
{"tool": "list_llm_models", "params": {}}
```

---

## Outils Fichiers

### `read_file`

Lit le contenu d'un fichier.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | files |
| **Risque** | 🟡 Moyen |
| **Limite** | 100 KB |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `path` | string | ✅ | Chemin absolu du fichier |

**Retour:**
```json
{
  "content": "Contenu du fichier...",
  "size_bytes": 1234,
  "encoding": "utf-8"
}
```

**Exemples:**
```json
// Lire un fichier de config
{"tool": "read_file", "params": {"path": "/etc/hostname"}}

// Lire du code
{"tool": "read_file", "params": {"path": "/home/lalpha/script.py"}}
```

**Restrictions:**
- Fichiers binaires non supportés
- Limite de 100 KB
- Accès selon permissions utilisateur

---

### `write_file`

Écrit du contenu dans un fichier.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | files |
| **Risque** | ⚠️ Élevé |
| **Mode** | Création/Écrasement |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `path` | string | ✅ | Chemin absolu du fichier |
| `content` | string | ✅ | Contenu à écrire |
| `append` | bool | ❌ | Ajouter à la fin (défaut: false) |

**Retour:**
```json
{
  "success": true,
  "path": "/home/lalpha/test.txt",
  "bytes_written": 42
}
```

**Exemples:**
```json
// Créer un fichier
{"tool": "write_file", "params": {
  "path": "/home/lalpha/notes.txt",
  "content": "Mes notes importantes"
}}

// Ajouter à un fichier existant
{"tool": "write_file", "params": {
  "path": "/home/lalpha/log.txt",
  "content": "\n2026-01-08: Nouvelle entrée",
  "append": true
}}
```

---

### `list_directory`

Liste le contenu d'un répertoire.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | files |
| **Risque** | 🟢 Faible |

**Paramètres:**

| Nom | Type | Requis | Défaut | Description |
|-----|------|--------|--------|-------------|
| `path` | string | ✅ | - | Chemin du répertoire |
| `recursive` | bool | ❌ | false | Inclure sous-dossiers |
| `max_depth` | int | ❌ | 2 | Profondeur max (si recursive) |

**Retour:**
```json
{
  "path": "/home/lalpha",
  "entries": [
    {"name": "projets", "type": "directory", "size": 4096},
    {"name": "script.py", "type": "file", "size": 1234},
    {"name": ".bashrc", "type": "file", "size": 567, "hidden": true}
  ],
  "total_files": 2,
  "total_dirs": 1
}
```

**Exemples:**
```json
// Liste simple
{"tool": "list_directory", "params": {"path": "/home/lalpha"}}

// Liste récursive
{"tool": "list_directory", "params": {
  "path": "/home/lalpha/projets",
  "recursive": true,
  "max_depth": 3
}}
```

---

### `search_files`

Recherche des fichiers par nom ou contenu.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | files |
| **Risque** | 🟡 Moyen |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `directory` | string | ✅ | Répertoire de recherche |
| `pattern` | string | ✅ | Pattern de recherche (glob ou regex) |
| `content` | string | ❌ | Recherche dans le contenu |
| `max_results` | int | ❌ | Limite de résultats (défaut: 50) |

**Retour:**
```json
{
  "matches": [
    {
      "path": "/home/lalpha/projets/script.py",
      "type": "file",
      "size": 1234,
      "match_type": "name"
    }
  ],
  "total_matches": 1,
  "searched_files": 150
}
```

**Exemples:**
```json
// Par nom (glob)
{"tool": "search_files", "params": {
  "directory": "/home/lalpha",
  "pattern": "*.py"
}}

// Par contenu
{"tool": "search_files", "params": {
  "directory": "/home/lalpha/projets",
  "pattern": "*.py",
  "content": "def main"
}}
```

---

## Outils Utilitaires

### `get_datetime`

Retourne la date et l'heure actuelles.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | utility |
| **Risque** | 🟢 Faible |

**Paramètres:**

| Nom | Type | Requis | Défaut | Description |
|-----|------|--------|--------|-------------|
| `timezone` | string | ❌ | local | Fuseau horaire |
| `format` | string | ❌ | iso | Format de sortie |

**Retour:**
```json
{
  "datetime": "2026-01-08T14:30:00",
  "date": "2026-01-08",
  "time": "14:30:00",
  "timezone": "America/Montreal",
  "timestamp": 1736359800,
  "day_of_week": "Wednesday"
}
```

**Exemples:**
```json
// Heure locale
{"tool": "get_datetime", "params": {}}

// Avec timezone
{"tool": "get_datetime", "params": {"timezone": "UTC"}}

// Format personnalisé
{"tool": "get_datetime", "params": {"format": "human"}}
```

---

### `calculate`

Effectue des calculs mathématiques.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | utility |
| **Risque** | 🟢 Faible |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `expression` | string | ✅ | Expression mathématique |

**Retour:**
```json
{
  "expression": "2 + 2 * 3",
  "result": 8,
  "type": "int"
}
```

**Opérations supportées:**
- Arithmétique: `+`, `-`, `*`, `/`, `//`, `%`, `**`
- Fonctions: `sqrt`, `sin`, `cos`, `tan`, `log`, `exp`, `abs`, `round`
- Constantes: `pi`, `e`

**Exemples:**
```json
// Simple
{"tool": "calculate", "params": {"expression": "15 * 7"}}

// Avec fonctions
{"tool": "calculate", "params": {"expression": "sqrt(144) + pi"}}

// Pourcentages
{"tool": "calculate", "params": {"expression": "1500 * 0.15"}}
```

**⚠️ Sécurité:** Seules les expressions mathématiques sont autorisées (pas d'eval Python).

---

## Outils Réseau

### `http_request`

Effectue des requêtes HTTP.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | network |
| **Risque** | 🟡 Moyen |
| **Timeout** | 30 secondes |

**Paramètres:**

| Nom | Type | Requis | Défaut | Description |
|-----|------|--------|--------|-------------|
| `url` | string | ✅ | - | URL de la requête |
| `method` | string | ❌ | GET | Méthode HTTP |
| `headers` | object | ❌ | {} | Headers HTTP |
| `body` | string | ❌ | null | Corps de la requête |
| `timeout` | int | ❌ | 30 | Timeout en secondes |

**Retour:**
```json
{
  "status_code": 200,
  "headers": {
    "content-type": "application/json"
  },
  "body": "{\"result\": \"success\"}",
  "elapsed_ms": 150
}
```

**Exemples:**
```json
// GET simple
{"tool": "http_request", "params": {
  "url": "https://api.example.com/data"
}}

// POST avec body
{"tool": "http_request", "params": {
  "url": "https://api.example.com/submit",
  "method": "POST",
  "headers": {"Content-Type": "application/json"},
  "body": "{\"key\": \"value\"}"
}}

// Avec authentification
{"tool": "http_request", "params": {
  "url": "https://api.example.com/protected",
  "headers": {"Authorization": "Bearer token123"}
}}
```

**Restrictions:**
- Pas d'accès aux IPs privées (sauf localhost)
- Limite de 5 MB pour les réponses
- Timeout max de 60 secondes

---

## Outil Filesystem: search_directory (v6.2)

### `search_directory`

Recherche des répertoires par nom dans le système de fichiers.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | filesystem |
| **Risque** | 🟢 Faible |
| **Sécurité** | Allowlist de bases |

**Paramètres:**

| Nom | Type | Requis | Défaut | Description |
|-----|------|--------|--------|-------------|
| `name` | string | ✅ | - | Nom du répertoire à chercher |
| `base` | string | ❌ | WORKSPACE_DIR | Base de recherche |
| `max_depth` | int | ❌ | 3 | Profondeur maximale |

**Retour:**
```json
{
  "success": true,
  "data": {
    "query": "backend",
    "base": "/home/user",
    "max_depth": 3,
    "matches": [
      {"path": "/home/user/projects/backend", "name": "backend", "depth": 2}
    ],
    "count": 1,
    "suggestion": "/home/user/projects/backend"
  }
}
```

**Sécurité:**
- Bases autorisées: `/home`, `/workspace`, `/tmp`, `/var/www`, `/opt`, `WORKSPACE_DIR`
- Profondeur max: 3
- Résultats max: 5
- Utilisé automatiquement sur erreur `E_DIR_NOT_FOUND`

---

## Outils QA (Quality Assurance)

Les 7 outils QA sont utilisés par le Verifier pour valider les modifications.

### `git_status`

Affiche l'état du repository Git.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | qa |
| **Commande** | `git status --porcelain` |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `target` | string | ❌ | Répertoire cible (défaut: workspace) |

---

### `git_diff`

Affiche les modifications non committées.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | qa |
| **Commande** | `git diff` |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `target` | string | ❌ | Répertoire cible |
| `staged` | bool | ❌ | Inclure les changements staged |

---

### `run_tests`

Exécute les tests du projet.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | qa |
| **Commande** | `pytest` (Python) ou `npm test` (Node) |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `target` | string | ❌ | Répertoire ou fichier de test |
| `verbose` | bool | ❌ | Mode verbose |

---

### `run_lint`

Exécute le linter sur le code.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | qa |
| **Commande** | `ruff check` (Python) ou `eslint` (JS) |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `target` | string | ❌ | Répertoire ou fichier à analyser |
| `fix` | bool | ❌ | Corriger automatiquement |

---

### `run_format`

Formate le code selon les standards.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | qa |
| **Commande** | `ruff format` (Python) ou `prettier` (JS) |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `target` | string | ❌ | Répertoire ou fichier à formater |
| `check` | bool | ❌ | Vérifier seulement (pas de modification) |

---

### `run_build`

Compile/build le projet.

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | qa |
| **Commande** | `npm run build` ou `python setup.py build` |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `target` | string | ❌ | Répertoire du projet |

---

### `run_typecheck`

Vérifie les types (TypeScript/Python).

| Propriété | Valeur |
|-----------|--------|
| **Catégorie** | qa |
| **Commande** | `tsc --noEmit` (TS) ou `mypy` (Python) |

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `target` | string | ❌ | Répertoire ou fichier |

---

## Erreurs récupérables (v6.2)

Certaines erreurs déclenchent automatiquement un plan B:

| Code d'erreur | Récupérable | Action automatique |
|---------------|-------------|-------------------|
| `E_FILE_NOT_FOUND` | ✅ | Appel search_files |
| `E_DIR_NOT_FOUND` | ✅ | Appel search_directory |
| `E_PATH_NOT_FOUND` | ✅ | Appel search_files/search_directory |
| `E_PERMISSION` | ❌ | - |
| `E_CMD_NOT_ALLOWED` | ❌ | - |
| `E_PATH_FORBIDDEN` | ❌ | - |

---

## Ajout d'outils personnalisés

### Structure d'un outil

```python
async def mon_outil(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Description de l'outil pour le LLM.
    
    Args:
        param1: Description du paramètre 1
        param2: Description du paramètre 2 (optionnel)
    
    Returns:
        Dictionnaire avec le résultat
    """
    try:
        # Logique de l'outil
        result = await do_something(param1, param2)
        return {"success": True, "data": result}
    except Exception as e:
        return {"error": str(e)}
```

### Enregistrement

```python
from app.services.react_engine.tools import BUILTIN_TOOLS

BUILTIN_TOOLS.register(
    name="mon_outil",
    func=mon_outil,
    description="Description claire pour le LLM",
    category="custom",
    parameters={
        "param1": "string - Description",
        "param2": "int - Description (défaut: 10)"
    }
)
```

### Bonnes pratiques

1. **Async** - Toujours utiliser `async def` pour les I/O
2. **Timeout** - Implémenter un timeout pour éviter les blocages
3. **Erreurs** - Retourner `{"error": "message"}` plutôt que lever une exception
4. **Documentation** - Décrire clairement pour que le LLM comprenne
5. **Sécurité** - Valider les entrées, éviter les injections

---

## Matrice de sécurité

| Outil | Lecture | Écriture | Réseau | Système |
|-------|---------|----------|--------|---------|
| execute_command | ✅ | ✅ | ✅ | ✅ |
| get_system_info | ✅ | ❌ | ❌ | ✅ |
| read_file | ✅ | ❌ | ❌ | ❌ |
| write_file | ❌ | ✅ | ❌ | ❌ |
| list_directory | ✅ | ❌ | ❌ | ❌ |
| search_files | ✅ | ❌ | ❌ | ❌ |
| get_datetime | ✅ | ❌ | ❌ | ❌ |
| calculate | ✅ | ❌ | ❌ | ❌ |
| http_request | ✅ | ❌ | ✅ | ❌ |
