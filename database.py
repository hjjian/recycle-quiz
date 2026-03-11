from datetime import datetime

import gspread
import pandas as pd
import streamlit as st

SPREADSHEET_KEY = "16-0dwjrNvDFjiYy0z9G6ldZUArJsNWL5mQFlxAPxdEE"


def connect_sheet():
    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
    }

    client = gspread.service_account_from_dict(creds_dict)
    spreadsheet = client.open_by_key(SPREADSHEET_KEY)

    attempts_sheet = spreadsheet.worksheet("attempts")
    answers_sheet = spreadsheet.worksheet("answers")
    return attempts_sheet, answers_sheet


def init_db() -> None:
    return None


def load_attempts() -> pd.DataFrame:
    attempts_sheet, _ = connect_sheet()
    records = attempts_sheet.get_all_records()

    if not records:
        return pd.DataFrame(
            columns=["attempt_id", "user_code", "quiz_type", "submitted_at", "score", "total", "accuracy"]
        )

    df = pd.DataFrame(records)

    for col in ["attempt_id", "score", "total", "accuracy"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def load_answers() -> pd.DataFrame:
    _, answers_sheet = connect_sheet()
    records = answers_sheet.get_all_records()

    if not records:
        return pd.DataFrame(
            columns=["attempt_id", "question_id", "question_text", "user_answer", "correct_answer", "is_correct"]
        )

    df = pd.DataFrame(records)

    for col in ["attempt_id", "question_id", "is_correct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def save_attempt(user_code: str, quiz_type: str, questions: list, user_answers: dict) -> int:
    attempts_sheet, answers_sheet = connect_sheet()

    score = 0
    total = len(questions)
    for q in questions:
        if user_answers.get(str(q["id"])) == q["answer"]:
            score += 1

    accuracy = round((score / total) * 100, 1)
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    attempts_df = load_attempts()
    if attempts_df.empty:
        attempt_id = 1
    else:
        attempt_id = int(attempts_df["attempt_id"].max()) + 1

    attempts_sheet.append_row(
        [attempt_id, user_code, quiz_type, submitted_at, score, total, accuracy],
        value_input_option="USER_ENTERED",
    )

    rows = []
    for q in questions:
        selected = user_answers.get(str(q["id"]))
        is_correct = 1 if selected == q["answer"] else 0
        rows.append(
            [
                attempt_id,
                q["id"],
                q["question"],
                selected if selected is not None else "",
                q["answer"],
                is_correct,
            ]
        )

    if rows:
        answers_sheet.append_rows(rows, value_input_option="USER_ENTERED")

    return attempt_id


def get_attempt_history(user_code: str) -> pd.DataFrame:
    df = load_attempts()
    if df.empty:
        return df

    filtered = df[df["user_code"] == user_code].copy()
    filtered = filtered.sort_values("submitted_at")
    return filtered


def get_answers_for_attempt(attempt_id: int) -> pd.DataFrame:
    df = load_answers()
    if df.empty:
        return df

    filtered = df[df["attempt_id"] == attempt_id].copy()
    filtered = filtered.sort_values("question_id")
    return filtered


def read_attempt_by_id(attempt_id: int) -> pd.DataFrame:
    df = load_attempts()
    if df.empty:
        return pd.DataFrame(columns=["score", "total", "accuracy", "submitted_at", "quiz_type"])

    filtered = df[df["attempt_id"] == attempt_id].copy()
    return filtered[["score", "total", "accuracy", "submitted_at", "quiz_type"]]