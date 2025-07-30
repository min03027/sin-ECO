import streamlit as st

# 페이지 기본 설정
st.set_page_config(page_title="시니어 금융 설문", page_icon="💸", layout="centered")

st.markdown("### 💬 시니어 금융 유형 설문")
st.markdown("**아래 질문에 순차적으로 응답해주세요.**")

# 상태 저장
if "page" not in st.session_state:
    st.session_state.page = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}

# 설문 문항 정의
questions = [
    ("나이를 입력해주세요.", "number", "age"),
    ("성별을 선택해주세요.", "selectbox", "gender", ["남성", "여성"]),
    ("가구원 수를 입력해주세요.", "number", "family_size"),
    ("피부양자가 있나요?", "selectbox", "dependents", ["예", "아니오"]),
    ("현재 보유한 금융자산(만원)을 입력해주세요.", "number", "assets"),
    ("월 수령하는 연금 금액(만원)을 입력해주세요.", "number", "pension"),
    ("월 평균 지출비(만원)은 얼마인가요?", "number", "living_cost"),
    ("월 평균 소득은 얼마인가요?", "number", "income"),
    ("투자 성향을 선택해주세요.", "selectbox", "risk", ["안정형", "안정추구형", "위험중립형", "적극투자형", "공격투자형"])
]

# 다음 문항으로 이동
def next_page():
    if st.session_state.get("input_value") is not None:
        current_q = questions[st.session_state.page]
        st.session_state.responses[current_q[2]] = st.session_state.input_value
        st.session_state.page += 1
        st.session_state.input_value = None

# 설문 진행
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
# 설문 완료 시
else:
    st.success("✅ 모든 질문에 응답하셨습니다!")
    r = st.session_state.responses

    # 점수 산정 (0~5 스케일)
    asset_score = min((r["assets"] or 0) / 1000, 5)
    pension_score = min((r["pension"] or 0) / 50, 5)
    consumption_score = min((r["living_cost"] or 0) / 100, 5)

    # 유형 분류
    if asset_score >= 4 and pension_score >= 4:
        category = "자산운용형"
    elif asset_score >= 4 and pension_score < 2:
        category = "자산중심형"
    elif asset_score < 2 and pension_score >= 4:
        category = "소득중심형"
    elif asset_score < 2 and pension_score < 2 and consumption_score >= 4:
        category = "위험 취약형"
    elif 2 <= asset_score <= 4 and 2 <= pension_score <= 4:
        category = "균형형"
    else:
        category = "지출관리형"

    # 결과 출력
    st.markdown(f"### 🧾 당신의 금융 유형은: **{category}**")
    st.markdown("👉 해당 유형에 따라 맞춤 금융 전략을 제시해드립니다.")
    st.write("🗂️ 응답 요약:")
    st.json(st.session_state.responses)
