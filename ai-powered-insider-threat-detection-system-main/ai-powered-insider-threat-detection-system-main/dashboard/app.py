from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

st.set_page_config(layout="wide")
st.title("AI-Powered Insider Threat Detection Dashboard")


@st.cache_data
def load_data():
    features = pd.read_csv(DATA_DIR / "merged_features.csv")
    scores = pd.read_csv(DATA_DIR / "anomaly_scores.csv")
    feature_columns = [column for column in features.columns if column != "is_red_team"]
    return features[feature_columns].merge(scores, on="user", how="inner")


df = load_data()
score_options = [
    "hybrid_score",
    "supervised_probability",
    "unsupervised_ensemble",
    "isolation_forest",
    "oneclass_svm",
    "autoencoder",
]
available_scores = [column for column in score_options if column in df.columns]

st.header("User Anomaly Scores")
score_method = st.selectbox("Select Model", available_scores)

df["Red Team"] = df["is_red_team"].map({1: "Yes", 0: "No"})
df["rank"] = df[score_method].rank(ascending=False, method="dense").astype(int)
df_sorted = df.sort_values(score_method, ascending=False)
cols = ["user", "risk_label", "Red Team", score_method, "rank"] + [
    column
    for column in df.columns
    if column not in ["user", "risk_label", score_method, "rank", "Red Team"]
]
st.dataframe(df_sorted[cols], height=420, hide_index=True)

st.subheader("Top 5 Anomalous Users")
st.bar_chart(df_sorted.head(5).set_index("user")[score_method])

results_path = DATA_DIR / "hybrid_model_results.csv"
if results_path.exists():
    st.subheader("Hybrid ML Results")
    st.dataframe(pd.read_csv(results_path), hide_index=True)

st.header("User Detail")
selected_user = st.selectbox("Select User", df_sorted["user"])
user_row = df_sorted[df_sorted["user"] == selected_user].iloc[0]
st.write("**Risk:**", user_row.get("risk_label", "Unknown"))
st.write("**Red Team:**", "Yes" if int(user_row["is_red_team"]) else "No")
st.write("**Features:**")
st.json({
    key: user_row[key]
    for key in [
        "mean_login_hour",
        "mean_logout_hour",
        "files_per_day",
        "usb_per_day",
        "emails_per_day",
        "out_of_session_access",
        "degree_centrality",
        "betweenness_centrality",
        "keyword_flag",
        "subject_len",
        "sentiment",
    ]
    if key in user_row
})
st.write("**Anomaly Scores:**")
st.json({key: user_row[key] for key in score_options if key in user_row})
