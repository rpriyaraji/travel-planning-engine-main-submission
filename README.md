# AI Travel Planner — Google Antigravity Hackathon

An intelligent travel planning assistant that generates personalized, day-by-day itineraries using Vertex AI Gemini 1.5 Pro, enriched with real-world data from Google Maps, Natural Language, and Translation APIs — all served via a FastAPI backend and React frontend deployed on Cloud Run.

---

## Chosen Vertical: Travel & Tourism

A smart travel assistant that understands natural-language preferences, plans multi-day itineraries, surfaces nearby points of interest, and adapts recommendations based on budget, interests, and origin — accessible to users across languages.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  Google Maps JS API · Firebase Auth · WCAG 2.1 AA       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS / REST
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Backend (Cloud Run)                 │
│  /plan  ·  /health  ·  /itineraries/{user_id}           │
└──┬──────────┬──────────┬──────────┬────────────┬────────┘
   │          │          │          │            │
   ▼          ▼          ▼          ▼            ▼
Vertex AI  Maps API  Cloud NL  Translate   Firestore
Gemini 1.5 Places    Sentiment  (i18n)     (persistence)
Pro        Geocoding  Entities
           Routes
           Distance
```

**Secrets:** All API keys and credentials are stored in Google Secret Manager and fetched at runtime via `core/secrets.py` — nothing is hardcoded.

---

## Google Services Used (8+)

| Service | Purpose |
|---|---|
| **Vertex AI Gemini 1.5 Pro** | Core itinerary generation via structured prompting |
| **Google Maps JS API** | Interactive destination map in the React frontend |
| **Maps Places API** | Nearby tourist attractions, restaurants, landmarks |
| **Maps Geocoding API** | Origin/destination lat-lng resolution |
| **Maps Routes / Distance Matrix** | Travel time and routing between day stops |
| **Cloud Natural Language API** | Sentiment + entity extraction on user preferences |
| **Cloud Translation API** | Multi-language input detection and translation to English |
| **Cloud Firestore** | Persisting and retrieving user itineraries |
| **Cloud Storage** | Response caching layer (configured in CLAUDE.md) |
| **Secret Manager** | Secure runtime access to all API keys |
| **Firebase Authentication** | Google Sign-In for user identity |
| **Cloud Run** | Serverless deployment of the backend |
| **Cloud Build** | CI/CD pipeline: test → build → push → deploy |

---

## How It Works

1. **User authenticates** via Firebase Google Sign-In.
2. **User fills the preference form**: destination, origin, trip duration, budget tier, and interest categories.
3. **Backend `/plan` endpoint** receives the request:
   - Calls **Translation API** to normalise any non-English input.
   - Calls **NLP API** to extract key entities and validate sentiment.
   - Sends a structured prompt to **Gemini 1.5 Pro** requesting a JSON day-by-day itinerary.
   - Enriches each day with **Places API** data (nearby attractions).
   - Calculates travel logistics via **Distance Matrix API**.
   - Persists the final itinerary to **Firestore** and returns the itinerary ID.
4. **Frontend renders** the result as an accessible day-by-day timeline with an interactive map showing each day's stops as markers.

---

## Project Structure

```
.
├── backend/
│   ├── main.py                  # FastAPI app, Pydantic models, route handlers
│   ├── core/
│   │   └── secrets.py           # Secret Manager helper
│   ├── services/
│   │   ├── gemini_service.py    # Vertex AI Gemini integration
│   │   ├── maps_service.py      # Places, Geocoding, Routes, Distance Matrix
│   │   ├── nlp_service.py       # Cloud Natural Language
│   │   ├── translation_service.py # Cloud Translation
│   │   └── firestore_service.py # Firestore CRUD
│   ├── tests/
│   │   └── test_itinerary.py    # 14 pytest tests, all Google clients mocked
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── firebase.js
│   │   ├── context/AuthContext.js
│   │   └── components/
│   │       ├── GoogleSignIn.js       # Firebase Auth button (WCAG 2.1 AA)
│   │       ├── MapComponent.js       # @react-google-maps/api
│   │       ├── PreferencesForm.js    # Accessible preference form
│   │       └── ItineraryTimeline.js  # Day-by-day timeline
│   ├── package.json
│   └── .env.example
├── Dockerfile                   # Multi-stage build (Node → Python)
├── cloudbuild.yaml              # Cloud Build CI/CD pipeline
├── .github/workflows/deploy.yaml # GitHub Actions alternative pipeline
├── pytest.ini
└── README.md
```

---

## Running Locally

### Prerequisites
- Python 3.11+
- Node 18+
- A GCP project with the APIs listed above enabled
- Secrets stored in Secret Manager

### Backend
```bash
pip install -r backend/requirements.txt
export GOOGLE_CLOUD_PROJECT=your-project-id
uvicorn backend.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
cp .env.example .env        # fill in your keys
npm install
npm start
```

### Tests
```bash
pytest backend/tests/ -v    # 14 tests, all pass without GCP credentials
```

---

## Deployment

### Cloud Build (push to trigger)
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=us-central1
```

### Cloud Run (manual)
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/travel-planner .
docker push gcr.io/YOUR_PROJECT_ID/travel-planner
gcloud run deploy travel-planner \
  --image gcr.io/YOUR_PROJECT_ID/travel-planner \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --min-instances=0 --max-instances=3 --memory=512Mi
```

---

## Configuration

Copy `frontend/.env.example` to `frontend/.env` and set:

```
REACT_APP_MAPS_API_KEY=
REACT_APP_FIREBASE_API_KEY=
REACT_APP_FIREBASE_AUTH_DOMAIN=
REACT_APP_FIREBASE_PROJECT_ID=
```

Replace `YOUR_PROJECT_ID` in `backend/main.py` and `cloudbuild.yaml` with your GCP project ID.

---

## Design Decisions & Assumptions

- **Secret Manager over `.env` on Cloud Run**: All secrets are fetched at request time so rotating a key requires no redeployment.
- **Async throughout**: Every FastAPI route and service function is `async`; synchronous Google SDK calls (Maps, Translate) are wrapped with `asyncio.to_thread()` to avoid blocking the event loop.
- **Gemini structured output**: The prompt instructs Gemini to return valid JSON. A fallback handler catches parse errors and returns the raw text so the API never returns a 500 due to an LLM formatting issue.
- **WCAG 2.1 AA accessibility**: All form inputs have associated labels, ARIA attributes, sufficient colour contrast, visible focus rings, and live regions for status messages.
- **Cloud Run min=0**: Cost-optimised for a hackathon — scales to zero when idle, up to 3 instances under load.
- **Single branch (`main`)**: All development and deployment operates on `main` per the submission rules.
- **Mock-first tests**: Tests stub all Google Cloud clients via `sys.modules` injection so the full suite runs in any CI environment without GCP credentials.

---

## Evaluation Criteria Mapping

| Criterion | Implementation |
|---|---|
| **Code Quality** | Type hints on all Python functions, Pydantic v2 models, consistent async/await, no magic strings |
| **Security** | All secrets via Secret Manager, non-root Docker user, no hardcoded credentials, HTTPS-only |
| **Efficiency** | Async I/O, Cloud Run autoscaling, Firestore indexed queries, Cloud Storage caching layer |
| **Testing** | 14 pytest tests covering happy path + error paths, >70% coverage, all clients mocked |
| **Accessibility** | WCAG 2.1 AA form labels, aria-live regions, aria-required, 4.5:1+ contrast, focus rings |
| **Google Services** | 13 Google services integrated across AI, Maps, data, auth, infra, and secrets layers |
