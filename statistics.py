import pandas as pd

from database import load_answers, load_attempts


def get_summary_stats(attempts_df: pd.DataFrame, total_questions: int) -> dict:
    if attempts_df.empty:
        return {
            "participants": 0,
            "attempts": 0,
            "avg_score": 0.0,
            "avg_accuracy": 0.0,
            "total_questions": total_questions,
        }

    return {
        "participants": attempts_df["user_code"].nunique(),
        "attempts": len(attempts_df),
        "avg_score": round(float(attempts_df["score"].mean()), 2),
        "avg_accuracy": round(float(attempts_df["accuracy"].mean()), 1),
        "total_questions": total_questions,
    }


def get_question_stats(answers_df: pd.DataFrame) -> pd.DataFrame:
    if answers_df.empty:
        return pd.DataFrame(
            columns=["question_id", "question_text", "total", "correct", "correct_rate", "wrong_rate"]
        )

    question_stats = (
        answers_df.groupby(["question_id", "question_text"], as_index=False)
        .agg(total=("is_correct", "count"), correct=("is_correct", "sum"))
    )
    question_stats["correct_rate"] = (question_stats["correct"] / question_stats["total"] * 100).round(1)
    question_stats["wrong_rate"] = (100 - question_stats["correct_rate"]).round(1)
    return question_stats.sort_values("question_id")


def get_pre_post_compare(attempts_df: pd.DataFrame) -> pd.DataFrame:
    pre_mean = attempts_df[attempts_df["quiz_type"] == "pre"]["score"].mean()
    post_mean = attempts_df[attempts_df["quiz_type"] == "post"]["score"].mean()

    return pd.DataFrame(
        {
            "구분": ["학습 전", "학습 후"],
            "평균 점수": [
                round(pre_mean, 2) if pd.notna(pre_mean) else 0,
                round(post_mean, 2) if pd.notna(post_mean) else 0,
            ],
        }
    )


def get_progress_df(attempts_df: pd.DataFrame) -> pd.DataFrame:
    if attempts_df.empty:
        return pd.DataFrame()

    first_attempts = (
        attempts_df.sort_values("submitted_at")
        .groupby("user_code", as_index=False)
        .first()[["user_code", "score"]]
        .rename(columns={"score": "first_score"})
    )

    latest_attempts = (
        attempts_df.sort_values("submitted_at")
        .groupby("user_code", as_index=False)
        .last()[["user_code", "score", "accuracy", "quiz_type", "submitted_at"]]
        .rename(
            columns={
                "score": "latest_score",
                "accuracy": "latest_accuracy",
                "quiz_type": "latest_quiz_type",
            }
        )
    )

    progress_df = first_attempts.merge(latest_attempts, on="user_code", how="inner")
    progress_df["improvement"] = progress_df["latest_score"] - progress_df["first_score"]
    return progress_df