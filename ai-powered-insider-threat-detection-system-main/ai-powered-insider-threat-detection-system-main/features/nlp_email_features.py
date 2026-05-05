from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
SUSPICIOUS_KEYWORDS = ["confidential", "urgent", "password", "secret", "invoice", "transfer"]


def extract_features() -> pd.DataFrame:
    emails = pd.read_csv(DATA_DIR / "emails.csv", parse_dates=["time"])
    features = []
    for _, row in emails.iterrows():
        subject = str(row["subject"]).lower()
        keyword_flag = int(any(kw in subject for kw in SUSPICIOUS_KEYWORDS))
        subject_len = len(subject.strip())
        sentiment = 0
        features.append({
            "sender": row["sender"],
            "recipient": row["recipient"],
            "time": row["time"],
            "keyword_flag": keyword_flag,
            "subject_len": subject_len,
            "sentiment": sentiment,
        })
    df = pd.DataFrame(features)
    df.to_csv(DATA_DIR / "nlp_email_features.csv", index=False)
    return df


if __name__ == "__main__":
    extract_features()
    print("NLP email features saved to data/nlp_email_features.csv")
