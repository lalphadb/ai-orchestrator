# 📊 Configuration Grafana Professionnelle

Structure organisée et scalable pour vos dashboards Grafana.

---

## 🚀 Quick Start (3 commandes)

```bash
cd monitoring/grafana/

# 1. Voir ce qui sera fait (simulation)
./migrate.sh dry-run

# 2. Appliquer la migration
./migrate.sh execute

# 3. Vérifier dans Grafana
open https://grafana.4lb.ca/dashboards
```

**C'est tout!** Vos dashboards sont maintenant organisés proprement. ✨

---

## 📁 Structure créée

```
Grafana Dashboards
│
├── 📊 1. Overview & Home
│   ├── 🏠 Infrastructure Home
│   ├── 📈 Global Metrics Summary
│   └── 🎯 SLO Dashboard
│
├── 🏗️ 2. Infrastructure
│   ├── 💻 System Overview (Node Exporter)
│   ├── 🖥️  NVIDIA GPU - RTX 5070 Ti
│   ├── 💾 Storage & Disk Usage
│   └── 🔌 Network Interfaces
│
├── 🐳 3. Docker & Containers
│   ├── 🐋 Docker Containers
│   ├── 📊 Docker Resource Usage
│   └── 🔄 Container Lifecycle
│
├── 🌐 4. Networking & HTTP
│   ├── 🚦 Traefik & Services
│   ├── 📡 HTTP Observatory
│   ├── 🌍 DNS & Load Balancing
│   └── 🔒 SSL Certificates
│
├── 🤖 5. AI-Orchestrator
│   ├── 🎯 Application Overview
│   ├── 🔧 Backend Performance
│   ├── 🎨 Frontend Metrics
│   ├── 🧠 Learning & Training
│   ├── 🔄 Workflow Engine
│   └── 🛠️  Tool Usage Analytics
│
├── 🧠 6. AI & ML Stack
│   ├── 🦙 Ollama LLM
│   ├── 🔮 Model Performance
│   ├── 📊 ChromaDB Vector Store
│   └── 🎓 Learning & Training
│
├── 📈 7. Observability
│   ├── 📝 Loki Logs Explorer
│   ├── 📊 Prometheus Metrics
│   ├── 🔍 Request Tracing
│   └── 🐛 Error Tracking
│
├── ⚠️ 8. Alerting & Incidents
│   ├── 🚨 Active Alerts
│   ├── 📉 SLO Violations
│   └── 📊 Alert History
│
└── 🔧 9. Admin & Maintenance
    ├── 📦 Infrastructure Changelog
    ├── 🔄 Backup Status
    └── 🛠️  System Health
```

---

## 🎯 Avantages de cette structure

### ✅ Avant (désorganisé)
- ❌ Dashboards éparpillés
- ❌ Dossiers dupliqués/vides
- ❌ Pas de convention de nommage
- ❌ Tags incohérents
- ❌ Difficile à naviguer

### ✨ Après (organisé)
- ✅ **9 dossiers numérotés** - Hiérarchie claire
- ✅ **Emojis visuels** - Reconnaissance rapide
- ✅ **Noms standardisés** - Convention cohérente
- ✅ **Tags structurés** - Recherche facile
- ✅ **Navigation intuitive** - Trouver en 2 clics

---

## 📋 Commandes disponibles

### Migration

```bash
# Voir les changements (aucune modification)
./migrate.sh dry-run

# Exécuter la migration
./migrate.sh execute

# Exporter tous les dashboards (backup)
./migrate.sh export

# Aide
./migrate.sh help
```

---

### Python direct (avancé)

```bash
# Simulation
python3 migrate_dashboards.py --dry-run

# Exécution
python3 migrate_dashboards.py --execute

# Export
python3 migrate_dashboards.py --export

# Export dans un dossier spécifique
python3 migrate_dashboards.py --export --output-dir=/backups/grafana
```

---

## ⚙️ Configuration

Par défaut:
```bash
GRAFANA_URL=http://localhost:3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=ChangeMe123!
```

Pour changer:
```bash
export GRAFANA_URL="https://grafana.4lb.ca"
export GRAFANA_USER="admin"
export GRAFANA_PASSWORD="votre_mot_de_passe"

./migrate.sh execute
```

Ou créer un fichier `.env`:
```bash
# .env
GRAFANA_URL=https://grafana.4lb.ca
GRAFANA_USER=admin
GRAFANA_PASSWORD=votre_mot_de_passe
```

Puis:
```bash
source .env
./migrate.sh execute
```

---

## 📊 Mapping des dashboards

| Dashboard actuel | Nouveau nom | Dossier |
|------------------|-------------|---------|
| Infrastructure Home | 🏠 Overview - Infrastructure Home | 1. Overview & Home |
| Infrastructure Changelog | 📦 Admin - Infrastructure Changelog | 9. Admin & Maintenance |
| AI Orchestrator - Learning | 🧠 AI - Learning & Training | 5. AI-Orchestrator |
| Traefik & Services | 🚦 HTTP - Traefik & Services | 4. Networking & HTTP |
| NVIDIA GPU - RTX 5070 Ti | 🖥️ Infra - NVIDIA GPU RTX 5070 Ti | 2. Infrastructure |
| Docker Containers | 🐋 Docker - Containers Overview | 3. Docker & Containers |
| System Overview - lalpha-server-1 | 💻 Infra - System Overview | 2. Infrastructure |
| Ollama LLM | 🦙 AI - Ollama LLM | 6. AI & ML Stack |

