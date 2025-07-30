import streamlit as st
import pandas as pd

st.set_page_config(page_title="시니어 금융 유형 설문", page_icon="💸", layout="centered")

st.markdown("### 💬 시니어 금융 유형 설문")
st.markdown("**아래 질문에 순차적으로 응답해주세요.**")

if "page" not in st.session_state:
    st.session_state.page = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}

questions = [
    ("나이를 입력해주세요.", "number", "age"),
    ("성별을 선택해주세요.", "selectbox", "gender", ["남성", "여성"]),
    ("가구원 수를 입력해주세요.", "number", "family_size"),
    ("현재 보유한 금융자산 분위(1~5)를 입력해주세요.", "number", "assets"),
    ("월 수령하는 연금 금액 분위(1~5)를 입력해주세요.", "number", "pension"),
    ("월 평균 소비 분위(1~5)를 입력해주세요.", "number", "consumption")
]

def next_page():
    if st.session_state.get("input_value") is not None:
        current_q = questions[st.session_state.page]
        st.session_state.responses[current_q[2]] = st.session_state.input_value
        st.session_state.page += 1
        st.session_state.input_value = None

if st.session_state.page < len(questions):
    q = questions[st.session_state.page]
    st.markdown(f"**Q{st.session_state.page + 1}. {q[0]}**")

    if q[1] == "number":
        st.number_input(
            label=" ",
            key="input_value",
            step=1,
            min_value=1,
            max_value=5,
            format="%d",
            on_change=next_page,
            label_visibility="collapsed"
        )
    elif q[1] == "selectbox":
        st.selectbox(
            label=" ",
            options=q[3],
            key="input_value",
            on_change=next_page,
            label_visibility="collapsed"
        )
else:
    st.success("✅ 모든 질문에 응답하셨습니다!")
    r = st.session_state.responses
    pension = r["pension"]
    assets = r["assets"]
    consumption = r["consumption"]

    def classify_user(p, a, c):
        if c >= 4:
            return "고소비형"
        elif p >= 4 and a >= 4 and c <= 2:
            return "자산운용형"
        elif p <= 2 and a <= 2 and c >= 4:
            return "위험취약형"
        elif p <= 2 and a <= 3:
            return "소득취약형"
        elif p <= 2 and a >= 4:
            return "자산보유형"
        elif p >= 4 and a <= 2:
            return "현금흐름형"
        elif p == 3 and a == 3:
            return "균형형"
        else:
            return "기타"

    category = classify_user(pension, assets, consumption)

    st.markdown(f"### 🧾 당신의 금융유형은: **{category}** 입니다.")

    # 유형 목록 및 표시
    types = ["소득취약형", "현금흐름형", "균형형", "자산보유형", "자산운용형", "고소비형", "위험취약형", "기타"]
    df = pd.DataFrame({
        "유형": types,
        "당신의 결과": ["✅" if t == category else "" for t in types]
    })
    st.dataframe(df, use_container_width=True)
