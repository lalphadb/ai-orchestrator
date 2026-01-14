# Développement — v7.1

## Backend

- Installer deps (exemple) :
  - `python -m venv .venv && . .venv/bin/activate`
  - `pip install -r requirements.txt`
- Lancer : `uvicorn ...`

## Frontend

- `npm ci`
- `npm run dev`

## Qualité

Recommandé :
- `make quality` (ou équivalent)
- `pytest`
- `npm run lint` + `npm run build`
