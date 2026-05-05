from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

def load_logs():
    logins = pd.read_csv(DATA_DIR / "logins.csv", parse_dates=["login", "logout"])
    file_access = pd.read_csv(DATA_DIR / "file_access.csv", parse_dates=["access_time"])
    usb_usage = pd.read_csv(DATA_DIR / "usb_usage.csv", parse_dates=["plug_time", "unplug_time"])
    emails = pd.read_csv(DATA_DIR / "emails.csv", parse_dates=["time"])
    return logins, file_access, usb_usage, emails


def _safe_mean(series, default=0.0):
    if series.empty:
        return default
    value = series.mean()
    return default if pd.isna(value) else float(value)


def extract_features() -> pd.DataFrame:
    logins, file_access, usb_usage, emails = load_logs()
    users = sorted(
        set(logins["user"].dropna().astype(str))
        | set(file_access["user"].dropna().astype(str))
        | set(usb_usage["user"].dropna().astype(str))
        | set(emails["sender"].dropna().astype(str).str.replace("@company.com", "", regex=False))
    )
    features = []
    for user in users:
        user_logins = logins[logins["user"].astype(str) == user]
        user_files = file_access[file_access["user"].astype(str) == user]
        user_usb = usb_usage[usb_usage["user"].astype(str) == user]
        user_emails = emails[emails["sender"].astype(str) == f"{user}@company.com"]

        mean_login_hour = _safe_mean(user_logins["login"].dt.hour)
        mean_logout_hour = _safe_mean(user_logins["logout"].dt.hour)
        files_per_day = _safe_mean(user_files.groupby(user_files["access_time"].dt.date).size())
        usb_per_day = _safe_mean(user_usb.groupby(user_usb["plug_time"].dt.date).size())
        emails_per_day = _safe_mean(user_emails.groupby(user_emails["time"].dt.date).size())

        out_of_session = 0
        for _, row in user_files.iterrows():
            session = user_logins[
                (user_logins["login"] <= row["access_time"])
                & (user_logins["logout"] >= row["access_time"])
            ]
            if session.empty:
                out_of_session += 1
        features.append({
            "user": user,
            "mean_login_hour": mean_login_hour,
            "mean_logout_hour": mean_logout_hour,
            "files_per_day": files_per_day,
            "usb_per_day": usb_per_day,
            "emails_per_day": emails_per_day,
            "out_of_session_access": int(out_of_session),
        })
    df = pd.DataFrame(features)
    df.to_csv(DATA_DIR / "features.csv", index=False)
    return df


if __name__ == "__main__":
    extract_features()
    print("Features extracted to data/features.csv")
