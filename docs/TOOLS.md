# Outils (Tools)

Documentation complète des 9 outils intégrés dans AI Orchestrator v6.

---

## Vue d'ensemble

Le système d'outils permet à l'IA d'interagir avec le système d'exploitation et d'effectuer des actions concrètes. Chaque outil est une fonction Python async qui peut être appelée par le moteur ReAct.

### Catégories

| Catégorie | Outils | Description |
|-----------|--------|-------------|
| **system** | 2 | Commandes système et informations |
| **files** | 4 | Manipulation de fichiers |
| **utility** | 2 | Date/heure et calculs |
| **network** | 1 | Requêtes HTTP |

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
