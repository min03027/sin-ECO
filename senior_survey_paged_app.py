import streamlit as st
import pandas as pd

st.set_page_config(page_title="시니어 금융 설문", page_icon="💸", layout="centered")
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
    ("현재 보유한 금융자산(만원)을 입력해주세요.", "number", "assets"),
    ("월 수령하는 연금 금액(만원)을 입력해주세요.", "number", "pension"),
    ("월 평균 생활비(만원)은 얼마인가요?", "number", "living_cost"),
    ("월 평균 취미/여가비(만원)는 얼마인가요?", "number", "hobby_cost"),
    ("투자 성향을 선택해주세요.", "selectbox", "risk", ["안정형", "중립형", "공격형"])
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

    def get_quintile(value, bounds):
        for i, b in enumerate(bounds):
            if value <= b:
                return i + 1
        return 5

    # 임의 기준 (실제 데이터 기반 수정 가능)
    pension_bounds = [70, 150, 250, 400]      # 연금
    asset_bounds = [2000, 5000, 10000, 20000]  # 자산
    consume_bounds = [50, 100, 150, 200]       # 소비

    pension_q = get_quintile(r["pension"], pension_bounds)
    asset_q = get_quintile(r["assets"], asset_bounds)
    consume_q = get_quintile(r["living_cost"] + r["hobby_cost"], consume_bounds)

    def classify_type(pq, aq, cq):
        if pq >= 4 and aq >= 4 and cq <= 2:
            return "자산운용형"
        elif pq <= 2 and aq <= 2 and cq >= 4:
            return "위험취약형"
        elif pq == 3 and aq == 3:
            return "균형형"
        elif cq >= 4:
            return "고소비형"
        elif pq <= 2 and aq <= 3:
            return "소득취약형"
        else:
            return "일반형"

    result = classify_type(pension_q, asset_q, consume_q)

    st.markdown(f"### 🧾 당신의 금융 유형: **{result}**")
    st.markdown("👉 입력 기반 재무 진단 결과입니다.")

    df = pd.DataFrame({
        "항목": ["연금 분위", "자산 분위", "소비 분위"],
        "값": [pension_q, asset_q, consume_q]
    })
    st.dataframe(df)

    st.markdown("---")
    st.markdown("💡 이 결과는 입력한 수치를 기반으로 계산되며, 유형에 맞는 금융 전략 설계에 활용할 수 있습니다.")
