# CLAUDE.md — Travel Planner (Antigravity Hackathon)

## Project
FastAPI + React travel planner on Cloud Run using 19 Google services.
GCP Project: YOUR_PROJECT_ID | Region: us-central1

## Stack
- Backend: Python 3.11 / FastAPI / uvicorn
- Frontend: React + Maps JS API
- AI: Vertex AI Gemini 1.5 Pro (via google-cloud-aiplatform)
- Data: Firestore + Cloud Storage cache
- Secrets: ALL via Secret Manager (never hardcode)

## File Structure
backend/main.py, backend/services/, backend/tests/
frontend/src/, frontend/src/components/, frontend/tests/
Dockerfile, cloudbuild.yaml, cloudbuild.yaml

## Rules
- Type hints on all Python functions
- async/await throughout FastAPI routes
- Every service call wrapped in try/except
- pytest for backend, Jest for frontend
- No hardcoded keys — use core/secrets.py get_secret()
