pip install matplotlib

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

# 페이지 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = 1

# 질문 리스트 정의
questions = [
    ("pension", "당신의 월 연금 수령액은 얼마인가요? (단위: 만 원)"),
    ("assets", "현재 보유한 총 금융자산은 얼마인가요? (단위: 만 원)"),
    ("spending", "한 달 평균 소비 금액은 얼마인가요? (단위: 만 원)"),
    ("family_size", "현재 함께 거주 중인 가족 수는 몇 명인가요? (본인 포함)")
]

# 점수 시각화 함수 정의
def plot_user_scores(user_inputs):
    fig, ax = plt.subplots(figsize=(8, 4))
    user_series = pd.Series(user_inputs)
    user_series.plot(kind='bar', ax=ax)
    ax.set_title("입력 기반 재무 요소 점수 시각화")
    ax.set_ylabel("점수")
    ax.set_ylim(0, 100)
    ax.grid(axis='y', linestyle='--', alpha=0.6)
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

# 입력 받기
if st.session_state.page <= len(questions):
    key, question = questions[st.session_state.page - 1]
    user_input = st.number_input(question, min_value=0.0, format="%.1f", key=key)
    if st.button("다음"):
        st.session_state.page += 1
        st.experimental_rerun()

# 결과 출력
elif st.session_state.page == len(questions) + 1:
    st.title("\U0001F4C8 당신의 시니어 금융 건강 점수")

    pension = st.session_state.get("pension", 0)
    assets = st.session_state.get("assets", 0)
    spending = st.session_state.get("spending", 0)
    family_size = st.session_state.get("family_size", 1)

    user_scores = {
        "월 연금 수령액": min(pension / 300, 1) * 100,  # 300만 원 기준
        "총 자산 규모": min(assets / 10000, 1) * 100,  # 1억 원 기준
        "월 평균 소비": max(100 - (spending / 300 * 100), 0),  # 300만 원 초과하면 감점
        "부양 가족 수": max(100 - (family_size - 1) * 20, 0)  # 가족 수 많을수록 점수 감소
    }

    fig = plot_user_scores(user_scores)
    st.pyplot(fig)

    st.markdown("\n### 총평")
    total_score = sum(user_scores.values()) / len(user_scores)
    if total_score >= 75:
        st.success(f"총점: {total_score:.1f}점\n\n금융적으로 매우 안정적인 상태입니다!")
    elif total_score >= 50:
        st.info(f"총점: {total_score:.1f}점\n\n기본적인 금융 여건은 갖추고 있으나, 일부 개선이 필요할 수 있습니다.")
    else:
        st.warning(f"총점: {total_score:.1f}점\n\n주의가 필요합니다. 재정 점검을 권장드립니다.")

    if st.button("처음으로 돌아가기"):
        st.session_state.page = 1
        for k, _ in questions:
            st.session_state.pop(k, None)
        st.experimental_rerun()
