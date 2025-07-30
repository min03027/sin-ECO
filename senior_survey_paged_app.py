import streamlit as st
import pandas as pd

st.set_page_config(page_title="시니어 금융 설문", page_icon="💸", layout="centered")
st.markdown("### 💬 시니어 금융 유형 설문")
st.markdown("**아래 질문에 순차적으로 응답해주세요.**")

# 상태 초기화
if "page" not in st.session_state:
    st.session_state.page = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}

# 설문 문항
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

# 다음 문항으로 이동
def next_page():
    if st.session_state.get("input_value") is not None:
        current_q = questions[st.session_state.page]
        st.session_state.responses[current_q[2]] = st.session_state.input_value
        st.session_state.page += 1
        st.session_state.input_value = None

# 질문 응답 처리
if st.session_state.page < len(questions):
    q = questions[st.session_state.page]
    st.markdown(f"**Q{st.session_state.page + 1}. {q[0]}**")

    if q[1] == "number":
        st.number_input(label=" ", key="input_value", step=1, format="%d", on_change=next_page, label_visibility="collapsed")
    elif q[1] == "selectbox":
        st.selectbox(label=" ", options=q[3], key="input_value", on_change=next_page, label_visibility="collapsed")

else:
    st.success("✅ 모든 질문에 응답하셨습니다!")
    r = st.session_state.responses

    # 분위 분류
    def get_quintile(value, boundaries):
        for i, b in enumerate(boundaries):
            if value <= b:
                return i + 1
        return 5

    pension_q = get_quintile(r["pension"], [800, 1600, 3000, 5000])
    assets_q = get_quintile(r["assets"], [1000, 3000, 6000, 10000])
    spend = (r["living_cost"] or 0) + (r["hobby_cost"] or 0)
    spend_q = get_quintile(spend, [50, 100, 200, 300])

    # 유형 분류
    def classify(pq, aq, sq):
        if pq >= 4 and aq >= 4 and sq <= 2:
            return "자산운용형"
        elif pq <= 2 and aq <= 2 and sq >= 4:
            return "위험취약형"
        elif pq == 3 and aq == 3:
            return "균형형"
        elif sq >= 4:
            return "고소비형"
        elif pq <= 2 and aq <= 3:
            return "소득취약형"
        else:
            return "기타"

    category = classify(pension_q, assets_q, spend_q)

    st.markdown(f"### 🧾 당신의 금융 유형: **{category}**")
    st.markdown("👉 입력 기반 재무 진단 결과입니다.")

    # 유형표 데이터 생성
    data = {
        "금융유형": ["자산운용형", "위험취약형", "균형형", "고소비형", "소득취약형", "기타"],
        "분류 조건 (요약)": [
            "연금 분위 ≥ 4, 자산 분위 ≥ 4, 소비 분위 ≤ 2",
            "연금 분위 ≤ 2, 자산 분위 ≤ 2, 소비 분위 ≥ 4",
            "연금 분위 = 3, 자산 분위 = 3",
            "소비 분위 ≥ 4",
            "연금 분위 ≤ 2, 자산 분위 ≤ 3",
            "기타 조합"
        ],
        "주요 특징": [
            "투자 여력 풍부, 운용 중심 전략 적합",
            "재무 위험 큼, 지출 조정 필요",
            "안정적이고 보수적 접근 적합",
            "지출 관리 및 절세 상품 추천 필요",
            "기초 재정 안정 필요, 복지 연계 고려",
            "일반적 상태"
        ]
    }

    df = pd.DataFrame(data)

    # 하이라이트 렌더링
    def highlight_category(row):
        return ['background-color: #cce5ff' if row['금융유형'] == category else '' for _ in row]

    st.dataframe(df.style.apply(highlight_category, axis=1))

    # 분위 정보도 보여줌
    st.markdown("#### 🔍 입력 기준 분위 분류")
    st.table(pd.DataFrame({
        "항목": ["연금 분위", "자산 분위", "소비 분위"],
        "값": [pension_q, assets_q, spend_q]
    }))
