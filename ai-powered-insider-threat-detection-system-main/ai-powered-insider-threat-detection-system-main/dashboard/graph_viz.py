from pathlib import Path

import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DASHBOARD_DIR = ROOT_DIR / "dashboard"

st.set_page_config(layout="wide")
st.title("User-File-Device Graph: At-Risk Nodes and Their Connections")


@st.cache_data
def load_data():
    file_access = pd.read_csv(DATA_DIR / "file_access.csv", parse_dates=["access_time"])
    usb_usage = pd.read_csv(DATA_DIR / "usb_usage.csv", parse_dates=["plug_time", "unplug_time"])
    scores = pd.read_csv(DATA_DIR / "anomaly_scores.csv")
    return file_access, usb_usage, scores


file_access, usb_usage, scores = load_data()

graph = nx.Graph()
for _, row in file_access.iterrows():
    graph.add_edge(row["user"], row["file"], type="access")
for _, row in usb_usage.iterrows():
    graph.add_edge(row["user"], row["device"], type="usb")

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

connected_nodes = set()
for node, values in attrs.items():
    if values["high_risk"] and node in graph:
        connected_nodes.add(node)
        connected_nodes.update(graph.neighbors(node))
subgraph = graph.subgraph(connected_nodes).copy()

net = Network(height="900px", width="100%", notebook=False, bgcolor="#222222", font_color="white")
net.barnes_hut(gravity=-2000, central_gravity=0.1, spring_length=200, spring_strength=0.01, damping=0.85, overlap=1)

for node in subgraph.nodes():
    if node in attrs:
        score = attrs[node]["anomaly"]
        risk = attrs[node]["risk_label"]
        red_team = attrs[node]["red_team"]
        color = "red" if red_team else ("orange" if risk == "High" else "yellow" if risk == "Medium" else "lightblue")
        size = 30 if red_team else (22 if risk == "High" else 15 if risk == "Medium" else 10)
        title = f"User: {node}<br>Hybrid Score: {score:.3f}<br>Risk: {risk}<br>Red Team: {'Yes' if red_team else 'No'}"
    elif str(node).startswith("file"):
        color, size, title = "green", 8, f"File: {node}"
    elif str(node).startswith("usb"):
        color, size, title = "purple", 8, f"Device: {node}"
    else:
        color, size, title = "gray", 8, str(node)
    net.add_node(node, label=str(node), color=color, size=size, title=title)

for edge in subgraph.edges(data=True):
    net.add_edge(edge[0], edge[1], color="gray" if edge[2]["type"] == "access" else "purple")

graph_path = DASHBOARD_DIR / "graph.html"
net.save_graph(str(graph_path))
components.html(graph_path.read_text(encoding="utf-8"), height=900, scrolling=False)