---

## 🎨 Convention de nommage

### Format standard
```
[Emoji] [Catégorie] - [Nom spécifique]
```

### Exemples
- ✅ `🚦 HTTP - Traefik & Services`
- ✅ `🤖 AI - Backend Performance`
- ✅ `💻 Infra - System Overview (Node Exporter)`
- ✅ `🐋 Docker - Container Resource Usage`

### Emojis par domaine
- 📊 Overview
- 🏗️ Infrastructure
- 🐳 Docker
- 🌐 Networking
- 🤖 AI-Orchestrator
- 🧠 AI & ML
- 📈 Observability
- ⚠️ Alerting
- 🔧 Admin

---

## 🏷️ Tags standardisés

### Tags primaires (domaine)
```
overview, infrastructure, docker, networking, ai, observability, alerts, admin
```

### Tags secondaires (technologie)
```
traefik, prometheus, loki, ollama, chromadb, gpu, http, ssl, learning
```

### Tags tertiaires (type)
```
performance, resources, errors, debugging, security, slo
```

---

## 🔍 Recherche rapide

Utilisez les tags ou emojis pour chercher:

| Recherche | Trouve |
|-----------|--------|
| `🚦` ou `traefik` | Traefik dashboards |
| `🤖` ou `ai` | AI-Orchestrator |
| `💻` ou `system` | System Overview |
| `🐋` ou `docker` | Docker Containers |
| `📝` ou `logs` | Logs Explorer |

---

## 📚 Documentation

- **Guide de migration complet**: `MIGRATION_GUIDE.md`
- **Structure détaillée**: `STRUCTURE.md`
- **Script Python**: `migrate_dashboards.py`
- **Provisioning Grafana**: `provisioning/dashboards/folders.yml`

---

## ✅ Checklist post-migration

- [ ] Migration exécutée avec succès
- [ ] 9 dossiers visibles dans Grafana
- [ ] Tous les dashboards renommés avec emojis
- [ ] Tags standardisés appliqués
- [ ] Anciens dossiers vides supprimés
- [ ] Dashboard par défaut défini: `🏠 Overview - Infrastructure Home`
- [ ] Backup récent disponible
- [ ] Équipe informée de la nouvelle structure

---

## 🐛 Problèmes courants

### Erreur de connexion

```bash
# Tester la connexion
curl -u admin:ChangeMe123! http://localhost:3000/api/health

# Si échec, vérifier:
# 1. Grafana est démarré
docker ps | grep grafana

# 2. Port correct
ss -tulpn | grep 3000

# 3. Credentials corrects
docker logs grafana | grep password
```

---

### Module Python manquant

```bash
# Installer requests
pip3 install requests

# Ou avec apt
sudo apt install python3-requests
```

---

### Dashboards dupliqués

Si vous voyez des dashboards en double après migration:

1. Garder ceux avec emoji (nouveaux)
2. Supprimer ceux sans emoji (anciens)

Ou relancer:
```bash
./migrate.sh execute
```

---

## 🔙 Rollback (annuler)

Pour revenir en arrière:

```bash
# 1. Voir les backups disponibles
ls -lh backups/dashboards/

# 2. Restaurer manuellement via Grafana UI
# Ou via API (voir MIGRATION_GUIDE.md)
```

---

## 🎯 Prochaines étapes

Après la migration:

1. **Nettoyer**: Supprimer dashboards obsolètes
2. **Dashboard par défaut**: Définir `🏠 Overview - Infrastructure Home`
3. **Favoris**: Marquer dashboards importants en "Starred" ⭐
4. **Playlists**: Créer playlists pour monitoring
5. **Alertes**: Vérifier alertes dans "⚠️ 8. Alerting"

---

## 💡 Bonnes pratiques

### Maintenance régulière

- **Hebdomadaire**: Vérifier dashboards cassés
- **Mensuel**: Nettoyer dashboards inutilisés
- **Trimestriel**: Réviser structure si besoin

### Création de nouveaux dashboards

Toujours respecter:
1. **Nommage**: Emoji + Catégorie + Nom
2. **Dossier**: Placer dans le bon dossier (1-9)
3. **Tags**: 3-5 tags cohérents
4. **Description**: Expliquer les métriques clés

### Collaboration

- Documenter changements dans "📦 Infrastructure Changelog"
- Partager dashboards importants
- Former l'équipe à la nouvelle structure

---

## 📞 Support

- **Documentation complète**: Voir `MIGRATION_GUIDE.md` et `STRUCTURE.md`
- **Issues**: Créer une issue si problème
- **Grafana API**: https://grafana.com/docs/grafana/latest/http_api/

---

**Dernière mise à jour**: 2026-01-26
**Version**: 1.0
**Maintainer**: DevOps Team
