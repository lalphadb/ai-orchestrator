#!/usr/bin/env python3
"""
Script de migration et réorganisation des dashboards Grafana
Réorganise automatiquement les dashboards selon la nouvelle structure

Usage:
    python migrate_dashboards.py --dry-run          # Voir les changements sans appliquer
    python migrate_dashboards.py --execute          # Appliquer les changements
    python migrate_dashboards.py --export           # Exporter tous les dashboards
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

# Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD", "ChangeMe123!")

# Mapping: ancien nom → nouvelle config
DASHBOARD_MAPPING = {
    "Infrastructure Home": {
        "new_name": "🏠 Overview - Infrastructure Home",
        "folder": "📊 1. Overview & Home",
        "folder_uid": "overview-home",
        "tags": ["overview", "home", "infrastructure"],
        "emoji": "🏠",
    },
    "Infrastructure Changelog": {
        "new_name": "📦 Admin - Infrastructure Changelog",
        "folder": "🔧 9. Admin & Maintenance",
        "folder_uid": "admin-maintenance",
        "tags": ["admin", "changelog", "infrastructure"],
        "emoji": "📦",
    },
    "AI Orchestrator - Learning": {
        "new_name": "🧠 AI - Learning & Training",
        "folder": "🤖 5. AI-Orchestrator",
        "folder_uid": "ai-orchestrator",
        "tags": ["ai", "learning", "orchestrator", "training"],
        "emoji": "🧠",
    },
    "Traefik & Services": {
        "new_name": "🚦 HTTP - Traefik & Services",
        "folder": "🌐 4. Networking & HTTP",
        "folder_uid": "networking-http",
        "tags": ["traefik", "http", "networking", "services"],
        "emoji": "🚦",
    },
    "NVIDIA GPU - RTX 5070 Ti": {
        "new_name": "🖥️ Infra - NVIDIA GPU RTX 5070 Ti",
        "folder": "🏗️ 2. Infrastructure",
        "folder_uid": "infrastructure",
        "tags": ["infrastructure", "gpu", "nvidia", "hardware"],
        "emoji": "🖥️",
    },
    "Docker Containers": {
        "new_name": "🐋 Docker - Containers Overview",
        "folder": "🐳 3. Docker & Containers",
        "folder_uid": "docker-containers",
        "tags": ["docker", "containers", "cadvisor"],
        "emoji": "🐋",
    },
    "System Overview - lalpha-server-1": {
        "new_name": "💻 Infra - System Overview (Node Exporter)",
        "folder": "🏗️ 2. Infrastructure",
        "folder_uid": "infrastructure",
        "tags": ["infrastructure", "system", "node-exporter", "monitoring"],
        "emoji": "💻",
    },
    "Ollama LLM": {
        "new_name": "🦙 AI - Ollama LLM",
        "folder": "🧠 6. AI & ML Stack",
        "folder_uid": "ai-ml-stack",
        "tags": ["ai", "llm", "ollama", "models"],
        "emoji": "🦙",
    },
}

# Nouveaux dashboards à créer
NEW_DASHBOARDS = [
    {
        "name": "📈 Overview - Global Metrics Summary",
        "folder": "📊 1. Overview & Home",
        "folder_uid": "overview-home",
        "tags": ["overview", "metrics", "summary"],
        "description": "Vue d'ensemble des métriques globales de l'infrastructure",
    },
    {
        "name": "🚨 Alerts - Active Alerts",
        "folder": "⚠️ 8. Alerting & Incidents",
        "folder_uid": "alerting-incidents",
        "tags": ["alerts", "incidents", "monitoring"],
        "description": "Liste des alertes actives et historique",
    },
    {
        "name": "📝 Logs - Loki Explorer",
        "folder": "📈 7. Observability",
        "folder_uid": "observability",
        "tags": ["logs", "loki", "observability"],
        "description": "Explorateur de logs Loki avec filtres avancés",
    },
    {
        "name": "🎯 AI - Application Overview",
        "folder": "🤖 5. AI-Orchestrator",
        "folder_uid": "ai-orchestrator",
        "tags": ["ai", "orchestrator", "overview", "application"],
        "description": "Vue d'ensemble de l'application AI-Orchestrator",
    },
]

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class GrafanaClient:
    """Client pour interagir avec l'API Grafana"""

    def __init__(self, url: str, user: str, password: str):
        self.url = url.rstrip("/")
        self.auth = HTTPBasicAuth(user, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    def get_all_dashboards(self) -> List[Dict]:
        """Récupère tous les dashboards"""
        try:
            response = self.session.get(f"{self.url}/api/search?type=dash-db")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des dashboards: {e}")
            return []

    def get_dashboard(self, uid: str) -> Optional[Dict]:
        """Récupère un dashboard par son UID"""
        try:
            response = self.session.get(f"{self.url}/api/dashboards/uid/{uid}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération du dashboard {uid}: {e}")
            return None

    def create_or_update_dashboard(
        self, dashboard: Dict, folder_uid: str, message: str = "Migration automatique"
    ) -> bool:
        """Crée ou met à jour un dashboard"""
        try:
            payload = {
                "dashboard": dashboard,
                "folderUid": folder_uid,
                "message": message,
                "overwrite": True,
            }

            response = self.session.post(f"{self.url}/api/dashboards/db", json=payload)
            response.raise_for_status()
            logger.info(f"✓ Dashboard '{dashboard['title']}' mis à jour avec succès")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(
                f"✗ Erreur lors de la mise à jour du dashboard '{dashboard.get('title', 'unknown')}': {e}"
            )
            return False

    def get_folders(self) -> List[Dict]:
        """Récupère tous les dossiers"""
        try:
            response = self.session.get(f"{self.url}/api/folders")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des dossiers: {e}")
            return []

    def create_folder(self, title: str, uid: str) -> bool:
        """Crée un nouveau dossier"""
        try:
            payload = {"title": title, "uid": uid}
            response = self.session.post(f"{self.url}/api/folders", json=payload)
            response.raise_for_status()
            logger.info(f"✓ Dossier '{title}' créé avec succès")
            return True
        except requests.exceptions.RequestException as e:
            if "already exists" in str(e).lower():
                logger.debug(f"Dossier '{title}' existe déjà")
                return True
            logger.error(f"✗ Erreur lors de la création du dossier '{title}': {e}")
            return False


def migrate_dashboard(
    client: GrafanaClient, dashboard_info: Dict, mapping: Dict, dry_run: bool = True
) -> bool:
    """Migre un dashboard selon le mapping"""

    title = dashboard_info.get("title")
    uid = dashboard_info.get("uid")

    if not title or not uid:
        logger.warning(f"Dashboard sans titre ou UID: {dashboard_info}")
        return False

    # Vérifier si le dashboard est dans le mapping
    config = mapping.get(title)
    if not config:
        logger.debug(f"Dashboard '{title}' non mappé, ignoré")
        return False

    logger.info(f"\n{'='*60}")
    logger.info(f"Migration: {title}")
    logger.info(f"  → {config['new_name']}")
    logger.info(f"  → Dossier: {config['folder']}")
    logger.info(f"  → Tags: {', '.join(config['tags'])}")

    if dry_run:
        logger.info("  → [DRY-RUN] Aucune modification appliquée")
        return True

    # Récupérer le dashboard complet
    dashboard_data = client.get_dashboard(uid)
    if not dashboard_data:
        return False

    dashboard = dashboard_data["dashboard"]

    # Appliquer les modifications
    dashboard["title"] = config["new_name"]
    dashboard["tags"] = config["tags"]

    # Ajouter/mettre à jour la description
    if "description" not in dashboard or not dashboard["description"]:
        dashboard["description"] = (
            f"Dashboard migré automatiquement le {datetime.now().strftime('%Y-%m-%d')}"
        )

    # Mettre à jour le dashboard
    success = client.create_or_update_dashboard(
        dashboard, config["folder_uid"], f"Migration: {title} → {config['new_name']}"
    )

    return success


def export_dashboards(client: GrafanaClient, output_dir: Path):
    """Exporte tous les dashboards en JSON"""

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Export des dashboards dans: {output_dir}")

    dashboards = client.get_all_dashboards()
    logger.info(f"Nombre de dashboards trouvés: {len(dashboards)}")

    success_count = 0
    for dash_info in dashboards:
        uid = dash_info.get("uid")
        title = dash_info.get("title", "unknown")

        # Nettoyer le nom de fichier
        safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in title)
        filename = f"{safe_title}_{uid}.json"

        dashboard_data = client.get_dashboard(uid)
        if dashboard_data:
            filepath = output_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(dashboard_data["dashboard"], f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Exporté: {title}")
            success_count += 1
        else:
            logger.error(f"✗ Échec export: {title}")

    logger.info(f"\nExport terminé: {success_count}/{len(dashboards)} dashboards exportés")


def create_folders(client: GrafanaClient, dry_run: bool = True):
    """Crée les dossiers de la nouvelle structure"""

    folders = [
        ("📊 1. Overview & Home", "overview-home"),
        ("🏗️ 2. Infrastructure", "infrastructure"),
        ("🐳 3. Docker & Containers", "docker-containers"),
        ("🌐 4. Networking & HTTP", "networking-http"),
        ("🤖 5. AI-Orchestrator", "ai-orchestrator"),
        ("🧠 6. AI & ML Stack", "ai-ml-stack"),
        ("📈 7. Observability", "observability"),
        ("⚠️ 8. Alerting & Incidents", "alerting-incidents"),
        ("🔧 9. Admin & Maintenance", "admin-maintenance"),
    ]

    logger.info("\nCréation de la structure de dossiers...")

    for title, uid in folders:
        if dry_run:
            logger.info(f"  [DRY-RUN] Créerait le dossier: {title}")
        else:
            client.create_folder(title, uid)


def main():
    parser = argparse.ArgumentParser(description="Migration des dashboards Grafana")
    parser.add_argument(
        "--dry-run", action="store_true", help="Afficher les changements sans les appliquer"
    )
    parser.add_argument("--execute", action="store_true", help="Appliquer les changements")
    parser.add_argument("--export", action="store_true", help="Exporter tous les dashboards")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./backups/dashboards",
        help="Répertoire de sortie pour l'export",
    )

    args = parser.parse_args()

    # Valider les arguments
    if not any([args.dry_run, args.execute, args.export]):
        parser.error("Veuillez spécifier --dry-run, --execute ou --export")

    # Client Grafana
    client = GrafanaClient(GRAFANA_URL, GRAFANA_USER, GRAFANA_PASSWORD)

    # Mode export
    if args.export:
        output_dir = Path(args.output_dir) / datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dashboards(client, output_dir)
        return

    # Mode migration
    logger.info("=" * 60)
    logger.info("MIGRATION DES DASHBOARDS GRAFANA")
    logger.info("=" * 60)
    logger.info(f"URL Grafana: {GRAFANA_URL}")
    logger.info(
        f"Mode: {'DRY-RUN (simulation)' if args.dry_run else 'EXECUTION (modifications appliquées)'}"
    )
    logger.info("=" * 60)

    # 1. Créer les dossiers
    create_folders(client, dry_run=args.dry_run)

    # 2. Récupérer tous les dashboards
    logger.info("\nRécupération des dashboards existants...")
    dashboards = client.get_all_dashboards()
    logger.info(f"Nombre de dashboards trouvés: {len(dashboards)}")

    # 3. Migrer les dashboards
    logger.info("\nMigration des dashboards...")
    success_count = 0
    for dash_info in dashboards:
        if migrate_dashboard(client, dash_info, DASHBOARD_MAPPING, dry_run=args.dry_run):
            success_count += 1

    # 4. Résumé
    logger.info("\n" + "=" * 60)
    logger.info("RÉSUMÉ")
    logger.info("=" * 60)
    logger.info(f"Dashboards traités: {len(dashboards)}")
    logger.info(f"Dashboards migrés: {success_count}")
    logger.info(f"Dashboards ignorés: {len(dashboards) - success_count}")

    if args.dry_run:
        logger.info("\n⚠️ DRY-RUN: Aucune modification appliquée")
        logger.info("Pour appliquer les changements, utilisez: --execute")
    else:
        logger.info("\n✅ Migration terminée avec succès!")
        logger.info("Vérifiez les dashboards dans Grafana: " + GRAFANA_URL)


if __name__ == "__main__":
    main()
