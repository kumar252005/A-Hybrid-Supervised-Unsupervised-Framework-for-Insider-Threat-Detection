from pathlib import Path

import pandas as pd
import networkx as nx
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DASHBOARD_DIR = ROOT_DIR / "dashboard"
ACTION_LOG_PATH = DATA_DIR / "user_actions.csv"

st.set_page_config(
    page_title="Insider Threat Command Center",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --bg: #0b1017;
        --panel: rgba(18, 25, 35, 0.94);
        --panel-soft: rgba(255, 255, 255, 0.055);
        --line: rgba(180, 198, 220, 0.16);
        --text: #eff5fb;
        --muted: #a8b6c7;
        --accent: #5fb3ff;
        --accent-2: #36d399;
        --danger: #ff5c6c;
        --warning: #f6c453;
    }
    .stApp {
        background:
            linear-gradient(180deg, rgba(17, 26, 38, 0.94), rgba(8, 12, 18, 1) 420px),
            var(--bg);
        color: var(--text);
        font-family: "Inter", "Segoe UI", Arial, sans-serif;
    }
    [data-testid="stHeader"] {
        background: rgba(11, 16, 23, 0.86);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--line);
    }
    .block-container {
        max-width: 1440px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3 {
        color: var(--text);
        letter-spacing: 0;
    }
    p, label, span {
        letter-spacing: 0;
    }
    .site-shell {
        border: 1px solid var(--line);
        border-radius: 8px;
        background:
            linear-gradient(135deg, rgba(95, 179, 255, 0.12), transparent 34%),
            linear-gradient(180deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
        padding: 22px 24px;
        margin-bottom: 18px;
        box-shadow: 0 18px 50px rgba(0,0,0,0.24);
    }
    .site-kicker {
        color: var(--accent-2);
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .site-title {
        font-size: 34px;
        font-weight: 760;
        margin: 0;
        color: #f6f9ff;
    }
    .site-subtitle {
        max-width: 900px;
        color: var(--muted);
        margin: 8px 0 0;
        font-size: 15px;
    }
    .site-meta {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 16px;
    }
    .meta-chip {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 7px 10px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.055);
        color: #dfeaf6;
        font-size: 12px;
    }
    .section-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--panel);
        padding: 18px;
        margin: 12px 0 18px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.18);
    }
    .section-title {
        margin: 0 0 4px;
        color: #f5f8fc;
        font-size: 20px;
        font-weight: 720;
    }
    .section-copy {
        color: var(--muted);
        margin: 0 0 14px;
        font-size: 14px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 1px solid var(--line);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        color: var(--muted);
        background: rgba(255,255,255,0.035);
        border: 1px solid transparent;
        padding: 10px 14px;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff;
        background: rgba(95,179,255,0.12);
        border-color: var(--line);
    }
    div[data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 14px 16px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.18);
    }
    div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #f6f9ff;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        background: var(--panel);
    }
    div[data-testid="stAlert"] {
        border-radius: 8px;
    }
    .stSelectbox, .stMultiSelect, .stSlider, .stToggle {
        color: var(--text);
    }
    .live-hero {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(95, 179, 255, 0.28);
        border-radius: 8px;
        padding: 22px 24px;
        margin: 6px 0 18px;
        background:
            linear-gradient(135deg, rgba(28, 39, 55, 0.98), rgba(14, 20, 29, 0.98));
        box-shadow: 0 18px 50px rgba(0,0,0,0.26);
    }
    .live-hero:before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(110deg, transparent 0%, rgba(91, 188, 255, 0.16) 48%, transparent 56%);
        animation: sweep 4.5s linear infinite;
    }
    .live-hero h2, .live-hero p, .live-hero .hero-row {
        position: relative;
        z-index: 1;
    }
    .live-hero h2 {
        margin: 0;
        font-size: 30px;
        letter-spacing: 0;
    }
    .live-hero p {
        margin: 8px 0 0;
        color: var(--muted);
    }
    .hero-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 16px;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 11px;
        border-radius: 999px;
        background: rgba(255,255,255,0.06);
        border: 1px solid var(--line);
        color: #e9f2ff;
        font-size: 13px;
    }
    .pulse-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #40f29a;
        box-shadow: 0 0 0 rgba(64, 242, 154, 0.7);
        animation: pulse 1.6s infinite;
    }
    .alert-strip {
        height: 44px;
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: rgba(0,0,0,0.22);
        margin: 10px 0 18px;
    }
    .ticker {
        white-space: nowrap;
        display: inline-block;
        padding: 11px 0;
        animation: ticker 32s linear infinite;
        color: #f7fbff;
    }
    .ticker span {
        display: inline-block;
        margin-right: 34px;
    }
    .risk-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        gap: 12px;
        margin: 12px 0 18px;
    }
    .risk-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 14px;
        background: var(--panel);
        box-shadow: 0 12px 28px rgba(0,0,0,0.16);
    }
    .risk-card strong {
        display: block;
        font-size: 24px;
        margin-top: 4px;
    }
    .risk-card span {
        color: var(--muted);
        font-size: 13px;
    }
    .risk-card.critical { border-color: rgba(255, 92, 108, 0.62); box-shadow: 0 0 28px rgba(255, 92, 108, 0.12); }
    .risk-card.warning { border-color: rgba(246, 196, 83, 0.62); box-shadow: 0 0 28px rgba(246, 196, 83, 0.10); }
    .risk-card.normal { border-color: rgba(54, 211, 153, 0.56); box-shadow: 0 0 28px rgba(54, 211, 153, 0.10); }
    .radar-wrap {
        position: relative;
        height: 260px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid rgba(120, 196, 255, 0.25);
        background:
            repeating-radial-gradient(circle at center, rgba(112, 202, 255, 0.16) 0 1px, transparent 1px 42px),
            linear-gradient(135deg, rgba(18, 30, 42, 0.98), rgba(10, 15, 23, 0.98));
    }
    .radar-wrap:before {
        content: "";
        position: absolute;
        inset: -50%;
        background: conic-gradient(from 0deg, rgba(80, 200, 255, 0.0), rgba(80, 200, 255, 0.28), rgba(80, 200, 255, 0.0) 28%);
        animation: radar 4s linear infinite;
    }
    .radar-label {
        position: absolute;
        left: 18px;
        top: 16px;
        color: #dcecff;
        font-weight: 700;
    }
    .radar-user {
        position: absolute;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #54d4ff;
        box-shadow: 0 0 14px #54d4ff;
        border: 0;
        padding: 0;
        cursor: pointer;
        outline: none;
    }
    .radar-user.high {
        width: 14px;
        height: 14px;
        background: #ff5757;
        box-shadow: 0 0 20px #ff5757;
        animation: pulse 1.35s infinite;
    }
    .radar-user .radar-tooltip {
        position: absolute;
        left: 16px;
        top: -14px;
        min-width: 150px;
        padding: 8px 10px;
        border-radius: 8px;
        background: rgba(5, 10, 18, 0.96);
        border: 1px solid rgba(139, 211, 255, 0.48);
        color: #f7fbff;
        font-size: 12px;
        line-height: 1.35;
        text-align: left;
        box-shadow: 0 12px 24px rgba(0,0,0,0.35);
        opacity: 0;
        pointer-events: none;
        transform: translateY(4px);
        transition: opacity 140ms ease, transform 140ms ease;
        z-index: 4;
    }
    .radar-user:focus .radar-tooltip,
    .radar-user:hover .radar-tooltip {
        opacity: 1;
        transform: translateY(0);
    }
    .radar-user:focus {
        box-shadow: 0 0 0 4px rgba(84, 212, 255, 0.24), 0 0 18px #54d4ff;
    }
    @keyframes sweep {
        from { transform: translateX(-100%); }
        to { transform: translateX(100%); }
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(64, 242, 154, 0.65); transform: scale(1); }
        70% { box-shadow: 0 0 0 12px rgba(64, 242, 154, 0); transform: scale(1.08); }
        100% { box-shadow: 0 0 0 0 rgba(64, 242, 154, 0); transform: scale(1); }
    }
    @keyframes ticker {
        from { transform: translateX(100%); }
        to { transform: translateX(-100%); }
    }
    @keyframes radar {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    @media (max-width: 760px) {
        .site-title { font-size: 26px; }
        .live-hero h2 { font-size: 24px; }
        .block-container { padding-left: 1rem; padding-right: 1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_all_data():
    features = pd.read_csv(DATA_DIR / "merged_features.csv")
    scores = pd.read_csv(DATA_DIR / "anomaly_scores.csv")
    logins = pd.read_csv(DATA_DIR / "logins.csv", parse_dates=["login", "logout"])
    file_access = pd.read_csv(DATA_DIR / "file_access.csv", parse_dates=["access_time"])
    usb_usage = pd.read_csv(DATA_DIR / "usb_usage.csv", parse_dates=["plug_time", "unplug_time"])
    emails = pd.read_csv(DATA_DIR / "emails.csv", parse_dates=["time"])
    return features, scores, logins, file_access, usb_usage, emails

features, scores, logins, file_access, usb_usage, emails = load_all_data()
feature_columns = [column for column in features.columns if column != "is_red_team"]
df = features[feature_columns].merge(scores, on="user", how="inner")
score_options = [
    "hybrid_score",
    "supervised_probability",
    "unsupervised_ensemble",
    "isolation_forest",
    "oneclass_svm",
    "autoencoder",
]
available_score_options = [c for c in score_options if c in scores.columns]

if "analyst_logged_in" not in st.session_state:
    st.session_state.analyst_logged_in = False
if "analyst_name" not in st.session_state:
    st.session_state.analyst_name = "Analyst"

with st.sidebar:
    st.header("Analyst Login")
    analyst_name_input = st.text_input("User name", value=st.session_state.analyst_name)
    analyst_password_input = st.text_input("Password", type="password", placeholder="demo password")
    login_col, logout_col = st.columns(2)
    with login_col:
        if st.button("Login", use_container_width=True):
            if analyst_name_input.strip() and analyst_password_input.strip():
                st.session_state.analyst_logged_in = True
                st.session_state.analyst_name = analyst_name_input.strip()
                st.success(f"Logged in as {st.session_state.analyst_name}")
            else:
                st.warning("Enter a user name and password.")
    with logout_col:
        if st.button("Logout", use_container_width=True):
            st.session_state.analyst_logged_in = False
            st.info("Logged out.")
    st.caption(
        f"Status: {'Logged in' if st.session_state.analyst_logged_in else 'Guest mode'}"
    )

st.markdown(
    f"""
    <div class="site-shell">
      <div class="site-kicker">Security analytics platform</div>
      <h1 class="site-title">Insider Threat Command Center</h1>
      <p class="site-subtitle">
        A unified monitoring website for dataset-backed user behavior, hybrid anomaly scoring,
        alert triage, entity graph review, and model explainability.
      </p>
      <div class="site-meta">
        <span class="meta-chip"><span class="pulse-dot"></span> Monitoring active</span>
        <span class="meta-chip">{len(scores)} users scored</span>
        <span class="meta-chip">{len(file_access)} file events</span>
        <span class="meta-chip">{len(usb_usage)} USB events</span>
        <span class="meta-chip">{len(emails)} email events</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

def get_node_attrs():
    attrs = {}
    for _, row in scores.iterrows():
        score = float(row.get("hybrid_score", 0.0))
        red_team = int(row.get("is_red_team", 0))
        high_risk = int(row.get("hybrid_prediction", 0)) == 1
        attrs[row["user"]] = {
            "anomaly": score,
            "red_team": red_team,
            "risk_label": row.get("risk_label", "High" if high_risk else "Low"),
            "high_risk": high_risk or red_team == 1,
        }
    return attrs
attrs = get_node_attrs()

def build_activity_events():
    events = []
    for _, row in logins.iterrows():
        events.append({
            "time": row["login"],
            "user": row["user"],
            "event_type": "login",
            "target": "session",
            "details": f"logout {row['logout']}",
        })
    for _, row in file_access.iterrows():
        events.append({
            "time": row["access_time"],
            "user": row["user"],
            "event_type": "file_access",
            "target": row["file"],
            "details": "file opened",
        })
    for _, row in usb_usage.iterrows():
        events.append({
            "time": row["plug_time"],
            "user": row["user"],
            "event_type": "usb_usage",
            "target": row["device"],
            "details": f"unplug {row['unplug_time']}",
        })
    for _, row in emails.iterrows():
        events.append({
            "time": row["time"],
            "user": str(row["sender"]).replace("@company.com", ""),
            "event_type": "email",
            "target": row["recipient"],
            "details": row["subject"],
        })
    return pd.DataFrame(events).sort_values("time", ascending=False)


def build_monitor_rows(activity_events):
    latest_activity = activity_events.groupby("user", as_index=False).first()[["user", "time", "event_type"]]
    monitored = df.merge(latest_activity, on="user", how="left")
    monitored["hybrid_score"] = pd.to_numeric(monitored["hybrid_score"], errors="coerce").fillna(0)
    monitored["hybrid_prediction"] = pd.to_numeric(monitored["hybrid_prediction"], errors="coerce").fillna(0).astype(int)
    monitored["is_red_team"] = pd.to_numeric(monitored["is_red_team"], errors="coerce").fillna(0).astype(int)
    monitored["out_of_session_access"] = pd.to_numeric(monitored.get("out_of_session_access", 0), errors="coerce").fillna(0)
    monitored["usb_per_day"] = pd.to_numeric(monitored.get("usb_per_day", 0), errors="coerce").fillna(0)
    monitored["keyword_flag"] = pd.to_numeric(monitored.get("keyword_flag", 0), errors="coerce").fillna(0)

    alert_reasons = []
    for _, row in monitored.iterrows():
        reasons = []
        if row["hybrid_prediction"] == 1:
            reasons.append("hybrid anomaly")
        if row["risk_label"] == "Medium":
            reasons.append("medium risk")
        if row["is_red_team"] == 1:
            reasons.append("known red-team label")
        if row["out_of_session_access"] >= monitored["out_of_session_access"].quantile(0.75):
            reasons.append("high out-of-session access")
        if row["keyword_flag"] >= 0.5:
            reasons.append("suspicious email subjects")
        alert_reasons.append(", ".join(reasons) if reasons else "normal activity")

    monitored["alert_reason"] = alert_reasons
    monitored["alert_status"] = monitored.apply(
        lambda row: "Critical" if row["hybrid_prediction"] == 1 or row["is_red_team"] == 1 else (
            "Warning" if row["risk_label"] == "Medium" or row["alert_reason"] != "normal activity" else "Normal"
        ),
        axis=1,
    )
    return monitored.sort_values(["alert_status", "hybrid_score"], ascending=[True, False])


def load_user_actions():
    if not ACTION_LOG_PATH.exists():
        return pd.DataFrame(columns=["user", "flagged", "access_suspended", "action_note", "analyst", "updated_at"])
    actions = pd.read_csv(ACTION_LOG_PATH)
    for column in ["action_note", "analyst", "updated_at"]:
        if column not in actions:
            actions[column] = ""
    for column in ["flagged", "access_suspended"]:
        if column in actions:
            actions[column] = pd.to_numeric(actions[column], errors="coerce").fillna(0).astype(int)
    return actions


def save_user_action(user, flagged, access_suspended, note, analyst):
    actions = load_user_actions()
    updated_row = pd.DataFrame([{
        "user": user,
        "flagged": int(flagged),
        "access_suspended": int(access_suspended),
        "action_note": note,
        "analyst": analyst,
        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    }])
    actions = actions[actions["user"] != user]
    actions = pd.concat([actions, updated_row], ignore_index=True)
    actions.to_csv(ACTION_LOG_PATH, index=False)
    st.cache_data.clear()
    return actions


activity_events = build_activity_events()
monitor_df = build_monitor_rows(activity_events)
user_actions = load_user_actions()
if not user_actions.empty:
    monitor_df = monitor_df.merge(user_actions, on="user", how="left")
else:
    monitor_df["flagged"] = 0
    monitor_df["access_suspended"] = 0
    monitor_df["action_note"] = ""
    monitor_df["analyst"] = ""
    monitor_df["updated_at"] = ""
monitor_df[["flagged", "access_suspended"]] = (
    monitor_df[["flagged", "access_suspended"]].fillna(0).astype(int)
)
monitor_df["action_note"] = monitor_df["action_note"].fillna("")
monitor_df["analyst"] = monitor_df["analyst"].fillna("")
monitor_df["updated_at"] = monitor_df["updated_at"].fillna("")
monitor_df["access_state"] = monitor_df.apply(
    lambda row: "Suspended" if row["access_suspended"] else ("Flagged" if row["flagged"] else "Active"),
    axis=1,
)

def build_graph():
    G = nx.Graph()
    for _, row in file_access.iterrows():
        G.add_edge(row["user"], row["file"], type="access")
    for _, row in usb_usage.iterrows():
        G.add_edge(row["user"], row["device"], type="usb")
    return G
G = build_graph()

def get_at_risk_subgraph(G, attrs):
    high_risk_nodes = {n for n, v in attrs.items() if v["high_risk"]}
    connected_nodes = set()
    for node in high_risk_nodes:
        connected_nodes.add(node)
        connected_nodes.update(G.neighbors(node))
    return G.subgraph(connected_nodes).copy()

live_tab, anomaly_tab, user_tab, graph_tab, html_tab, how_tab = st.tabs([
    "Live Monitor",
    "Anomaly Table",
    "User Detail",
    "At-Risk Graph",
    "HTML Results",
    "How Does It Work?",
])

with live_tab:
    top_alerts_for_hero = monitor_df.sort_values("hybrid_score", ascending=False).head(5)
    latest_time = activity_events["time"].max()
    hero_html = f"""
    <div class="live-hero">
      <h2>Live Insider Threat Command Center</h2>
      <p>Monitoring user behavior across logins, file access, USB usage, email activity, graph risk, and hybrid ML anomaly output.</p>
      <div class="hero-row">
        <span class="status-pill"><span class="pulse-dot"></span> Live feed active</span>
        <span class="status-pill">Latest dataset event: {latest_time}</span>
        <span class="status-pill">Top risk: {top_alerts_for_hero.iloc[0]["user"]} ({top_alerts_for_hero.iloc[0]["hybrid_score"]:.3f})</span>
      </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)

    control_col, interval_col = st.columns([1, 2])
    with control_col:
        refresh_enabled = st.toggle("Auto refresh dashboard", value=False)
    with interval_col:
        refresh_seconds = st.slider("Refresh interval seconds", 10, 120, 30, step=10)
    if refresh_enabled:
        components.html(
            f"<script>setTimeout(function(){{window.parent.location.reload();}}, {refresh_seconds * 1000});</script>",
            height=0,
        )

    critical_count = int((monitor_df["alert_status"] == "Critical").sum())
    warning_count = int((monitor_df["alert_status"] == "Warning").sum())
    normal_count = int((monitor_df["alert_status"] == "Normal").sum())
    high_model_alerts = int(monitor_df["hybrid_prediction"].sum())

    st.markdown(
        f"""
        <div class="risk-grid">
          <div class="risk-card"><span>Monitored users</span><strong>{len(monitor_df)}</strong></div>
          <div class="risk-card critical"><span>Critical alerts</span><strong>{critical_count}</strong></div>
          <div class="risk-card warning"><span>Warnings</span><strong>{warning_count}</strong></div>
          <div class="risk-card normal"><span>Hybrid model alerts</span><strong>{high_model_alerts}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ticker_items = []
    for _, row in top_alerts_for_hero.iterrows():
        ticker_items.append(
            f"<span>{row['alert_status']} | {row['user']} | score {row['hybrid_score']:.3f} | {row['alert_reason']}</span>"
        )
    st.markdown(
        f"""<div class="alert-strip"><div class="ticker">{''.join(ticker_items)}</div></div>""",
        unsafe_allow_html=True,
    )

    radar_points = []
    radar_source = monitor_df.sort_values("hybrid_score", ascending=False).head(12).reset_index(drop=True)
    for index, row in radar_source.iterrows():
        left = 12 + ((index * 31) % 76)
        top = 20 + ((index * 47) % 60)
        high_class = " high" if row["alert_status"] == "Critical" else ""
        tooltip = (
            f"<strong>{row['user']}</strong><br>"
            f"Score: {row['hybrid_score']:.3f}<br>"
            f"Risk: {row['risk_label']}<br>"
            f"Status: {row['alert_status']}"
        )
        radar_points.append(
            f'<button class="radar-user{high_class}" style="left:{left}%;top:{top}%;" '
            f'aria-label="{row["user"]} score {row["hybrid_score"]:.3f}">'
            f'<span class="radar-tooltip">{tooltip}</span></button>'
        )
    st.markdown(
        f"""
        <div class="radar-wrap">
          <div class="radar-label">Animated Risk Radar</div>
          {''.join(radar_points)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-card">
          <h3 class="section-title">Operational Alert Board</h3>
          <p class="section-copy">Prioritized user monitoring view generated from current anomaly scores and recent activity across all datasets.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Manual User Access Control")
    manual_col_1, manual_col_2 = st.columns([1, 2])
    with manual_col_1:
        manual_user = st.selectbox(
            "Select any user",
            monitor_df.sort_values("user")["user"].tolist(),
            key="manual_action_user",
        )
    manual_row = monitor_df[monitor_df["user"] == manual_user].iloc[0]
    with manual_col_2:
        manual_note = st.text_input(
            "Manual action note",
            value=manual_row["action_note"] or "Manual analyst action",
            key="manual_action_note",
        )

    logged_in = st.session_state.analyst_logged_in
    analyst_name = st.session_state.analyst_name if logged_in else "Guest"
    if not logged_in:
        st.info("Login from the sidebar to save manual flag, suspend, or resume actions.")

    manual_buttons = st.columns(5)
    with manual_buttons[0]:
        if st.button("Manual Flag", disabled=not logged_in, use_container_width=True):
            save_user_action(
                manual_user,
                flagged=1,
                access_suspended=int(manual_row["access_suspended"]),
                note=manual_note,
                analyst=analyst_name,
            )
            st.success(f"{manual_user} manually flagged.")
            st.rerun()
    with manual_buttons[1]:
        if st.button("Manual Suspend", disabled=not logged_in, type="primary", use_container_width=True):
            save_user_action(
                manual_user,
                flagged=1,
                access_suspended=1,
                note=manual_note,
                analyst=analyst_name,
            )
            st.error(f"{manual_user} manually suspended.")
            st.rerun()
    with manual_buttons[2]:
        if st.button("Resume Access", disabled=not logged_in, use_container_width=True):
            save_user_action(
                manual_user,
                flagged=0,
                access_suspended=0,
                note=manual_note or "Access resumed",
                analyst=analyst_name,
            )
            st.success(f"{manual_user} access resumed.")
            st.rerun()
    with manual_buttons[3]:
        if st.button("Clear Flag", disabled=not logged_in, use_container_width=True):
            save_user_action(
                manual_user,
                flagged=0,
                access_suspended=int(manual_row["access_suspended"]),
                note=manual_note or "Flag cleared",
                analyst=analyst_name,
            )
            st.success(f"{manual_user} flag cleared.")
            st.rerun()
    with manual_buttons[4]:
        if st.button("Flag + Suspend", disabled=not logged_in, use_container_width=True):
            save_user_action(
                manual_user,
                flagged=1,
                access_suspended=1,
                note=manual_note or "Flagged and suspended",
                analyst=analyst_name,
            )
            st.error(f"{manual_user} flagged and suspended.")
            st.rerun()

    st.caption(
        f"{manual_user}: {manual_row['access_state']} | "
        f"Risk {manual_row['risk_label']} | Score {manual_row['hybrid_score']:.3f} | "
        f"Last analyst: {manual_row['analyst'] or 'none'}"
    )

    critical_users = monitor_df[monitor_df["alert_status"] == "Critical"].sort_values("hybrid_score", ascending=False)
    if critical_users.empty:
        st.success("No critical users are currently available for suspension.")
    else:
        st.subheader("Critical User Response")
        action_col, note_col = st.columns([1, 2])
        with action_col:
            selected_critical_user = st.selectbox(
                "Select critical user",
                critical_users["user"].tolist(),
                key="critical_action_user",
            )
        selected_action_row = monitor_df[monitor_df["user"] == selected_critical_user].iloc[0]
        with note_col:
            action_note = st.text_input(
                "Action note",
                value=selected_action_row["action_note"] or "Critical insider-threat response",
                key="critical_action_note",
            )

        action_buttons = st.columns(4)
        with action_buttons[0]:
            if st.button("Mark Flagged", use_container_width=True):
                if not st.session_state.analyst_logged_in:
                    st.warning("Login from the sidebar before saving this action.")
                    st.stop()
                save_user_action(
                    selected_critical_user,
                    flagged=1,
                    access_suspended=0,
                    note=action_note,
                    analyst=st.session_state.analyst_name,
                )
                st.success(f"{selected_critical_user} marked as flagged.")
                st.rerun()
        with action_buttons[1]:
            if st.button("Suspend All Access", type="primary", use_container_width=True):
                if not st.session_state.analyst_logged_in:
                    st.warning("Login from the sidebar before saving this action.")
                    st.stop()
                save_user_action(
                    selected_critical_user,
                    flagged=1,
                    access_suspended=1,
                    note=action_note,
                    analyst=st.session_state.analyst_name,
                )
                st.error(f"All access suspended for {selected_critical_user}.")
                st.rerun()
        with action_buttons[2]:
            if st.button("Restore Access", use_container_width=True):
                if not st.session_state.analyst_logged_in:
                    st.warning("Login from the sidebar before saving this action.")
                    st.stop()
                save_user_action(
                    selected_critical_user,
                    flagged=0,
                    access_suspended=0,
                    note="Access restored by analyst",
                    analyst=st.session_state.analyst_name,
                )
                st.success(f"Access restored for {selected_critical_user}.")
                st.rerun()
        with action_buttons[3]:
            if st.button("Clear Flag Only", use_container_width=True):
                if not st.session_state.analyst_logged_in:
                    st.warning("Login from the sidebar before saving this action.")
                    st.stop()
                save_user_action(
                    selected_critical_user,
                    flagged=0,
                    access_suspended=int(selected_action_row["access_suspended"]),
                    note="Flag cleared by analyst",
                    analyst=st.session_state.analyst_name,
                )
                st.success(f"Flag cleared for {selected_critical_user}.")
                st.rerun()

        st.caption(
            f"Current action state for {selected_critical_user}: "
            f"{selected_action_row['access_state']} | Updated: {selected_action_row['updated_at'] or 'not actioned'}"
        )

    st.subheader("Current User Alert Board")
    status_filter = st.multiselect(
        "Alert status",
        ["Critical", "Warning", "Normal"],
        default=["Critical", "Warning", "Normal"],
    )
    filtered_monitor = monitor_df[monitor_df["alert_status"].isin(status_filter)].copy()
    live_columns = [
        "user",
        "alert_status",
        "risk_label",
        "hybrid_score",
        "supervised_probability",
        "unsupervised_ensemble",
        "time",
        "event_type",
        "access_state",
        "flagged",
        "access_suspended",
        "analyst",
        "updated_at",
        "alert_reason",
    ]
    st.dataframe(filtered_monitor[live_columns], height=420, hide_index=True)

    suspended_users = monitor_df[monitor_df["access_suspended"] == 1]
    if not suspended_users.empty:
        st.subheader("Suspended Access List")
        st.dataframe(
            suspended_users[["user", "alert_status", "risk_label", "hybrid_score", "analyst", "action_note", "updated_at"]],
            height=180,
            hide_index=True,
        )

    actioned_users = monitor_df[(monitor_df["flagged"] == 1) | (monitor_df["access_suspended"] == 1)]
    if not actioned_users.empty:
        st.subheader("Manual Action History")
        st.dataframe(
            actioned_users[["user", "access_state", "flagged", "access_suspended", "analyst", "action_note", "updated_at"]],
            height=220,
            hide_index=True,
        )

    st.markdown(
        """
        <div class="section-card">
          <h3 class="section-title">Recent Dataset Event Stream</h3>
          <p class="section-copy">Latest login, file, USB, and email activity joined with the user risk output for rapid review.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Recent Dataset Events")
    recent_events = activity_events.head(40).merge(
        scores[["user", "risk_label", "hybrid_score", "hybrid_prediction"]],
        on="user",
        how="left",
    )
    st.dataframe(
        recent_events[["time", "user", "event_type", "target", "details", "risk_label", "hybrid_score", "hybrid_prediction"]],
        height=360,
        hide_index=True,
    )

    if critical_count:
        st.error("Critical alerts are active. Review the users marked Critical in the alert board.")
    elif warning_count:
        st.warning("Warning alerts are active. Review medium-risk users and unusual activity.")
    else:
        st.success("All monitored users are currently normal according to the dataset and hybrid model.")

with anomaly_tab:
    st.markdown(
        """
        <div class="section-card">
          <h3 class="section-title">Model Scoring Workspace</h3>
          <p class="section-copy">Compare supervised, unsupervised, and hybrid anomaly scores for every monitored user.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.header("User Anomaly Scores")
    score_method = st.selectbox("Select Model", available_score_options, key="score_method")
    df["Red Team"] = df["is_red_team"].map({1: "Yes", 0: "No"})
    df["rank"] = df[score_method].rank(ascending=False, method="dense").astype(int)
    df_sorted = df.sort_values(score_method, ascending=False)
    cols = ["user", "risk_label", "Red Team", score_method, "rank"] + [
        c for c in df.columns if c not in ["user", "risk_label", score_method, "rank", "Red Team"]
    ]
    st.dataframe(df_sorted[cols], height=500, hide_index=True)
    st.subheader("Top 5 Anomalous Users")
    top5 = df_sorted.head(5)
    st.bar_chart(top5.set_index("user")[score_method])
    results_path = DATA_DIR / "hybrid_model_results.csv"
    if results_path.exists():
        st.subheader("Hybrid ML Results")
        st.dataframe(pd.read_csv(results_path), hide_index=True)

with user_tab:
    st.markdown(
        """
        <div class="section-card">
          <h3 class="section-title">User Investigation View</h3>
          <p class="section-copy">Inspect one user at a time with engineered features and model score breakdowns.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.header("User Detail")
    selected_user = st.selectbox("Select User", df_sorted["user"], key="user_detail")
    user_row = df_sorted[df_sorted["user"] == selected_user].iloc[0]
    st.write("**Risk:**", user_row.get("risk_label", "Unknown"))
    st.write("**Red Team:**", "Yes" if int(user_row["is_red_team"]) else "No")
    st.write("**Features:**")
    st.json({k: user_row[k] for k in ['mean_login_hour', 'mean_logout_hour', 'files_per_day', 'usb_per_day', 'emails_per_day', 'out_of_session_access', 'degree_centrality', 'betweenness_centrality', 'keyword_flag', 'subject_len', 'sentiment'] if k in user_row})
    st.write("**Anomaly Scores:**")
    st.json({k: user_row[k] for k in score_options if k in user_row})

with graph_tab:
    st.markdown(
        """
        <div class="section-card">
          <h3 class="section-title">Relationship Graph</h3>
          <p class="section-copy">Interactive graph of high-risk users and their connected files or USB devices.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.header("At-Risk Nodes and Their Connections")
    subG = get_at_risk_subgraph(G, attrs)
    net = Network(height="900px", width="100%", notebook=False, bgcolor="#222222", font_color="white")
    net.barnes_hut(gravity=-2000, central_gravity=0.1, spring_length=200, spring_strength=0.01, damping=0.85, overlap=1)
    net.set_options('''
    var options = {
      "physics": {
        "enabled": true,
        "stabilization": {"enabled": true, "fit": true, "iterations": 2500, "updateInterval": 50},
        "barnesHut": {
          "gravitationalConstant": -2000,
          "centralGravity": 0.1,
          "springLength": 200,
          "springConstant": 0.01,
          "damping": 0.85,
          "avoidOverlap": 1
        }
      }
    }
    ''')
    for node in subG.nodes():
        if node in attrs:
            score = attrs[node]["anomaly"]
            red = attrs[node]["red_team"]
            risk = attrs[node]["risk_label"]
            color = "red" if red else ("orange" if risk == "High" else "yellow" if risk == "Medium" else "lightblue")
            size = 30 if red else (22 if risk == "High" else 15 if risk == "Medium" else 10)
            title = f"User: {node}<br>Hybrid Score: {score:.3f}<br>Risk: {risk}<br>Red Team: {'Yes' if red else 'No'}"
        elif str(node).startswith("file"):
            color = "green"
            size = 8
            title = f"File: {node}"
        elif str(node).startswith("usb"):
            color = "purple"
            size = 8
            title = f"Device: {node}"
        else:
            color = "gray"
            size = 8
            title = str(node)
        net.add_node(node, label=str(node), color=color, size=size, title=title)
    for edge in subG.edges(data=True):
        net.add_edge(edge[0], edge[1], color="gray" if edge[2]["type"] == "access" else "purple")
    graph_path = DASHBOARD_DIR / "graph.html"
    net.save_graph(str(graph_path))
    components.html(graph_path.read_text(encoding="utf-8"), height=900, scrolling=False)

with html_tab:
    st.markdown(
        """
        <div class="section-card">
          <h3 class="section-title">Generated Executive Report</h3>
          <p class="section-copy">A standalone HTML report generated from the latest hybrid anomaly output.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.header("Generated HTML Results")
    report_path = DASHBOARD_DIR / "anomaly_results.html"
    if report_path.exists():
        components.html(report_path.read_text(encoding="utf-8"), height=760, scrolling=True)
    else:
        st.warning("Run `python models/train.py` to generate dashboard/anomaly_results.html.")

with how_tab:
    st.markdown(
        """
        <div class="section-card">
          <h3 class="section-title">System Methodology</h3>
          <p class="section-copy">How the dashboard converts raw activity datasets into supervised and unsupervised anomaly alerts.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.header('How Does It Work?')
    st.markdown('''
## System Overview
This system detects insider threats by analyzing user behavior, system access, and relationships using advanced machine learning and graph analysis techniques.

---

### 1. **Data Simulation & Feature Engineering**
- **Simulated Logs:** The system generates synthetic logs for user logins, file access, USB usage, and emails, mimicking real organizational activity.
- **Feature Engineering:** Extracts features such as:
    - Login/logout patterns (mean hours, frequency)
    - File/USB/email activity rates
    - Out-of-session file access
    - Graph centrality (degree, betweenness)
    - NLP features from email subjects (keyword flags, length)

---

### 2. **Anomaly Detection Algorithms**
- **Isolation Forest**
    - *Mathematics:* Randomly partitions data to isolate points. Anomalies are isolated faster (shorter average path length in trees).
    - *Computer Science:* Ensemble of binary trees; each tree splits on random features/values. The anomaly score is based on the average path length to isolate a sample.
- **One-Class SVM**
    - *Mathematics:* Finds a boundary in feature space that encloses most data (support vectors). Points outside are anomalies.
    - *Computer Science:* Uses kernel methods (e.g., RBF) to map data to high-dimensional space and find a maximal margin hyperplane.
- **Autoencoder**
    - *Mathematics:* Neural network learns to compress and reconstruct input. High reconstruction error indicates anomaly.
    - *Computer Science:* Trains a feedforward neural network (MLP) to minimize reconstruction loss (MSE) between input and output.
- **Supervised Random Forest**
    - *Mathematics:* Learns from red-team labels to estimate the probability that a user matches known malicious behavior.
    - *Computer Science:* Trains an ensemble of decision trees with class balancing so rare insider-threat labels still influence the model.
- **Hybrid Score**
    - *Mathematics:* Normalizes the unsupervised detector scores, averages them into an unsupervised ensemble, then blends that risk with the supervised probability.
    - *Computer Science:* Produces one ranked `hybrid_score` for investigation while keeping the individual detector outputs visible for comparison.

---

### 3. **Graph Analysis**
- **Entity Graph:** Users, files, and devices are nodes; edges represent access or usage.
- **Centrality Measures:**
    - *Degree Centrality:* Number of connections (activity level).
    - *Betweenness Centrality:* Frequency a node lies on shortest paths (potential for information flow/control).
- **At-Risk Subgraph:** Focuses on high-risk users and their direct connections for visualization and investigation.

---

### 4. **Explainability**
- **SHAP (SHapley Additive exPlanations):**
    - *Mathematics:* Based on cooperative game theory; attributes model output to each feature by averaging over all possible feature orderings.
    - *Computer Science:* Computes feature importances for each prediction, helping analysts understand why a user is flagged.
- **LIME (Local Interpretable Model-agnostic Explanations):**
    - *Mathematics:* Fits a simple, interpretable model locally around a prediction to approximate the complex model.
    - *Computer Science:* Perturbs input data and observes output changes to estimate feature influence (not supported for Isolation Forest, but available for other models).

---

### 5. **Dashboard & Visualization**
- **Streamlit:** Interactive web app for data exploration, anomaly review, and graph visualization.
- **PyVis/NetworkX:** Renders interactive network graphs for at-risk nodes and their relationships.

---

### 6. **Red Team Simulation**
- Injects malicious behaviors (after-hours access, mass downloads, suspicious USB usage) to test detection capability.

---

## Summary
This system combines unsupervised machine learning, graph theory, and explainable AI to provide a robust, interpretable approach to insider threat detection.
''') 
