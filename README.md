# Sentinel — AI-Powered Behavioral Health Risk Monitor

Behavioral Health Risk Monitor ("Sentinel") is an AI-powered research prototype that ingests short daily check-ins (sleep, mood, activity, social interactions, free-text journal) and produces an explainable risk assessment (LOW / MEDIUM / HIGH). The system combines engineered behavioral features, transformer-based NLP, anomaly detection, and a rule-based weighted scorer with an optional ML classifier blend.

This README documents how the repository is organized, how to run the system locally, and what each core component does.

---

**Quick links**

- Backend API: http://localhost:8000/docs
- Streamlit dashboard: http://localhost:8501
- React dev server (frontend-web): http://localhost:5173

---

**What this repo contains (high level)**

- A FastAPI backend that implements the check-in API, orchestrates the ML/NLP pipeline, persists check-ins in SQLite, and exposes analytics endpoints.
- A Streamlit dashboard (legacy) for submitting check-ins and seeing trends.
- A React + Vite frontend skeleton in `frontend-web/` for landing pages and future UI migration.
- Lightweight in-repo ML code: feature engineering, a DistilBERT-based NLP analyzer, an Isolation Forest anomaly detector, an XGBoost classifier, and a rule-based `RiskScoringEngine` that combines signals into a final score.
- Utilities to generate synthetic training data so the system can run out-of-the-box.

---

**Status & Notes**

- The backend is the primary, production-intent component. On startup it initialises all ML components and will train lightweight models on synthetic data if pre-trained artifacts are not present.
- The Streamlit dashboard provides a usable demo UI. The modern React UI in `frontend-web/` is focused on marketing/landing pages and is not yet a full replacement for the dashboard.

---

**Requirements**

Install system requirements from `requirements.txt` (Python 3.10+ recommended). HuggingFace `transformers` and `torch` are required for the NLP analyzer; they can increase setup time and disk usage.

---

## Quickstart (local)

1. Clone and enter the repo

```bash
git clone <repo-url>
cd behavioral-health-monitor
```

2. (Recommended) Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

3. Install Python dependencies

```bash
pip install -r requirements.txt
```

4. Run the full demo (this will generate synthetic training data if missing)

```bash
bash run.sh
```

Alternative: run components separately

```bash
# Backend (FastAPI)
cd backend && uvicorn main:app --reload --port 8000

# Streamlit dashboard (legacy)
cd frontend && streamlit run dashboard.py --server.port 8501

# React dev server (frontend-web)
cd frontend-web && npm install && npm run dev
```

Open the API docs at `http://localhost:8000/docs` and the dashboard at `http://localhost:8501`.

---

## Core components (implementation details)

- `backend/main.py`: FastAPI app that orchestrates the pipeline and exposes endpoints (`/api/checkin`, `/api/history/{user_id}`, `/api/stats/{user_id}`, `/api/risk-trend/{user_id}`, `/health`). On startup it initialises `MentalHealthNLPAnalyzer`, `BehavioralAnomalyDetector`, `RiskClassifier`, and `RiskScoringEngine`.
- `backend/feature_engineering.py`: Extracts 15+ behavioral features from recent check-in history (sleep, mood, social, activity, composites).
- `backend/nlp_analyzer.py`: DistilBERT sentiment pipeline plus linguistic markers (first-person ratio, absolutist words, negative-emotion words) and a composite `nlp_risk_score`.
- `backend/anomaly_detector.py`: Isolation Forest based behavioral anomaly detection (normalised anomaly risk output).
- `backend/risk_classifier.py`: Lightweight XGBoost risk classifier used when trained artifacts are available (blended with the rule-based score).
- `backend/risk_engine.py`: Rule-based weighted scorer (NLP 30%, Anomaly 25%, Sleep 18%, Mood 17%, Social 10%) with weight re-normalisation when components are unavailable and a safety override path.
- `backend/data_ingestion.py` and `backend/database.py`: SQLAlchemy models and helpers to persist and retrieve check-ins as DataFrames for the ML pipeline.

---

## API — example

POST `/api/checkin` accepts JSON payloads like:

```json
{
	"user_id": "user_001",
	"sleep_hours": 5.5,
	"mood_score": 3,
	"activity_level": "sedentary",
	"social_interactions": 0,
	"journal_text": "I feel exhausted and hopeless today."
}
```

Response includes `risk_level`, `risk_score`, `component_scores`, `recommendation`, `nlp_analysis`, and a `safety_override` flag when safety phrases are detected.

For interactive testing, use the OpenAPI docs at `/docs` or the Streamlit dashboard demo UI.

---

## Data & Models

- `data/generate_synthetic_data.py` can create a small synthetic dataset and train the in-repo models so the system runs without external artifacts.
- Trained model artifacts (when produced) are stored under `models/`.

---

## Safety & Disclaimer

This repository is a research prototype and not a medical device. It is intended for educational and development purposes only and must not be used as a substitute for professional diagnosis or emergency services.

If you or someone you know is in immediate danger, contact local emergency services or crisis resources in your region (for example: 988 in the US).

---

## Contributing

Contributions are welcome. Suggested next work items:

- Add end-to-end tests for the API + model blending behaviour
- Port the Streamlit dashboard into the React app for a single consolidated frontend
- Add CI that runs unit tests and optionally trains on tiny synthetic data

---

## License & Acknowledgements

Academic/research use. See project authors for reuse permissions.

Sentinel — HRMS-G67
