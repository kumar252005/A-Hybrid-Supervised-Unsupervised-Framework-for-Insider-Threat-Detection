from pathlib import Path

import pandas as pd

from feature_engineering import extract_features as extract_behavior_features
from nlp_email_features import extract_features as extract_nlp_features

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

import sys

sys.path.insert(0, str(ROOT_DIR))
from gnn.gnn_anomaly import compute_graph_features


def merge_features() -> pd.DataFrame:
    df_classic = extract_behavior_features()
    df_graph = compute_graph_features()
    df_nlp = extract_nlp_features()
    red_team_path = DATA_DIR / "red_team_users.csv"
    red_team = (
        pd.read_csv(red_team_path)["user"].dropna().astype(str).tolist()
        if red_team_path.exists()
        else []
    )

    df_nlp["user"] = df_nlp["sender"].astype(str).str.replace("@company.com", "", regex=False)
    df_nlp_agg = df_nlp.groupby("user", as_index=False).agg({
        "keyword_flag": "mean",
        "subject_len": "mean",
        "sentiment": "mean",
    })

    df = df_classic.merge(df_graph, on="user", how="left").merge(df_nlp_agg, on="user", how="left")
    df["is_red_team"] = df["user"].astype(str).isin(red_team).astype(int)
    numeric_columns = df.columns.difference(["user"])
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce").fillna(0)
    df.to_csv(DATA_DIR / "merged_features.csv", index=False)
    return df


if __name__ == "__main__":
    merge_features()
    print("Merged features saved to data/merged_features.csv")
