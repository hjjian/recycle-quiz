import streamlit as st

questions = [
    {
        "question": "컵라면 용기는 어떻게 버려야 할까요?",
        "options": [
            "플라스틱으로 분리배출",
            "종이류로 분리배출",
            "일반쓰레기(종량제 봉투)",
            "캔류"
        ],
        "answer": "일반쓰레기(종량제 봉투)"
    },
    {
        "question": "칫솔은 어떻게 버려야 할까요?",
        "options": [
            "플라스틱",
            "일반쓰레기",
            "비닐",
            "캔류"
        ],
        "answer": "일반쓰레기"
    },
    {
        "question": "페트병을 버릴 때 올바른 방법은?",
        "options": [
            "라벨 제거 후 배출",
            "그대로 버리기",
            "종이류로 배출",
            "캔류로 배출"
        ],
        "answer": "라벨 제거 후 배출"
    }
]

st.title("♻️ 분리수거 퀴즈")

score = 0

for i, q in enumerate(questions):

    st.subheader(q["question"])

    user_answer = st.radio(
        "정답을 선택하세요",
        q["options"],
        key=i
    )

    if user_answer == q["answer"]:
        score += 1

if st.button("결과 보기"):

    st.write(f"점수: {score} / {len(questions)}")

    if score == len(questions):
        st.success("완벽합니다! 🎉")
    else:
        st.info("틀린 문제를 다시 확인해보세요.")