# Sentinel — AI-Powered Mental Health Risk Monitor

> **HRMS-G67** · Educational & Research Prototype · Not a clinical tool

---

## What is Sentinel?

Think of Sentinel as a **daily health check-up for your mind**.

Every day you answer a few simple questions — how did you sleep? what's your mood today? how many people did you talk to? — and optionally write a short journal entry. Sentinel reads all of this together and tells you whether your mental health signals look **Low**, **Medium**, or **High** risk.

The key idea: **mental health problems don't appear overnight.** They drift. Sleep gets a little worse each week. You talk to fewer people. Your journal entries get darker. Sentinel watches these slow changes across multiple days and catches the drift *before* it becomes a crisis.

It also has a built-in **safety screen** — if you write something that suggests self-harm or suicidal thoughts, it immediately shows you crisis helpline numbers. This part is non-negotiable and cannot be overridden by the score.

---

## How does it work? (Simple explanation)

When you submit a check-in, Sentinel runs five things in parallel:

```
Your check-in
     │
     ├─ 1. Sleep analysis       → How bad is your sleep pattern?
     ├─ 2. Mood analysis        → Is your mood declining? How fast?
     ├─ 3. Social analysis      → How many days of isolation this week?
     ├─ 4. Journal NLP          → What emotions does your text show?
     └─ 5. Anomaly detection    → Is today unusual compared to your past?

All five scores are combined (with weights) → Final risk: LOW / MEDIUM / HIGH
```

The result also tells you **which signal is driving the score** and gives you a **personalised observation** — for example: *"You've averaged 5.2h of sleep this week, 1.8h below baseline. 4 consecutive nights of sleep deficit detected."*

---

## What's inside the project?

| Folder / File | What it does |
|---|---|
| `backend/` | FastAPI server — handles API requests and runs the ML pipeline |
| `backend/main.py` | The brain — connects everything together |
| `backend/nlp_analyzer.py` | Reads your journal and detects emotions (7 types) |
| `backend/risk_classifier.py` | XGBoost ML model that predicts risk level |
| `backend/anomaly_detector.py` | Detects if today's behavior is unusual for you |
| `backend/risk_engine.py` | Combines all scores into a final risk result |
| `backend/safety_screen.py` | Scans for crisis language — surfaces helplines immediately |
| `backend/early_warning.py` | Detects multi-day patterns (e.g. 4 declining days in a row) |
| `backend/feature_engineering.py` | Turns raw check-ins into 24 ML features |
| `frontend-web/` | React + TypeScript web app (the main UI) |
| `frontend/dashboard.py` | Streamlit dashboard (legacy, still works) |
| `data/` | Training data and trained ML models |
| `models/` | Saved ML model files |

---

## Meet the Team

This project was built by a team of five for the HRMS-G67 final year project.

### Ustav Kumar — Project Lead & Backend Engineer
Led the team and designed the overall system architecture. Built the entire FastAPI backend from scratch — all API endpoints, the database layer using SQLAlchemy/SQLite, and the startup pipeline that initialises every ML component. Implemented the weighted risk scoring engine with personalised insight generation, and wired all ML components into the end-to-end prediction flow. Also handled CORS, structured logging, and deployment scripts.

### Vikash Kumar — Machine Learning Engineer
Responsible for the core ML model pipeline. Built and trained the XGBoost multi-class risk classifier (LOW/MEDIUM/HIGH) and upgraded the NLP system from binary sentiment to a 7-class emotion detection model. Added SHAP explainability so every prediction comes with the top features that drove it. Replaced misleading training-set accuracy with 5-fold cross-validated F1 scores, and designed the blending strategy that combines rule-based and ML scores.

### Vikash Kumar — NLP, Research & Clinical Logic
Led the clinical research side of the project. Studied PHQ-9 and GAD-7 clinical depression/anxiety scales to ground the feature distributions in validated medical evidence. Built the safety screen — 75+ crisis phrases, regex-based indirect ideation patterns, and negation detection. Designed the early-warning pattern detector (mood freefall, sleep debt accumulation, multi-signal crisis, accelerating deterioration). Wrote the personalised observation text that cites the user's actual numbers in every recommendation.

