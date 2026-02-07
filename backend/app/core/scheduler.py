"""
Scheduler pour tâches périodiques - CRQ-P0-5
"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Import optionnel d'APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    APSCHEDULER_AVAILABLE = True
    # Instance globale du scheduler
    scheduler = AsyncIOScheduler()
except ImportError:
    APSCHEDULER_AVAILABLE = False
    scheduler = None
    logger.warning("[SCHEDULER] APScheduler non installé (pip install apscheduler)")


def cleanup_memory_task():
    """Tâche périodique de cleanup des memories expirées"""
    if not settings.ENABLE_MEMORY_CLEANUP:
        return

    try:
        from app.services.react_engine.memory import durable_memory

        cleaned = durable_memory.cleanup_expired()
        if cleaned > 0:
            logger.info(f"[SCHEDULER] Memory cleanup: {cleaned} entrées supprimées")
    except Exception as e:
        logger.error(f"[SCHEDULER] Erreur cleanup memory: {e}")


def start_scheduler():
    """Démarre le scheduler avec les tâches configurées"""
    if not settings.ENABLE_MEMORY_CLEANUP:
        logger.info("[SCHEDULER] Memory cleanup désactivé (ENABLE_MEMORY_CLEANUP=false)")
        return

    if not APSCHEDULER_AVAILABLE:
        logger.warning("[SCHEDULER] Impossible de démarrer: APScheduler non installé")
        return

    # Tâche cleanup memory (toutes les N heures)
    scheduler.add_job(
        cleanup_memory_task,
        trigger=IntervalTrigger(hours=settings.MEMORY_CLEANUP_INTERVAL_HOURS),
        id="memory_cleanup",
        name="Memory Cleanup Task",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"[SCHEDULER] Démarré - Memory cleanup toutes les {settings.MEMORY_CLEANUP_INTERVAL_HOURS}h"
    )


def stop_scheduler():
    """Arrête le scheduler proprement"""
    if APSCHEDULER_AVAILABLE and scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("[SCHEDULER] Arrêté")
