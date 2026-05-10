---
name: testing-bhrm-dashboard
description: Boot, exercise, and verify the Behavioral Health Risk Monitor (BHRM) backend + Streamlit dashboard end-to-end. Use whenever validating safety-screen, risk-engine, or dashboard changes.
---

# Testing the BHRM dashboard end-to-end

This repo is a FastAPI + Streamlit + ML behavioral-health risk monitor. End-to-end tests should exercise the **dashboard UI** (sidebar form → assessment tab) rather than just the API, because the safety-banner UX is part of the contract.

## Devin secrets needed

None — the app runs fully locally with no external auth. All ML models are bundled or downloaded on first boot.

## Local boot sequence

From repo root:

```bash
# 1) Install dev deps (only the first time, or after requirements changes)
pip install -r requirements-dev.txt

# 2) Start the FastAPI backend on :8000
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log &
# Wait ~10–20 s for DistilBERT to load. Health check: curl http://127.0.0.1:8000/health

# 3) Start Streamlit on :8501
streamlit run frontend/dashboard.py --server.port 8501 --server.headless true --browser.gatherUsageStats false &
# Wait ~3 s, then open http://localhost:8501
```

Both endpoints respond `200` once warm. The frontend reads `BHRM_API_BASE_URL` (default `http://localhost:8000`) and the backend reads `BHRM_CORS_ORIGINS` (default `http://localhost:8501,http://127.0.0.1:8501`).

## Three canonical end-to-end test cases

Use a fresh `User ID` for each so the per-user history doesn't pollute results. Pick ones that don't already exist in `data/health_monitor.db` — the `Days Tracked` counter in the sidebar should read `0` before submission.

| # | User ID | Sleep | Mood | Activity | Social | Journal | Expected |
|---|---|---|---|---|---|---|---|
| 1 | `e2e_benign` | 8.0 | 8 | moderate | 5 | `Today was great. I had coffee with a friend and felt grateful.` | LOW, score ≤ 0.20, no crisis banner |
| 2 | `e2e_empty` | 3.5 | 2 | sedentary | 0 | _empty_ | MEDIUM, score ≥ 0.50, no banner, NLP bar = 0.00, sleep/mood/social bars red |
| 3 | `e2e_safety` | 8.0 | 8 | moderate | 5 | `I want to die. I cannot go on like this anymore.` | HIGH, score = 0.650, **safety_override = true**, **dominant_factor = safety**, crisis banner above badge with 4 helplines, recommendation does NOT echo the matched phrase back |

Test 2 is the regression case for weight re-normalisation: pre-fix this scored ~0.42 because 30% of weight was forced to zero when NLP was unavailable.

Test 3 is the safety-pathway case. The journal must contain a phrase from `SUICIDAL_IDEATION_PHRASES` in `backend/safety_screen.py`. Negated forms (`I would never want to die`) must NOT trigger — that's a precision regression test worth running via curl.

## Streamlit sidebar quirks

- **Sliders**: clicking on the slider track jumps the handle to that x-position (which is rarely what you want). Better: click the existing handle, then use Left/Right arrow keys for fine adjustments. Step is `0.5` for sleep and `1` for mood.
- **Number input**: `social_interactions` accepts triple-click + type. The `−` button is disabled at value `0`.
- **Activity dropdown**: click the visible select, then click the option label in the popup. Options: `sedentary`, `light`, `moderate`, `active`.
- **Journal textarea**: triple-click + Delete clears it. Don't press Ctrl+Enter — Streamlit submits immediately.
- **User ID input**: triple-click + type to overwrite. Press Tab to commit.
- **Days Tracked = 0** confirms the user is fresh.

## Quick API smoke-test (pre-recording)

Run this before booting the GUI to confirm the backend is sound:

```bash
for user in benign safety empty negated; do
  case $user in
    benign)  payload='{"user_id":"smoke_'"$user"'","sleep_hours":8.0,"mood_score":8,"activity_level":"moderate","social_interactions":5,"journal_text":"Today was great. I had coffee with a friend."}' ;;
    safety)  payload='{"user_id":"smoke_'"$user"'","sleep_hours":8.0,"mood_score":8,"activity_level":"moderate","social_interactions":5,"journal_text":"I want to die. I cannot go on."}' ;;
    empty)   payload='{"user_id":"smoke_'"$user"'","sleep_hours":3.5,"mood_score":2,"activity_level":"sedentary","social_interactions":0,"journal_text":null}' ;;
    negated) payload='{"user_id":"smoke_'"$user"'","sleep_hours":7.0,"mood_score":7,"activity_level":"moderate","social_interactions":4,"journal_text":"I would never want to die."}' ;;
  esac
  echo "=== $user ==="
  curl -s -X POST http://127.0.0.1:8000/api/checkin -H 'Content-Type: application/json' -d "$payload" \
    | python -c 'import json,sys;r=json.load(sys.stdin);print(r["risk_level"], r["risk_score"], r["safety_override"], r["dominant_factor"])'
done
```

Expected outputs (rounded):

```
benign  LOW    0.10 False anomaly
safety  HIGH   0.65 True  safety
empty   MEDIUM 0.56 False sleep
negated LOW    ...  False ...
```

If any of these don't match, troubleshoot the backend before recording the GUI.

## Unit tests

```bash
pytest tests/ -v
```

59 tests, < 1 s. Tests are offline-safe — `tests/conftest.py` monkey-patches the HuggingFace `pipeline` so no model downloads happen.

## When the test plan can't be triggered

- If the demo-mode button doesn't show a crisis banner, the demo journal text in `frontend/dashboard.py` may not contain a phrase from `SUICIDAL_IDEATION_PHRASES`. As of PR #1 the demo text uses absolutist language ("hopeless", "alone", "worthless") which trips weighted scoring but NOT the safety screen — so the demo button alone is insufficient evidence of the safety pathway. Always do a manual check-in with explicit self-harm phrasing for the safety override test.
- If a check-in stays LOW despite severe inputs, check that the `BHRM_API_BASE_URL` is reachable from Streamlit and that the backend's `/api/checkin` returns 200 (sometimes the backend is up but DistilBERT is still loading on first request).
- If no PR has CI, only CodeRabbit (optional review bot) is registered — `git pr_checks` will report 0 passed / 0 failed / 1 pending and that's expected.

## What to record

The primary visual evidence is the crisis-banner-above-badge transition. Record:
1. Test 1 (benign) submission → no banner, LOW.
2. Test 2 (empty journal high-stress) submission → no banner, MEDIUM with red sleep/mood/social bars and NLP bar at exactly 0.00.
3. Test 3 (self-harm) submission → red crisis banner appears above the badge with 4 helplines, dominant factor SAFETY, score 0.650.

Maximize the browser before recording: `wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz`.
