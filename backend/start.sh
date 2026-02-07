#!/bin/bash
# AI Orchestrator Backend Startup Script
# Uses project venv to ensure all dependencies are available

cd /home/lalpha/projets/ai-tools/ai-orchestrator/backend
exec .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001
