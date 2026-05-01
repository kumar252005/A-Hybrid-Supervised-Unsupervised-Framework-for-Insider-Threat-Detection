from pathlib import Path

import pandas as pd
import networkx as nx
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DASHBOARD_DIR = ROOT_DIR / "dashboard"

st.set_page_config(layout="wide")
st.title("AI-Powered Insider Threat Detection: Combined Dashboard")

@st.cache_data
def load_all_data():
    features = pd.read_csv(DATA_DIR / "merged_features.csv")
    scores = pd.read_csv(DATA_DIR / "anomaly_scores.csv")
    file_access = pd.read_csv(DATA_DIR / "file_access.csv", parse_dates=["access_time"])
    usb_usage = pd.read_csv(DATA_DIR / "usb_usage.csv", parse_dates=["plug_time", "unplug_time"])
    return features, scores, file_access, usb_usage

features, scores, file_access, usb_usage = load_all_data()
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

anomaly_tab, user_tab, graph_tab, html_tab, how_tab = st.tabs([
    "Anomaly Table",
    "User Detail",
    "At-Risk Graph",
    "HTML Results",
    "How Does It Work?",
])

with anomaly_tab:
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
    st.header("Generated HTML Results")
    report_path = DASHBOARD_DIR / "anomaly_results.html"
    if report_path.exists():
        components.html(report_path.read_text(encoding="utf-8"), height=760, scrolling=True)
    else:
        st.warning("Run `python models/train.py` to generate dashboard/anomaly_results.html.")

with how_tab:
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
