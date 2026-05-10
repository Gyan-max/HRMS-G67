# 🧠 AI-Based Micro Behavioral Health Risk Monitoring System

An intelligent system that monitors subtle daily behavioral signals (sleep, mood, activity, social interactions, journal text) and uses AI/ML to detect early signs of mental health risks like depression, anxiety, and burnout. Outputs a risk score (LOW / MEDIUM / HIGH) with explanations.

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT DASHBOARD (Port 8501)              │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Check-In │  │  7-Day Trend │  │    History & Export       │  │
│  │   Form   │  │    Charts    │  │      (Plotly/CSV)         │  │
│  └────┬─────┘  └──────┬───────┘  └────────────┬─────────────┘  │
│       │               │                        │                │
└───────┼───────────────┼────────────────────────┼────────────────┘
        │ HTTP/JSON     │ GET                    │ GET
        ▼               ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Port 8000)                  │
│                                                                 │
│  POST /api/checkin ─────────────┐                               │
│                                 ▼                               │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐ │
│  │    Data       │  │    Feature        │  │   NLP Analyzer   │ │
│  │  Ingestion    │  │  Engineering      │  │  (DistilBERT)    │ │
│  │  (SQLAlchemy) │  │  (15+ features)   │  │  + Linguistics   │ │
│  └──────┬───────┘  └────────┬──────────┘  └────────┬─────────┘ │
│         │                   │                       │           │
│         ▼                   ▼                       ▼           │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐ │
│  │   SQLite DB   │  │ Anomaly Detector │  │ Risk Classifier  │ │
│  │  (SQLAlchemy)  │  │ (IsolationForest)│  │   (XGBoost)     │ │
│  └───────────────┘  └────────┬─────────┘  └────────┬─────────┘ │
│                              │                      │           │
│                              ▼                      ▼           │
│                     ┌──────────────────────────────────┐        │
│                     │     Risk Scoring Engine           │        │
│                     │  (Weighted: NLP 30% | Anomaly 25%│        │
│                     │   Sleep 18% | Mood 17% | Social  │        │
│                     │   10%) + Recommendations          │        │
│                     └──────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component          | Technology                                        |
|--------------------|---------------------------------------------------|
| Backend            | FastAPI + Uvicorn                                 |
| ML/AI              | scikit-learn, XGBoost, HuggingFace Transformers   |
| NLP Model          | distilbert-base-uncased-finetuned-sst-2-english   |
| Anomaly Detection  | Isolation Forest (scikit-learn)                   |
| Risk Classification| XGBoost Classifier                                |
| Frontend           | Streamlit + Plotly                                |
| Data Storage       | SQLite via SQLAlchemy                             |
| Language           | Python 3.10+                                      |

---

## 📁 Project Structure

```
behavioral-health-monitor/
├── backend/
│   ├── main.py                    # FastAPI app with all routes
│   ├── database.py                # SQLAlchemy models + SQLite setup
│   ├── data_ingestion.py          # Check-in logging + retrieval
│   ├── feature_engineering.py     # Feature extraction (15+ features)
│   ├── nlp_analyzer.py            # DistilBERT sentiment + linguistics
│   ├── anomaly_detector.py        # Isolation Forest anomaly detection
│   ├── risk_classifier.py         # XGBoost risk classification
│   ├── risk_engine.py             # Weighted risk scoring + recommendations
│   └── schemas.py                 # Pydantic request/response models
├── frontend/
│   └── dashboard.py               # Streamlit dashboard with Plotly charts
├── data/
│   ├── generate_synthetic_data.py # Synthetic training data generator
│   └── synthetic_training_data.csv # Generated training data (500 samples)
├── models/                        # Saved ML model files (.pkl)
├── requirements.txt               # Python dependencies
├── run.sh                         # Launch script (backend + frontend)
└── README.md                      # This file
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd behavioral-health-monitor
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate Synthetic Training Data & Train Models

```bash
python data/generate_synthetic_data.py
```

This will:
- Generate 500 labeled behavioral samples (150 LOW, 200 MEDIUM, 150 HIGH)
- Train the Isolation Forest anomaly detector
- Train the XGBoost risk classifier
- Save models to the `models/` directory

### 5. Launch the System

```bash
bash run.sh
```

Or start components individually:

```bash
# Terminal 1: Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && streamlit run dashboard.py --server.port 8501
```

### 6. Access the Application

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📡 API Endpoints

| Method | Endpoint                  | Description                          |
|--------|---------------------------|--------------------------------------|
| POST   | `/api/checkin`            | Submit daily check-in + get risk     |
| GET    | `/api/history/{user_id}`  | Get check-in history (query: days)   |
| GET    | `/api/stats/{user_id}`    | Get aggregate user statistics        |
| GET    | `/api/risk-trend/{user_id}` | Get risk score time-series         |
| DELETE | `/api/user/{user_id}`     | Delete all user data (GDPR)          |
| GET    | `/health`                 | System health check                  |

### Example Check-In Request

```bash
curl -X POST http://localhost:8000/api/checkin \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "sleep_hours": 4.5,
    "mood_score": 3,
    "activity_level": "sedentary",
    "social_interactions": 0,
    "journal_text": "I feel hopeless and exhausted. Nothing matters anymore."
  }'
```

---

## 🧪 Demo Mode

Click the **🎬 Demo Mode (High Risk)** button in the sidebar to instantly submit a pre-configured high-risk check-in. This demonstrates the full ML pipeline with a clearly concerning scenario.

---

## 🤖 ML Pipeline Details

### Feature Engineering (15+ Features)

| Category  | Features                                                      |
|-----------|---------------------------------------------------------------|
| Sleep     | avg_sleep, sleep_variance, sleep_trend, sleep_deficit_days    |
| Mood      | avg_mood, mood_trend, mood_volatility, lowest_mood            |
| Social    | avg_social, social_trend, isolation_days                      |
| Activity  | avg_activity_score, activity_trend, sedentary_days            |
| Composite | sleep_mood_correlation, behavioral_consistency_score          |

### NLP Analysis Features

- **Transformer Sentiment**: DistilBERT fine-tuned for sentiment classification
- **First-Person Ratio**: Elevated I/me/my usage (depression marker)
- **Absolutist Ratio**: Never/always/nothing usage (clinical marker)
- **Negative Emotion Words**: Depression/anxiety vocabulary frequency

### Risk Scoring Weights

| Component | Weight | Signal Source                  |
|-----------|--------|-------------------------------|
| NLP       | 30%    | Journal text sentiment + linguistics |
| Anomaly   | 25%    | Behavioral pattern deviation  |
| Sleep     | 18%    | Sleep quality and consistency |
| Mood      | 17%    | Mood level and trend          |
| Social    | 10%    | Social engagement patterns    |

---

## ⚠️ Disclaimer

**This tool is for educational and research purposes only.** It is NOT a clinical diagnostic tool. It does not provide medical advice, diagnosis, or treatment. If you are in crisis or experiencing a mental health emergency, please contact a mental health professional or call your local emergency services immediately.

**Crisis Resources:**
- 🇺🇸 988 Suicide & Crisis Lifeline: Call or text **988**
- 🇺🇸 Crisis Text Line: Text **HOME** to **741741**
- 🇬🇧 Samaritans: Call **116 123**
- 🇮🇳 iCall: Call **9152987821**

---

## 📄 License

This project is developed for academic/educational purposes as a capstone project.
# HRMS-G67
