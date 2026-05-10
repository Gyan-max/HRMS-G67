"""
dashboard.py — Streamlit-based frontend for the Behavioral Health Risk Monitor.

A full-featured interactive dashboard with:
  - Daily check-in form with sliders, selectors, and journal text area
  - Real-time risk assessment display with colored badges
  - Component score breakdown charts (Plotly)
  - 7-day trend visualizations (mood, sleep, social, risk)
  - Historical data table with CSV export
  - Demo mode for instant high-risk demonstration
  - Crisis resources expander
"""

import datetime
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ===========================================================================
# CONFIGURATION
# ===========================================================================
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="🧠 BH Risk Monitor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for premium dark-friendly styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* Risk badge styles */
    .risk-badge {
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        font-size: 1.4rem;
        font-weight: 700;
        margin: 10px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .risk-high {
        background: linear-gradient(135deg, rgba(255,68,68,0.2), rgba(255,68,68,0.05));
        border: 2px solid #ff4444;
        color: #ff6666;
    }
    .risk-medium {
        background: linear-gradient(135deg, rgba(255,170,0,0.2), rgba(255,170,0,0.05));
        border: 2px solid #ffaa00;
        color: #ffcc44;
    }
    .risk-low {
        background: linear-gradient(135deg, rgba(0,204,102,0.2), rgba(0,204,102,0.05));
        border: 2px solid #00cc66;
        color: #44dd88;
    }

    /* Recommendation box */
    .rec-box {
        padding: 16px 20px;
        border-radius: 12px;
        margin: 12px 0;
        font-size: 0.95rem;
        line-height: 1.6;
        backdrop-filter: blur(10px);
    }
    .rec-high {
        background: rgba(255,68,68,0.08);
        border-left: 4px solid #ff4444;
        color: #ffaaaa;
    }
    .rec-medium {
        background: rgba(255,170,0,0.08);
        border-left: 4px solid #ffaa00;
        color: #ffdd88;
    }
    .rec-low {
        background: rgba(0,204,102,0.08);
        border-left: 4px solid #00cc66;
        color: #88eebb;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 16px;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }

    /* Footer disclaimer */
    .disclaimer {
        padding: 16px;
        margin-top: 40px;
        border-radius: 12px;
        background: rgba(255,170,0,0.06);
        border: 1px solid rgba(255,170,0,0.15);
        font-size: 0.82rem;
        color: #aaa;
        text-align: center;
    }

    /* Onboarding card */
    .onboard-card {
        padding: 40px;
        border-radius: 16px;
        background: rgba(255,255,255,0.03);
        border: 1px dashed rgba(255,255,255,0.15);
        text-align: center;
        margin: 30px 0;
    }
</style>
""", unsafe_allow_html=True)


# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================

def api_call(method: str, endpoint: str, **kwargs):
    """
    Make an HTTP request to the FastAPI backend with error handling.

    Args:
        method: HTTP method ("get", "post", "delete").
        endpoint: API endpoint path (e.g., "/api/checkin").
        **kwargs: Additional arguments passed to requests.

    Returns:
        Parsed JSON response or None on error.
    """
    url = f"{API_BASE_URL}{endpoint}"
    try:
        resp = getattr(requests, method)(url, timeout=60, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to the backend server. Is it running on port 8000?")
        return None
    except requests.exceptions.Timeout:
        st.error("⏳ Request timed out. The server might be loading ML models — please wait and retry.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"🚫 Server error: {e.response.status_code} — {e.response.text[:200]}")
        return None
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {str(e)}")
        return None


def get_risk_class(level: str) -> str:
    """Map risk level to CSS class name."""
    return {"HIGH": "risk-high", "MEDIUM": "risk-medium", "LOW": "risk-low"}.get(level, "risk-low")


def get_rec_class(level: str) -> str:
    """Map risk level to recommendation CSS class."""
    return {"HIGH": "rec-high", "MEDIUM": "rec-medium", "LOW": "rec-low"}.get(level, "rec-low")


# ===========================================================================
# PLOTLY CHART THEME (dark-friendly)
# ===========================================================================

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#cccccc", family="Inter, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)"),
)


# ===========================================================================
# SIDEBAR
# ===========================================================================

with st.sidebar:
    st.markdown("## 🧠 BH Risk Monitor")
    st.markdown("---")

    # User ID input
    user_id = st.text_input(
        "👤 User ID",
        value="user_001",
        help="Enter your unique user identifier",
    )

    st.markdown("---")

    # ------------------------------------------------------------------
    # Daily Check-In Form
    # ------------------------------------------------------------------
    with st.expander("📝 Daily Check-In Form", expanded=True):
        sleep_hours = st.slider(
            "😴 Sleep Hours",
            min_value=0.0, max_value=12.0, value=7.0, step=0.5,
            help="How many hours did you sleep last night?",
        )

        mood_score = st.slider(
            "🎭 Mood Score",
            min_value=1, max_value=10, value=6,
            help="Rate your overall mood today (1=worst, 10=best)",
        )

        activity_level = st.selectbox(
            "🏃 Activity Level",
            options=["sedentary", "light", "moderate", "active"],
            index=1,
            help="How physically active were you today?",
        )

        social_interactions = st.number_input(
            "🤝 Social Interactions",
            min_value=0, max_value=30, value=3,
            help="Count of meaningful conversations or social contacts today",
        )

        journal_text = st.text_area(
            "📓 Journal Entry",
            placeholder="Write anything about your day, how you're feeling, what's on your mind...",
            height=120,
            help="Optional — used for NLP-based sentiment analysis",
        )

        # Submit button
        submitted = st.button("🚀 Submit Check-In", type="primary", use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Demo Mode — Pre-fill with high-risk test case
    # ------------------------------------------------------------------
    demo_mode = st.button(
        "🎬 Demo Mode (High Risk)",
        use_container_width=True,
        help="Pre-fills the form with a high-risk scenario for demonstration",
    )

    if demo_mode:
        # Submit a high-risk check-in directly
        demo_payload = {
            "user_id": user_id,
            "sleep_hours": 3.5,
            "mood_score": 2,
            "activity_level": "sedentary",
            "social_interactions": 0,
            "journal_text": (
                "I can't sleep at all. Everything feels meaningless and hopeless. "
                "I'm completely alone and nothing ever gets better. I'm so tired "
                "of feeling worthless and empty. I never want to talk to anyone."
            ),
        }
        with st.spinner("🔄 Running high-risk demo assessment..."):
            demo_result = api_call("post", "/api/checkin", json=demo_payload)
        if demo_result:
            st.session_state["latest_result"] = demo_result
            st.success("✅ Demo check-in submitted!")
            st.rerun()

    # Days tracked badge
    stats = api_call("get", f"/api/stats/{user_id}")
    if stats:
        st.metric("📅 Days Tracked", stats.get("total_days", 0))

    st.markdown("---")

    # Crisis resources
    with st.expander("⚠️ Crisis Resources"):
        st.markdown("""
        **If you are in crisis, please reach out:**

        🇺🇸 **988 Suicide & Crisis Lifeline**: Call or text **988**

        🇺🇸 **Crisis Text Line**: Text **HOME** to **741741**

        🇬🇧 **Samaritans**: Call **116 123**

        🇮🇳 **iCall**: Call **9152987821**

        🇮🇳 **Vandrevala Foundation**: **1860-2662-345**

        🌍 **International Association for Suicide Prevention**:
        [https://www.iasp.info/resources/Crisis_Centres/](https://www.iasp.info/resources/Crisis_Centres/)
        """)


# ===========================================================================
# PROCESS CHECK-IN SUBMISSION
# ===========================================================================

if submitted:
    payload = {
        "user_id": user_id,
        "sleep_hours": sleep_hours,
        "mood_score": mood_score,
        "activity_level": activity_level,
        "social_interactions": social_interactions,
        "journal_text": journal_text if journal_text else None,
    }
    with st.spinner("🔄 Analyzing your check-in with AI models..."):
        result = api_call("post", "/api/checkin", json=payload)
    if result:
        st.session_state["latest_result"] = result
        st.rerun()


# ===========================================================================
# MAIN CONTENT — TABS
# ===========================================================================

st.markdown("# 🧠 Behavioral Health Risk Monitor")
st.markdown("*AI-powered early detection of mental health risk patterns*")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Today's Assessment", "📈 7-Day Trends", "📋 History Log"])


# ===========================================================================
# TAB 1: TODAY'S ASSESSMENT
# ===========================================================================
with tab1:
    result = st.session_state.get("latest_result")

    if result:
        risk_level = result.get("risk_level", "LOW")
        risk_score = result.get("risk_score", 0.0)
        component_scores = result.get("component_scores", {})
        recommendation = result.get("recommendation", "")
        nlp_analysis = result.get("nlp_analysis", {})
        anomaly_detected = result.get("anomaly_detected", False)
        dominant_factor = result.get("dominant_factor", "N/A")
        color_code = result.get("color_code", "#00cc66")

        # ---------------------------------------------------------------
        # Risk Badge (centered, large)
        # ---------------------------------------------------------------
        badge_class = get_risk_class(risk_level)
        st.markdown(
            f'<div class="risk-badge {badge_class}">'
            f'⚡ Risk Level: {risk_level} — Score: {risk_score:.2f}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------------
        # Key metrics row
        # ---------------------------------------------------------------
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎯 Risk Level", risk_level)
        with col2:
            st.metric("📊 Risk Score", f"{risk_score:.3f}")
        with col3:
            st.metric("🔑 Dominant Factor", dominant_factor.upper())
        with col4:
            anomaly_icon = "🚨 YES" if anomaly_detected else "✅ NO"
            st.metric("🔍 Anomaly Detected", anomaly_icon)

        st.markdown("---")

        # ---------------------------------------------------------------
        # Component Scores — Horizontal Bar Chart
        # ---------------------------------------------------------------
        st.subheader("📊 Component Risk Scores")

        if component_scores:
            components = list(component_scores.keys())
            scores = list(component_scores.values())

            # Color based on score magnitude
            colors = []
            for s in scores:
                if s >= 0.65:
                    colors.append("#ff4444")
                elif s >= 0.35:
                    colors.append("#ffaa00")
                else:
                    colors.append("#00cc66")

            fig = go.Figure(go.Bar(
                x=scores,
                y=[c.upper() for c in components],
                orientation="h",
                marker=dict(
                    color=colors,
                    line=dict(width=0),
                    opacity=0.85,
                ),
                text=[f"{s:.2f}" for s in scores],
                textposition="outside",
                textfont=dict(color="#cccccc", size=13),
            ))
            fig.update_layout(**PLOTLY_LAYOUT)
            fig.update_layout(
                height=300,
                xaxis=dict(
                    range=[0, 1.1],
                    title="Risk Score (0 = Low, 1 = High)",
                    gridcolor="rgba(255,255,255,0.06)",
                ),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                title=dict(text="Risk Component Breakdown", font=dict(size=16)),
            )
            # Add threshold reference lines
            fig.add_vline(x=0.65, line_dash="dash", line_color="rgba(255,68,68,0.4)",
                          annotation_text="HIGH", annotation_font_color="#ff6666")
            fig.add_vline(x=0.35, line_dash="dash", line_color="rgba(255,170,0,0.4)",
                          annotation_text="MEDIUM", annotation_font_color="#ffcc44")

            st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------------------
        # Recommendation
        # ---------------------------------------------------------------
        st.subheader("💡 Recommendation")
        rec_class = get_rec_class(risk_level)
        st.markdown(
            f'<div class="rec-box {rec_class}">{recommendation}</div>',
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------------
        # NLP Analysis (expandable)
        # ---------------------------------------------------------------
        with st.expander("🔬 NLP Journal Analysis", expanded=False):
            if nlp_analysis.get("status") == "no_journal":
                st.info("ℹ️ No journal text was provided for this check-in.")
            else:
                ncol1, ncol2, ncol3, ncol4 = st.columns(4)
                with ncol1:
                    st.metric("Sentiment", nlp_analysis.get("sentiment_label", "N/A"))
                with ncol2:
                    st.metric("Confidence", f"{nlp_analysis.get('sentiment_confidence', 0):.2%}")
                with ncol3:
                    st.metric("NLP Risk", f"{nlp_analysis.get('nlp_risk_score', 0):.3f}")
                with ncol4:
                    st.metric("Word Count", nlp_analysis.get("text_length", 0))

                st.markdown("##### Linguistic Markers")
                lcol1, lcol2, lcol3 = st.columns(3)
                with lcol1:
                    st.metric("1st Person Ratio", f"{nlp_analysis.get('first_person_ratio', 0):.3f}")
                with lcol2:
                    st.metric("Absolutist Ratio", f"{nlp_analysis.get('absolutist_ratio', 0):.3f}")
                with lcol3:
                    st.metric("Neg. Emotion Ratio", f"{nlp_analysis.get('negative_emotion_ratio', 0):.3f}")

        # Anomaly status
        if anomaly_detected:
            st.warning(
                "🚨 **Behavioral Anomaly Detected** — Your recent patterns deviate "
                "significantly from your established baseline. This doesn't necessarily "
                "mean something is wrong, but it's worth reflecting on recent changes."
            )

    else:
        # Onboarding message for new users
        st.markdown(
            '<div class="onboard-card">'
            "<h2>👋 Welcome to the Behavioral Health Risk Monitor</h2>"
            "<p style='font-size:1.1rem; color:#aaa;'>"
            "Submit your first daily check-in using the form in the sidebar "
            "to receive your personalized AI-powered risk assessment."
            "</p>"
            "<p style='font-size:0.95rem; color:#888;'>"
            "💡 <strong>Tip:</strong> Click the <strong>🎬 Demo Mode</strong> button "
            "in the sidebar to see a high-risk assessment example instantly."
            "</p>"
            "</div>",
            unsafe_allow_html=True,
        )


# ===========================================================================
# TAB 2: 7-DAY TRENDS
# ===========================================================================
with tab2:
    st.subheader("📈 7-Day Behavioral Trends")

    history = api_call("get", f"/api/history/{user_id}?days=7")

    if history and history.get("total_records", 0) > 0:
        records = history["records"]
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # ---------------------------------------------------------------
        # Mood Score Trend
        # ---------------------------------------------------------------
        fig_mood = go.Figure()
        fig_mood.add_trace(go.Scatter(
            x=df["timestamp"], y=df["mood_score"],
            mode="lines+markers",
            name="Mood Score",
            line=dict(color="#6c63ff", width=3),
            marker=dict(size=10, symbol="circle"),
            fill="tozeroy",
            fillcolor="rgba(108,99,255,0.1)",
        ))
        fig_mood.update_layout(**PLOTLY_LAYOUT)
        fig_mood.update_layout(
            title=dict(text="🎭 Mood Score (1-10)", font=dict(size=16)),
            yaxis=dict(range=[0, 11], gridcolor="rgba(255,255,255,0.06)"),
            height=320,
        )
        st.plotly_chart(fig_mood, use_container_width=True)

        # ---------------------------------------------------------------
        # Sleep Hours Trend with reference line
        # ---------------------------------------------------------------
        fig_sleep = go.Figure()
        fig_sleep.add_trace(go.Scatter(
            x=df["timestamp"], y=df["sleep_hours"],
            mode="lines+markers",
            name="Sleep Hours",
            line=dict(color="#00bcd4", width=3),
            marker=dict(size=10, symbol="diamond"),
            fill="tozeroy",
            fillcolor="rgba(0,188,212,0.1)",
        ))
        # 7-hour recommended minimum reference line
        fig_sleep.add_hline(
            y=7, line_dash="dash", line_color="rgba(0,204,102,0.5)",
            annotation_text="7hr minimum",
            annotation_font_color="#44dd88",
        )
        fig_sleep.update_layout(**PLOTLY_LAYOUT)
        fig_sleep.update_layout(
            title=dict(text="😴 Sleep Hours (0-12)", font=dict(size=16)),
            yaxis=dict(range=[0, 13], gridcolor="rgba(255,255,255,0.06)"),
            height=320,
        )
        st.plotly_chart(fig_sleep, use_container_width=True)

        # ---------------------------------------------------------------
        # Social Interactions Bar Chart
        # ---------------------------------------------------------------
        fig_social = go.Figure()
        bar_colors = ["#ff4444" if v <= 1 else "#ffaa00" if v <= 3 else "#00cc66"
                       for v in df["social_interactions"]]
        fig_social.add_trace(go.Bar(
            x=df["timestamp"], y=df["social_interactions"],
            name="Social Interactions",
            marker=dict(color=bar_colors, opacity=0.85),
            text=df["social_interactions"],
            textposition="outside",
            textfont=dict(color="#cccccc"),
        ))
        fig_social.update_layout(**PLOTLY_LAYOUT)
        fig_social.update_layout(
            title=dict(text="🤝 Social Interactions Per Day", font=dict(size=16)),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            height=320,
        )
        st.plotly_chart(fig_social, use_container_width=True)

        # ---------------------------------------------------------------
        # Risk Score Trend with color zones
        # ---------------------------------------------------------------
        risk_df = df[df["risk_score"].notna()].copy()
        if len(risk_df) > 0:
            fig_risk = go.Figure()

            # Color zone backgrounds
            fig_risk.add_hrect(y0=0.65, y1=1.0, fillcolor="rgba(255,68,68,0.08)",
                               line_width=0, annotation_text="HIGH RISK",
                               annotation_font_color="rgba(255,68,68,0.5)")
            fig_risk.add_hrect(y0=0.35, y1=0.65, fillcolor="rgba(255,170,0,0.06)",
                               line_width=0, annotation_text="MEDIUM",
                               annotation_font_color="rgba(255,170,0,0.5)")
            fig_risk.add_hrect(y0=0.0, y1=0.35, fillcolor="rgba(0,204,102,0.06)",
                               line_width=0, annotation_text="LOW",
                               annotation_font_color="rgba(0,204,102,0.5)")

            fig_risk.add_trace(go.Scatter(
                x=risk_df["timestamp"], y=risk_df["risk_score"],
                mode="lines+markers",
                name="Risk Score",
                line=dict(color="#ff6b6b", width=3),
                marker=dict(size=10, symbol="star"),
            ))
            fig_risk.update_layout(**PLOTLY_LAYOUT)
            fig_risk.update_layout(
                title=dict(text="⚡ Risk Score Trend (0-1)", font=dict(size=16)),
                yaxis=dict(range=[0, 1.05], gridcolor="rgba(255,255,255,0.06)"),
                height=350,
            )
            st.plotly_chart(fig_risk, use_container_width=True)
    else:
        st.info("📝 No check-in data available yet. Submit your first check-in to see trends!")


# ===========================================================================
# TAB 3: HISTORY LOG
# ===========================================================================
with tab3:
    st.subheader("📋 Check-In History (Last 30 Days)")

    history_30 = api_call("get", f"/api/history/{user_id}?days=30")

    if history_30 and history_30.get("total_records", 0) > 0:
        records = history_30["records"]
        df_hist = pd.DataFrame(records)
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])

        # Summary stats row
        scol1, scol2, scol3, scol4 = st.columns(4)
        with scol1:
            avg_risk = df_hist["risk_score"].mean() if df_hist["risk_score"].notna().any() else 0
            st.metric("📊 Avg Risk Score", f"{avg_risk:.3f}")
        with scol2:
            st.metric("📅 Total Days", len(df_hist))
        with scol3:
            # Compute LOW risk streak
            streak = 0
            for _, row in df_hist.sort_values("timestamp", ascending=False).iterrows():
                if row.get("risk_level") == "LOW":
                    streak += 1
                else:
                    break
            st.metric("🔥 LOW Risk Streak", f"{streak} days")
        with scol4:
            avg_mood = df_hist["mood_score"].mean() if "mood_score" in df_hist else 0
            st.metric("🎭 Avg Mood", f"{avg_mood:.1f}")

        st.markdown("---")

        # Display table
        display_cols = [
            "timestamp", "sleep_hours", "mood_score", "activity_level",
            "social_interactions", "risk_score", "risk_level",
        ]
        available_display = [c for c in display_cols if c in df_hist.columns]
        df_display = df_hist[available_display].copy()
        df_display["timestamp"] = df_display["timestamp"].dt.strftime("%Y-%m-%d %H:%M")

        # Color-code risk levels
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            height=400,
        )

        # CSV download
        csv_data = df_hist.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"health_history_{user_id}_{datetime.date.today()}.csv",
            mime="text/csv",
        )
    else:
        st.info("📝 No history data available yet. Start checking in to build your history!")


# ===========================================================================
# FOOTER DISCLAIMER
# ===========================================================================
st.markdown("---")
st.markdown(
    '<div class="disclaimer">'
    "⚠️ <strong>Disclaimer:</strong> This tool is for educational and research purposes only "
    "and is <strong>NOT</strong> a clinical diagnostic tool. It does not provide medical advice, "
    "diagnosis, or treatment. If you are in crisis or experiencing a mental health emergency, "
    "please contact a mental health professional or call your local emergency services immediately."
    "</div>",
    unsafe_allow_html=True,
)
