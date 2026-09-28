# AegisCloud

AI-powered container and cloud security platform: static scanning (Trivy), runtime detection (Falco),
AI explanations, live dashboard, Prometheus + Grafana metrics, and AWS SNS alerts.

## Status: Week 1
Vue 3 frontend skeleton, FastAPI backend, MongoDB connection, JWT login, RBAC, audit log, dashboard layout.

## Run with Docker
```bash
cp .env.example .env      # then edit JWT_SECRET
docker compose up --build
```
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

## Run without Docker
```bash
# Terminal 1: MongoDB must be running on localhost:27017
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload

# Terminal 2
cd frontend && npm install && npm run dev
```

## Roles
The first account registered becomes `admin`; later accounts are `viewer`. Roles: admin, analyst, viewer.

## Tests
```bash
cd backend && pytest
```