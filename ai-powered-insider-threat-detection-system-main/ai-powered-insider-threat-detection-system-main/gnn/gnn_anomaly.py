from pathlib import Path

import networkx as nx
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


def compute_graph_features() -> pd.DataFrame:
    file_access = pd.read_csv(DATA_DIR / "file_access.csv", parse_dates=["access_time"])
    usb_usage = pd.read_csv(DATA_DIR / "usb_usage.csv", parse_dates=["plug_time", "unplug_time"])

    graph = nx.Graph()
    for _, row in file_access.iterrows():
        graph.add_edge(str(row["user"]), str(row["file"]), type="access")
    for _, row in usb_usage.iterrows():
        graph.add_edge(str(row["user"]), str(row["device"]), type="usb")

    user_nodes = sorted(n for n in graph.nodes if str(n).startswith("user"))
    degree = nx.degree_centrality(graph) if graph.number_of_nodes() else {}
    betweenness = nx.betweenness_centrality(graph) if graph.number_of_nodes() else {}

    features = pd.DataFrame(
        [
            {
                "user": user,
                "degree_centrality": degree.get(user, 0.0),
                "betweenness_centrality": betweenness.get(user, 0.0),
            }
            for user in user_nodes
        ]
    )
    features.to_csv(DATA_DIR / "graph_features.csv", index=False)
    return features


if __name__ == "__main__":
    compute_graph_features()
    print("Graph features saved to data/graph_features.csv")
    print("GNN anomaly detection scaffold ready. Use these graph features in the hybrid model.")
