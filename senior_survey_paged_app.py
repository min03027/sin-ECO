
import streamlit as st

# 상태 저장을 위한 세션 초기화
if 'page' not in st.session_state:
    st.session_state.page = 0
if 'responses' not in st.session_state:
    st.session_state.responses = {}

# 설문 문항 정의
questions = [
    {"key": "age", "question": "당신의 나이는 몇 세입니까?", "type": "number"},
    {"key": "gender", "question": "성별을 선택해주세요.", "type": "radio", "options": ["남성", "여성"]},
    {"key": "household_size", "question": "현재 함께 사는 가족 수는 몇 명입니까?", "type": "number"},
    {"key": "pension", "question": "현재 매달 수령하는 연금액(만원 기준)은 얼마입니까?", "type": "number"},
    {"key": "assets", "question": "본인의 전체 금융자산은 얼마나 되십니까? (만원 기준)", "type": "number"},
    {"key": "monthly_expense", "question": "월평균 생활비(만원 기준)는 얼마입니까?", "type": "number"},
    {"key": "hobby_expense", "question": "월평균 취미/여가 비용(만원 기준)은 얼마입니까?", "type": "number"},
    {"key": "risk_preference", "question": "금융 투자 성향을 선택해주세요.", "type": "radio", "options": ["매우 안정적", "안정적", "중립", "공격적", "매우 공격적"]}
]

# 현재 페이지의 질문 표시
current_q = questions[st.session_state.page]
st.title("📊 시니어 금융 유형 설문")
st.write(f"질문 {st.session_state.page + 1} / {len(questions)}")

if current_q["type"] == "number":
    response = st.number_input(current_q["question"], min_value=0, step=1, key=current_q["key"])
elif current_q["type"] == "radio":
    response = st.radio(current_q["question"], current_q["options"], key=current_q["key"])

# 다음 버튼
if st.button("다음"):
    st.session_state.responses[current_q["key"]] = response
    if st.session_state.page < len(questions) - 1:
        st.session_state.page += 1
    else:
        st.success("✅ 설문이 완료되었습니다.")
        st.write("### 🧾 당신의 응답 요약")
        st.json(st.session_state.responses)

        # 점수화 및 분류 예시
        score = 0
        if st.session_state.responses["pension"] > 100:
            score += 2
        if st.session_state.responses["assets"] > 3000:
            score += 2
        if st.session_state.responses["monthly_expense"] < 150:
            score += 1
        if st.session_state.responses["risk_preference"] in ["공격적", "매우 공격적"]:
            score += 1

        if score >= 5:
            st.success("💡 자산운용 적극형")
        elif score >= 3:
            st.info("💡 안정적 자산형")
        else:
            st.warning("💡 보수적 관리형")

# 뒤로가기 버튼
if st.session_state.page > 0:
    if st.button("이전"):
        st.session_state.page -= 1
