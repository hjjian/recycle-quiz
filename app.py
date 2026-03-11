import json
from pathlib import Path

import pandas as pd
import streamlit as st

from database import (
    get_answers_for_attempt,
    get_attempt_history,
    init_db,
    load_answers,
    load_attempts,
    read_attempt_by_id,
    save_attempt,
)
from statistics import (
    get_pre_post_compare,
    get_progress_df,
    get_question_stats,
    get_summary_stats,
)

st.set_page_config(page_title="분리수거 퀴즈", page_icon="♻️", layout="wide")

QUESTION_PATH = "questions.json"


def load_questions() -> list:
    if not Path(QUESTION_PATH).exists():
        st.error("questions.json 파일이 없습니다.")
        st.stop()

    with open(QUESTION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def reset_quiz_state() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("answer_"):
            del st.session_state[key]
    st.session_state.last_attempt_id = None


init_db()
questions = load_questions()

if "last_attempt_id" not in st.session_state:
    st.session_state.last_attempt_id = None

st.title("♻️ 분리수거 퀴즈")
st.caption(
    """퀴즈 풀고, 분리수거 챗봇을 이용한 후 선물 받아가세요!
    퀴즈 참여를 통해 수집된 결과는 고려대학교 지속가능원 체인지메이커스 활동에서 환경 인식 개선을 위한 자료로 활용됩니다."""
    )

quiz_tab, my_result_tab, admin_tab = st.tabs(["퀴즈 풀기", "내 기록 보기", "관리자 통계"])


with quiz_tab:
    user_code = st.text_input(
        "개인 코드",
        key="quiz_user_code",
        placeholder="이름 + 전화번호 뒷자리 (예: 현정1498, 은아6002, 현서8502)",
        help="같은 코드를 쓰면 이전 기록과 비교할 수 있어요.",
    ).strip().upper()

    quiz_type = st.radio(
        "응시 유형",
        options=["pre", "post"],
        format_func=lambda x: "이용 전 (pre)" if x == "pre" else "이용 후 (post)",
        horizontal=True,
    )

    if not user_code:
        st.info("개인 코드를 입력하면 퀴즈를 시작할 수 있어요.")
    else:
        with st.form("quiz_form"):
            collected_answers = {}
            for q in questions:
                st.markdown(f"### {q['id']}. {q['question']}")
                collected_answers[str(q["id"])] = st.radio(
                    "답을 선택하세요",
                    options=q["options"],
                    key=f"answer_{q['id']}",
                    index=None,
                )

            submitted = st.form_submit_button("제출하고 저장하기")

        if submitted:
            attempt_id = save_attempt(user_code, quiz_type, questions, collected_answers)
            st.session_state.last_attempt_id = attempt_id
            st.success("제출이 완료되었어요. 점수와 답안이 저장되었습니다.")

        if st.session_state.last_attempt_id is not None:
            latest_answers = get_answers_for_attempt(st.session_state.last_attempt_id)
            latest_attempt = read_attempt_by_id(st.session_state.last_attempt_id)

            if not latest_attempt.empty:
                row = latest_attempt.iloc[0]

                st.markdown("## 이번 결과")
                c1, c2, c3 = st.columns(3)
                c1.metric("점수", f"{int(row['score'])}/{int(row['total'])}")
                c2.metric("정답률", f"{float(row['accuracy']):.1f}%")
                c3.metric("응시 유형", "이용 전" if row["quiz_type"] == "pre" else "이용 후")
                st.caption(f"제출 시각: {row['submitted_at']}")

                st.markdown("### 문항별 피드백")
                for q in questions:
                    matched = latest_answers[latest_answers["question_id"] == q["id"]]
                    if matched.empty:
                        continue

                    answer_row = matched.iloc[0]
                    st.markdown(f"**{q['id']}. {q['question']}**")
                    st.write(
                        f"- 내 답: {answer_row['user_answer'] if pd.notna(answer_row['user_answer']) and answer_row['user_answer'] != '' else '미응답'}"
                    )
                    st.write(f"- 정답: {answer_row['correct_answer']}")
                    if int(answer_row["is_correct"]) == 1:
                        st.success("정답")
                    else:
                        st.error("오답")
                    st.write(f"- 해설: {q['explanation']}")
                    st.write("")

                if st.button("다시 풀기"):
                    reset_quiz_state()
                    st.rerun()


with my_result_tab:
    st.subheader("내 기록 조회")

    lookup_code = st.text_input(
        "조회할 개인 코드",
        key="lookup_code",
        placeholder="이름 + 전화번호 뒷자리 (예: 현정1498, 은아6002, 현서8502)",
    ).strip().upper()

    if lookup_code:
        history = get_attempt_history(lookup_code)

        if history.empty:
            st.warning("해당 코드의 기록이 아직 없습니다.")
        else:
            st.dataframe(history, use_container_width=True)

            total = int(history.iloc[-1]["total"])
            first_score = int(history.iloc[0]["score"])
            latest_score = int(history.iloc[-1]["score"])
            best_score = int(history["score"].max())

            c1, c2, c3 = st.columns(3)
            c1.metric("첫 점수", f"{first_score}/{total}")
            c2.metric("최근 점수", f"{latest_score}/{total}")
            c3.metric("최고 점수", f"{best_score}/{total}")

            if len(history) >= 2:
                st.metric("처음 대비 변화", f"{latest_score - first_score:+d}점")

            st.markdown("### 이용 전 / 후 비교")
            pre_df = history[history["quiz_type"] == "pre"]
            post_df = history[history["quiz_type"] == "post"]

            if not pre_df.empty and not post_df.empty:
                latest_pre = int(pre_df.iloc[-1]["score"])
                latest_post = int(post_df.iloc[-1]["score"])
                st.success(f"이용 전 {latest_pre}점 → 이용 후 {latest_post}점 ({latest_post - latest_pre:+d}점)")
            else:
                st.info("이용 전(pre)과 이용 후(post) 기록이 모두 있어야 비교할 수 있어요.")


with admin_tab:
    st.subheader("관리자 통계")

    password = st.text_input("관리자 비밀번호", type="password", key="admin_password_input")

    if password == st.secrets["admin_password"]:
        attempts_df = load_attempts()
        answers_df = load_answers()

        if attempts_df.empty:
            st.info("아직 수집된 데이터가 없습니다.")
        else:
            summary = get_summary_stats(attempts_df, len(questions))

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 참여자 수", f"{summary['participants']}명")
            c2.metric("총 응시 횟수", f"{summary['attempts']}회")
            c3.metric("평균 점수", f"{summary['avg_score']}/{summary['total_questions']}")
            c4.metric("평균 정답률", f"{summary['avg_accuracy']}%")

            st.markdown("### 문제별 정답률 / 오답률")
            question_stats = get_question_stats(answers_df)
            st.dataframe(question_stats, use_container_width=True)
            if not question_stats.empty:
                st.bar_chart(question_stats.set_index("question_text")["wrong_rate"])

            st.markdown("### 가장 많이 틀린 문제 TOP 10")
            top_wrong = question_stats.sort_values("wrong_rate", ascending=False).head(10)
            st.dataframe(
                top_wrong[["question_id", "question_text", "wrong_rate"]],
                use_container_width=True,
            )

            st.markdown("### 이용 전 / 이용 후 평균 비교")
            compare_df = get_pre_post_compare(attempts_df)
            st.dataframe(compare_df, use_container_width=True)
            st.bar_chart(compare_df.set_index("구분"))

            st.markdown("### 개인별 최근 기록과 향상도")
            progress_df = get_progress_df(attempts_df)
            st.dataframe(progress_df, use_container_width=True)

            st.markdown("### 데이터 다운로드")
            attempts_csv = attempts_df.to_csv(index=False).encode("utf-8-sig")
            answers_csv = answers_df.to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                "attempts.csv 다운로드",
                attempts_csv,
                file_name="attempts.csv",
                mime="text/csv",
            )
            st.download_button(
                "answers.csv 다운로드",
                answers_csv,
                file_name="answers.csv",
                mime="text/csv",
            )

    elif password:
        st.error("비밀번호가 틀렸습니다.")

    else:
        st.info("관리자만 통계를 확인할 수 있습니다.")