### Vikash Kumar — Data Engineering & Anomaly Detection
Built the data layer and the anomaly detection system. Designed the 24-feature behavioral engineering pipeline including streak detectors (consecutive low-mood days, sleep deficit nights, social isolation runs), velocity features that catch accelerating decline, cumulative sleep debt, and the cross-signal distress score. Implemented the per-user Isolation Forest anomaly model that learns each user's own baseline after 14 days. Also designed the SQLite database schema and all data ingestion helpers. Generated the 5,000-sample synthetic training dataset using PHQ-9-aligned feature distributions.

### Vinay Kumar — Frontend & UI/UX Design
Designed and built the entire React + TypeScript web application. Created all five pages (Home, Dashboard, Solution, Resources, About), the interactive trend charts using Recharts, the check-in form with live result display, and the history log with CSV export. Implemented the dark-theme design system with Tailwind CSS and glass-morphism cards. Built the component score breakdown bars, SHAP contribution display, and early-warning cards in the check-in result. Ensured full mobile responsiveness with skeleton loaders, a hamburger menu, and accessible UI throughout.

---

## Running Locally on Windows

### What you need before starting

Make sure the following are installed on your Windows machine:

- **Python 3.10 or newer** — download from [python.org](https://www.python.org/downloads/)
  - During installation, tick ✅ **"Add Python to PATH"**
- **Node.js 18 or newer** — download from [nodejs.org](https://nodejs.org/)
- **Git** — download from [git-scm.com](https://git-scm.com/download/win)

You can check if they are installed by opening **Command Prompt** and typing:
```
python --version
node --version
git --version
```

---

### Step 1 — Download the project

Open **Command Prompt** (press `Win + R`, type `cmd`, press Enter) and run:

```cmd
git clone https://github.com/your-repo/behavioral-health-monitor.git
cd behavioral-health-monitor
```

> If you have the project as a ZIP file, just extract it and `cd` into the extracted folder.

---

### Step 2 — Set up Python environment

Create a virtual environment (this keeps the project's packages separate from the rest of your computer):

```cmd
python -m venv venv
```

Activate it:

```cmd
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your command prompt. This means the environment is active.

> **Note:** If you get a PowerShell error about "running scripts is disabled", switch to Command Prompt (cmd.exe) instead of PowerShell, or run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### Step 3 — Install Python packages

```cmd
pip install -r requirements.txt
```

This will take 5–10 minutes the first time because it downloads PyTorch, HuggingFace Transformers, XGBoost, and other packages. Go make a coffee ☕

---

### Step 4 — Generate training data and train the models

```cmd
python data\generate_synthetic_data.py
```

This creates 5,000 synthetic training samples and trains the ML models. You should see output like:

```
✅ Saved 5000 samples
CV F1-macro: 0.98 ± 0.006
✅ Done. Models saved to models/
```

> You only need to run this once. After that, the trained models are saved in the `models/` folder.

---

### Step 5 — Start the backend (FastAPI)

Open a **new Command Prompt window**, activate the environment again, and run:

```cmd
venv\Scripts\activate
cd backend
uvicorn main:app --reload --port 8000
```

Wait until you see:
```
INFO:     Application startup complete.
```

The backend is now running at **http://localhost:8000**

You can test it by opening http://localhost:8000/docs in your browser — you'll see the interactive API documentation.

---

### Step 6 — Start the frontend (React web app)

Open **another new Command Prompt window** and run:

```cmd
cd frontend-web
npm install
npm run dev
```

Wait until you see:
```
  ➜  Local:   http://localhost:5173/
```

Open **http://localhost:5173** in your browser — this is the main Sentinel web app.

---

### Step 7 (Optional) — Start the Streamlit dashboard

The Streamlit dashboard is the legacy UI with more detailed ML pipeline charts. Open **yet another Command Prompt window** and run:

```cmd
venv\Scripts\activate
cd frontend
streamlit run dashboard.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

---

### Summary — what to have running

| Service | Command | URL |
|---|---|---|
| Backend API | `uvicorn main:app --reload` (from `backend/`) | http://localhost:8000 |
| React App | `npm run dev` (from `frontend-web/`) | http://localhost:5173 |
| API Docs | (auto, no extra command) | http://localhost:8000/docs |
| Streamlit (optional) | `streamlit run dashboard.py` (from `frontend/`) | http://localhost:8501 |

---

### Troubleshooting — Windows

**Problem: `python` not found**
> Solution: Make sure Python was installed with "Add to PATH" checked. Try `py` instead of `python`.

**Problem: `venv\Scripts\activate` gives an error**
> Solution: Use Command Prompt (cmd.exe), not PowerShell. Or run: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell first.

**Problem: `pip install` fails with long error messages**
> Solution: Make sure your virtual environment is active (`(venv)` should show in the prompt). Also try: `pip install --upgrade pip` first.

**Problem: `uvicorn` not found**
> Solution: Make sure the venv is activated. Run `venv\Scripts\activate` before the uvicorn command.

**Problem: Port already in use**
> Solution: Change the port number. Example: `uvicorn main:app --reload --port 8001`

**Problem: `npm` not found**
> Solution: Install Node.js from nodejs.org. Close and reopen Command Prompt after installing.

**Problem: The NLP model download is slow**
> The emotion detection model (~330 MB) downloads automatically on the first check-in. This is normal — it only happens once and is cached after that.

---

## Running on Mac / Linux

```bash
# Clone
git clone https://github.com/your-repo/behavioral-health-monitor.git
cd behavioral-health-monitor

# Python environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate training data + train models
python data/generate_synthetic_data.py

# Terminal 1 — Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend-web && npm install && npm run dev

# Terminal 3 — Streamlit (optional)
cd frontend && streamlit run dashboard.py --server.port 8501
```

---

## API Quick Reference

### Submit a check-in

```
POST http://localhost:8000/api/checkin
Content-Type: application/json
```

```json
{
  "user_id": "user_001",
  "sleep_hours": 5.5,
  "mood_score": 3,
  "activity_level": "sedentary",
  "social_interactions": 0,
  "journal_text": "I feel really tired and disconnected today."
}
```

**Response includes:**
- `risk_level` — LOW, MEDIUM, or HIGH
- `risk_score` — a number between 0 and 1
- `component_scores` — breakdown: sleep, mood, social, journal, anomaly
- `recommendation` — personalised advice with your actual numbers
- `observations` — specific data-driven observations ("avg sleep 5.5h this week")
- `shap_contributions` — which features drove the prediction most
- `early_warnings` — multi-day pattern alerts
- `nlp_analysis` — all 7 emotion scores from your journal text

### Other endpoints

| Endpoint | What it returns |
|---|---|
| `GET /api/history/{user_id}` | Last 30 days of check-ins |
| `GET /api/stats/{user_id}` | Average risk, streak, trend direction |
| `GET /api/risk-trend/{user_id}` | Risk score over time (for charts) |
| `GET /api/early-warning/{user_id}` | Multi-day pattern warnings |
| `GET /health` | Server health check |
| `DELETE /api/user/{user_id}` | Delete all data for a user |

---

## The ML Pipeline (for the curious)

```
Daily check-in
     │
     ▼
Feature Engineering (24 features)
  • avg_sleep, sleep_debt, consecutive_low_sleep_days
  • avg_mood, mood_velocity, mood_drop_from_peak
  • avg_social, social_isolation_streak
  • behavioral_consistency_score, cross_signal_distress
  • ... and 14 more
     │
     ├──► Safety Screen (75+ phrases + regex patterns)
     │         If triggered → force HIGH + show crisis resources
     │
     ├──► NLP Emotion Analysis (DistilRoBERTa, 7 emotions)
     │         anger, disgust, fear, joy, neutral, sadness, surprise
     │
     ├──► Anomaly Detection (Isolation Forest)
     │         Personal model (per-user, after 14 days) > Population model
     │
     ├──► XGBoost Classifier (trained on 5,000 PHQ-9-aligned samples)
     │         5-fold CV F1-macro: 0.98
     │
     └──► Rule-Based Risk Engine (weighted blend)
               NLP 30% + Anomaly 25% + Sleep 18% + Mood 17% + Social 10%
               → Blended with ML score (60% rule / 40% ML)
               → Personalised observations using actual user numbers
               → SHAP contributions (top 8 driving features)
               → Early warning pattern scan (7 pattern types)
```

---

## Important Disclaimer

**Sentinel is a research and educational prototype. It is NOT a medical device and cannot diagnose, treat, or prevent any mental health condition.**

The risk scores are based on patterns in self-reported data and synthetic training data — they are not clinically validated. Do not use Sentinel as a substitute for professional mental health care.

**If you or someone you know is in crisis, please contact:**
- iCall (India): 9152987821
- AASRA (India): 9820466627 (24/7)
- 988 Suicide & Crisis Lifeline (US): call or text 988
- Samaritans (UK): 116 123 (24/7)

---

*Sentinel — HRMS-G67 · Built with FastAPI, XGBoost, HuggingFace Transformers, React, Tailwind CSS*
