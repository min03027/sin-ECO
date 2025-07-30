import streamlit as st
import pandas as pd

st.set_page_config(page_title="시니어 금융 설문", page_icon="💸", layout="centered")

st.title("💬 시니어 금융 유형 설문")
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
    ("피부양자가 있나요?", "selectbox", "dependents", ["예", "아니오"]),
    ("현재 보유한 금융자산(만원)을 입력해주세요.", "number", "assets"),
    ("월 수령하는 연금 금액(만원)을 입력해주세요.", "number", "pension"),
    ("월 평균 지출비(만원)은 얼마인가요?", "number", "living_cost"),
    ("월 평균 소득은 얼마인가요?", "number", "income"),
    ("투자 성향을 선택해주세요.", "selectbox", "risk", ["안정형", "안정추구형", "위험중립형", "적극투자형", "공격투자형"]),
]

# 다음 페이지 이동
def next_page():
    if st.session_state.get("input_value") is not None:
        current_q = questions[st.session_state.page]
        st.session_state.responses[current_q[2]] = st.session_state.input_value
        st.session_state.page += 1
        st.session_state.input_value = None

# 질문 출력
if st.session_state.page < len(questions):
    q = questions[st.session_state.page]
    st.markdown(f"**Q{st.session_state.page + 1}. {q[0]}**")
    if q[1] == "number":
        st.number_input(" ", key="input_value", step=1, format="%d", on_change=next_page, label_visibility="collapsed")
    elif q[1] == "selectbox":
        st.selectbox(" ", options=q[3], key="input_value", on_change=next_page, label_visibility="collapsed")

# 모든 질문 완료 시
else:
    st.success("✅ 모든 질문에 응답하셨습니다!")
    r = st.session_state.responses

    # 분위 계산 함수
    def get_quintile(value, breaks):
        for i, b in enumerate(breaks):
            if value <= b:
                return i + 1
        return 5

    pension_q = get_quintile(r["pension"], [10, 20, 30, 40])
    asset_q = get_quintile(r["assets"], [5000, 10000, 30000, 50000])
    consume_q = get_quintile(r["living_cost"], [50, 100, 150, 200])

    # 유형 분류 조건
    if pension_q >= 4 and asset_q >= 4 and consume_q <= 2:
        category = "자산운용형"
    elif pension_q <= 2 and asset_q <= 2 and consume_q >= 4:
        category = "위험취약형"
    elif pension_q == 3 and asset_q == 3:
        category = "균형형"
    elif consume_q >= 4:
        category = "고소비형"
    elif pension_q <= 2 and asset_q <= 3:
        category = "소득취약형"
    else:
        category = "복합형"

    # 결과 출력
    st.markdown(f"## 🧾 당신의 금융 유형: **{category}**")
    st.markdown("👉 입력 기반 재무 진단 결과입니다.")

    # 분류 기준 테이블
    result_df = pd.DataFrame({
        "금융유형": ["자산운용형", "위험취약형", "균형형", "고소비형", "소득취약형", "복합형"],
        "분류 조건 (요약)": [
            "연금 분위 ≥4, 자산 분위 ≥4, 소비 분위 ≤2",
            "연금 분위 ≤2, 자산 분위 ≤2, 소비 분위 ≥4",
            "연금 분위 =3, 자산 분위 =3",
            "소비 분위 ≥4",
            "연금 분위 ≤2, 자산 분위 ≤3",
            "기타 조합"
        ],
        "주요 특징": [
            "투자 여력 풍부, 운용 중심 전략 적합",
            "재무 위험 큼, 지출 조정 필요",
            "안정적이고 보수적 접근 적합",
            "지출 관리 및 절세 상품 추천 필요",
            "기초 재정 안정 필요, 복지 연계 고려",
            "복합적 상태, 맞춤형 전략 필요"
        ]
    })

    # 조건 강조
    st.dataframe(result_df.style.applymap(
        lambda val: "background-color: #e6f7ff;" if val == category else "",
        subset=["금융유형"]
    ))
