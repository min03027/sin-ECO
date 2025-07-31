import streamlit as st
import pandas as pd
import joblib
from pytorch_tabnet.tab_model import TabNetClassifier

# 모델 로드
model = joblib.load("tabnet_model.pkl")
le = joblib.load("label_encoder.pkl")

st.title("📋 고령자 재무 설문 & 연금 유형 분류")

# 1. 연금 수령 여부 먼저 묻기
pension_status = st.radio("현재 연금을 수령하고 계신가요?", ["예", "아니오"])

if pension_status == "아니오":
    st.info("❗️아직 연금을 수령 중이 아니시므로, 예측 모델을 적용할 수 없습니다.\n예측은 연금 수령 중인 사용자에게만 가능합니다.")
    st.stop()

# 2. 수령 중인 경우 설문 계속 진행
st.markdown("### 👤 사용자 기본 정보")
gender = st.selectbox("성별", ["남성", "여성"])
age = st.slider("나이", 60, 100, 72)
family_size = st.number_input("가구원 수", min_value=1, step=1)
dependents = st.radio("피부양자 있음?", ["아니오", "예"])
assets = st.number_input("총 자산 (만원)", min_value=0)
income = st.number_input("월 소득 (만원)", min_value=0)
living_cost = st.number_input("월 지출비 (만원)", min_value=0)
investment = st.selectbox("투자 성향", ["안정형", "안정추구형", "위험중립형", "적극투자형", "공격투자형"])

st.markdown("### 📌 수령 중인 연금 수령액 입력")
pensions = {
    "조기노령연금_예측수령액": st.number_input("조기노령연금", min_value=0.0),
    "조기재직자노령연금_예측수령액": st.number_input("조기재직자노령연금", min_value=0.0),
    "분할연금_예측수령액": st.number_input("분할연금", min_value=0.0),
    "완전노령연금_예측수령액": st.number_input("완전노령연금", min_value=0.0),
    "완전재직자노령연금_예측수령액": st.number_input("완전재직자노령연금", min_value=0.0),
    "특례노령연금_예측수령액": st.number_input("특례노령연금", min_value=0.0)
}

if st.button("📊 고령자 유형 예측 실행"):
    # 3. 전처리
    input_df = pd.DataFrame([{
        "나이": age,
        "성별": 0 if gender == "남성" else 1,
        "가구원수": family_size,
        "피부양자": 1 if dependents == "예" else 0,
        "자산": assets,
        "지출비": living_cost,
        "소득": income,
        "투자성향": {"안정형": 0, "안정추구형": 1, "위험중립형": 2, "적극투자형": 3, "공격투자형": 4}[investment],
        "연금": sum(pensions.values())
    }])

    # 4. 예측
    pred = model.predict(input_df.values)
    pred_label = le.inverse_transform(pred)[0]

    best_pension = max(pensions, key=pensions.get)
    best_amt = pensions[best_pension]

    st.success(f"✅ 예측된 고령자 유형: **{pred_label}**")
    st.markdown("### 📈 연금 수령액 요약")
    st.dataframe(pd.DataFrame(pensions.values(), index=pensions.keys(), columns=["예측수령액(만원/월)"]))

    st.markdown(f"**📌 가장 유리한 연금 선택:** `{best_pension.replace('_예측수령액','')}` ({best_amt}만원/월)")
