# app.py
import os
import numpy as np
import pandas as pd
import streamlit as st
import joblib
import faiss

# ================================
# 기본 설정 & 공통 스타일
# ================================
st.set_page_config(page_title="시니어 금융 설문 & 추천", page_icon="💸", layout="centered")

st.markdown("""
<style>
:root {
  --blue:#BFD6FF;      /* 파랑 타일 */
  --yellow:#FFE1A8;    /* 노랑 타일 */
  --deep:#004aad;      /* 제목색 */
}
.big-title{font-size:40px !important; font-weight:800; color:var(--deep); text-align:center; margin:8px 0 18px;}
.help{font-size:16px; color:#555; text-align:center; margin:-8px 0 18px;}
.section-title{font-size:24px; font-weight:800; margin:12px 0 8px;}
.stButton>button{
  width:100%; height:120px; border-radius:16px; font-size:26px; font-weight:800;
  padding:8px 14px; border:0;
}
.tile-blue .stButton>button{ background:var(--blue); }
.tile-yellow .stButton>button{ background:var(--yellow); }
label, .stSelectbox label {font-size:18px !important;}
</style>
""", unsafe_allow_html=True)

# 실행 파일 기준 경로 (Streamlit/로컬 모두 안전)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
MODELS_DIR = BASE_DIR          # 모델/인덱스/CSV 모두 같은 폴더라고 가정
PRODUCTS_CSV = "금융상품_3개_통합본.csv"

# ================================
# 모델/데이터 로딩 (캐시)
# ================================
@st.cache_resource
def load_models():
    survey_model   = joblib.load(os.path.join(MODELS_DIR, "tabnet_model.pkl"))
    survey_encoder = joblib.load(os.path.join(MODELS_DIR, "label_encoder.pkl"))
    reg_model      = joblib.load(os.path.join(MODELS_DIR, "reg_model.pkl"))
    type_model     = joblib.load(os.path.join(MODELS_DIR, "type_model.pkl"))  # (보유 시) 여유
    return survey_model, survey_encoder, reg_model, type_model

@st.cache_resource
def load_faiss_index(optional=True):
    idx_path = os.path.join(MODELS_DIR, "faiss_index.idx")
    if optional and not os.path.exists(idx_path):
        return None
    return faiss.read_index(idx_path)

@st.cache_data
def load_products_fixed():
    path = os.path.join(BASE_DIR, PRODUCTS_CSV)
    if not os.path.exists(path):
        raise FileNotFoundError(f"상품 파일이 없습니다: {path}")
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="cp949")
    return df

# 모델/데이터 로드
survey_model, survey_encoder, reg_model, type_model = load_models()
faiss_index_loaded = load_faiss_index(optional=True)  # 있으면 로드(없어도 무방)
raw_products = load_products_fixed()

# ================================
# 상품 전처리 & 추천 유틸
# ================================
def preprocess_products(df: pd.DataFrame) -> pd.DataFrame:
    np.random.seed(42)
    df.columns = df.columns.str.strip()

    # 상품명 추출
    if '상품명' in df.columns:
        names = df['상품명'].fillna('무명상품').astype(str)
    elif '펀드명' in df.columns:
        names = df['펀드명'].fillna('무명상품').astype(str)
    elif '출처파일명' in df.columns:
        names = df['출처파일명'].apply(lambda x: str(x).split('.')[0] if pd.notnull(x) else '무명상품')
    else:
        names = [f"무명상품_{i}" for i in range(len(df))]

    # 최소 투자금액
    if '최고한도' in df.columns:
        min_invest = pd.to_numeric(df['최고한도'], errors='coerce').fillna(0)
        zero_mask = (min_invest == 0)
        if zero_mask.any():
            min_invest[zero_mask] = np.random.randint(100, 1000, zero_mask.sum())
    else:
        min_invest = np.random.randint(100, 1000, len(df))

    # 수익률(%) → 소수
    cand_cols = [c for c in df.columns if any(k in c for k in ["기본금리", "이자율", "세전"])]
    rate_col = cand_cols[0] if cand_cols else None

    if rate_col:
        raw = (df[rate_col].astype(str)
                          .str.replace(",", "", regex=False)
                          .str.extract(r"([\d\.]+)")[0])
        est_return = pd.to_numeric(raw, errors="coerce")
        rand_series = pd.Series(np.random.uniform(1.0, 8.0, len(df)), index=df.index)
        est_return = (est_return.fillna(rand_series) / 100.0).astype(float).round(4)
    else:
        est_return = pd.Series(np.round(np.random.uniform(0.01, 0.08, len(df)), 4), index=df.index)

    # 리스크
    if '위험등급' in df.columns:
        raw_risk = df['위험등급'].astype(str)
        risk = raw_risk.apply(lambda x: '높음' if ('5' in x or '4' in x) else ('중간' if '3' in x else '낮음'))
    else:
        risk = np.random.choice(['낮음','중간','높음'], len(df))

    duration = np.random.choice([6, 12, 24, 36], len(df))
    profile  = np.random.choice(['안정형','위험중립형','공격형'], len(df))

    out = pd.DataFrame({
        '상품명': names,
        '최소투자금액': min_invest.astype(int),
        '예상수익률': np.round(est_return, 4),
        '리스크': risk,
        '권장투자기간': duration,
        '투자성향': profile
    })
    return out[out['상품명'] != '무명상품'].drop_duplicates(subset=['상품명'])

def rule_based_filter(df: pd.DataFrame, user: dict) -> pd.DataFrame:
    risk_pref_map = {
        '안정형': ['낮음','중간'],
        '위험중립형': ['중간','낮음','높음'],
        '공격형': ['높음','중간']
    }
    allowed_risks = risk_pref_map.get(user['투자성향'], ['낮음','중간','높음'])

    filtered = df[
        (df['최소투자금액'] <= user['투자금액']) &
        (df['권장투자기간'] <= user['투자기간']) &
        (df['리스크'].isin(allowed_risks)) &
        (df['투자성향'] == user['투자성향'])
    ]
    if filtered.empty:
        filtered = df[
            (df['최소투자금액'] <= user['투자금액']) &
            (df['권장투자기간'] <= user['투자기간']) &
            (df['리스크'].isin(allowed_risks))
        ]
    return filtered.sort_values('예상수익률', ascending=False).head(200).reset_index(drop=True)

def _get_feature_vector(df: pd.DataFrame) -> np.ndarray:
    return np.vstack([
        df['최소투자금액'] / 1000.0,
        df['예상수익률'] * 100.0,
        df['권장투자기간'] / 12.0
    ]).T.astype('float32')

def _get_user_vector(user: dict) -> np.ndarray:
    return np.array([
        user['투자금액'] / 1000.0,
        user['목표월이자'],
        user['투자기간'] / 12.0
    ], dtype='float32').reshape(1, -1)

def _explain_product(row: pd.Series, user: dict) -> dict:
    expected_monthly = round((user['투자금액'] * float(row['예상수익률'])) / 12.0, 1)
    return {
        '상품명': row['상품명'],
        '월예상수익금(만원)': expected_monthly,
        '리스크': row['리스크'],
        '투자기간(개월)': int(row['권장투자기간']),
        '예상수익률(연)': f"{round(float(row['예상수익률'])*100,2)}%"
    }

def recommend_products(processed_df: pd.DataFrame, user: dict, topk: int = 3):
    filtered = rule_based_filter(processed_df, user)
    if filtered.empty:
        return pd.DataFrame({'메시지': ['조건에 맞는 상품이 없어요 😢']}), None

    filtered = filtered.drop_duplicates(subset=['상품명'])
    X = _get_feature_vector(filtered)
    index = faiss.IndexFlatL2(X.shape[1])
    index.add(X)

    user_vec = _get_user_vector(user)
    _, idx = index.search(user_vec, k=min(topk, len(filtered)))
    rec = filtered.iloc[idx[0]].drop_duplicates(subset=['상품명']).head(topk).reset_index(drop=True)
    results = pd.DataFrame([_explain_product(row, user) for _, row in rec.iterrows()])
    return results, index

processed_products = preprocess_products(raw_products)

# ================================
# 설문/분류 공통
# ================================
QUESTIONS = [
    ("나이를 입력해주세요.", "number", "age"),
    ("성별을 선택해주세요.", "select", "gender", ["남성", "여성"]),
    ("가구원 수를 입력해주세요.", "number", "family_size"),
    ("피부양자가 있나요?", "select", "dependents", ["예", "아니오"]),
    ("현재 보유한 금융자산(만원)을 입력해주세요.", "number", "assets"),
    ("월 수령하는 연금 금액(만원)을 입력해주세요.", "number", "pension"),
    ("월 평균 지출비(만원)은 얼마인가요?", "number", "living_cost"),
    ("월 평균 소득은 얼마인가요?", "number", "income"),
    ("투자 성향을 선택해주세요.", "select", "risk",
     ["안정형", "안정추구형", "위험중립형", "적극투자형", "공격투자형"]),
]

def render_survey():
    st.markdown('<div class="section-title">📝 설문</div>', unsafe_allow_html=True)
    answers = {}
    for q in QUESTIONS:
        title, kind, key = q[0], q[1], q[2]
        if kind == "number":
            answers[key] = st.number_input(title, min_value=0, step=1, key=f"q_{key}")
        elif kind == "select":
            answers[key] = st.selectbox(title, q[3], key=f"q_{key}")
    return answers

def map_survey_to_model_input(r):
    gender = 0 if r["gender"] == "남성" else 1
    dependents = 1 if r["dependents"] == "예" else 0
    risk_map = {"안정형": 0, "안정추구형": 1, "위험중립형": 2, "적극투자형": 3, "공격투자형": 4}
    risk = risk_map[r["risk"]]
    arr = np.array([[
        float(r["age"]), gender, float(r["family_size"]), dependents,
        float(r["assets"]), float(r["pension"]), float(r["living_cost"]),
        float(r["income"]), risk
    ]])
    return arr

# ================================
# 라우팅 상태
# ================================
route = st.session_state.setdefault("route", "home")  # home | pension | survey
ss = st.session_state
ss.setdefault("flow", "choose")      # (survey 내부) choose → predict → ask → recommend
ss.setdefault("pred_amount", None)
ss.setdefault("answers", {})

# ================================
# 페이지: 홈 (큰 타일)
# ================================
def page_home():
    st.markdown('<div class="big-title">시니어 금융 서비스</div>', unsafe_allow_html=True)
    st.markdown('<div class="help">원하는 기능을 선택하세요. 버튼은 크고 단순합니다.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.container().markdown("<div class='tile-blue'>", unsafe_allow_html=True)
        if st.button("🏦 연금 계산하기", key="go_pension"):
            st.session_state.route = "pension"
            st.rerun()
        st.container().markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.container().markdown("<div class='tile-yellow'>", unsafe_allow_html=True)
        if st.button("🛍️ 상품 추천받기", key="go_survey"):
            st.session_state.route = "survey"
            # 설문 첫 진입시 플로우 초기화
            for k,v in {"flow":"choose","pred_amount":None,"answers":{}}.items():
                st.session_state[k]=v
            st.rerun()
        st.container().markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.info("팁: 설문을 마치면 **금융 유형**과 함께 **맞춤 상품 3개**를 보여드립니다.")

# ================================
# 페이지: 연금 계산하기
# ================================
def page_pension():
    st.markdown('<div class="big-title">🏦 연금 계산하기</div>', unsafe_allow_html=True)
    st.caption("월 연금 수령액과 예상 수령 기간을 입력하면 총 수령액과 부족분을 계산합니다.")

    with st.form("pension_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            monthly_pension = st.number_input("월 연금 수령액 (만원)", min_value=0, step=10, value=120)
            monthly_expense = st.number_input("월 생활비 (만원)", min_value=0, step=10, value=180)
        with col2:
            years = st.number_input("예상 수령 기간 (년)", min_value=1, step=1, value=20)
            discount_rate = st.number_input("연 할인율(%) (선택)", min_value=0.0, step=0.5, value=0.0)
        submitted = st.form_submit_button("계산하기")

    if submitted:
        months = years * 12
        total_nominal = monthly_pension * months
        if discount_rate and discount_rate > 0:
            r = (discount_rate/100)/12
            pv = monthly_pension * (1 - (1+r)**(-months)) / r
        else:
            pv = total_nominal
        gap = monthly_pension - monthly_expense

        c1, c2 = st.columns(2)
        with c1:
            st.metric("월 연금 ▶ 생활비 대비", f"{gap:+.0f} 만원/월")
            st.metric("총 수령액(명목)", f"{total_nominal:,.0f} 만원")
        with c2:
            st.metric("연금 현재가치(PV)", f"{pv:,.0f} 만원")
            st.metric("예상 수령 기간", f"{years} 년")

        if gap < 0:
            st.warning("매월 **생활비가 부족**합니다. 지출 재구성, 금리 상향, 월지급식 상품 등을 검토하세요.")
        else:
            st.info("매월 **여유**가 있습니다. 원금 보전형 + 생활 안정형 비중 유지 권장.")

    st.markdown("---")
    if st.button("⬅️ 홈으로"):
        st.session_state.route = "home"
        st.rerun()

# ================================
# 페이지: 설문+유형분류+추천 (한 흐름)
# ================================
def page_survey_flow():
    st.markdown('<div class="big-title">🛍️ 상품 추천받기</div>', unsafe_allow_html=True)

    # 1) 연금 수령 여부
    if ss.flow == "choose":
        st.markdown("### 1️⃣ 현재 연금을 받고 계신가요?")
        choice = st.radio("연금 수령 여부", ["선택하세요", "예(수령 중)", "아니오(미수령)"], index=0, horizontal=True)
        if choice == "예(수령 중)":
            ss.flow = "ask"
            st.rerun()
        elif choice == "아니오(미수령)":
            ss.flow = "predict"
            st.rerun()

    # 2-1) 미수령자 → 간단 연금 예측(보유 reg_model 사용)
    if ss.flow == "predict":
        st.subheader("📈 연금 예측")
        income = st.number_input("평균 월소득(만원)", min_value=0, step=1, key="pred_income")
        years  = st.number_input("국민연금 가입기간(년)", min_value=0, max_value=50, step=1, key="pred_years")
        if st.button("예측하기"):
            X = pd.DataFrame([{"평균월소득(만원)": income, "가입기간(년)": years}])
            amount = round(float(reg_model.predict(X)[0]), 1)
            ss.pred_amount = amount

            def classify_pension_type(a):
                if a >= 90: return "완전노령연금"
                if a >= 60: return "조기노령연금"
                if a >= 30: return "감액노령연금"
                return "특례노령연금"

            ptype = classify_pension_type(amount)
            explains = {
                "조기노령연금": "만 60세부터 수령 가능하나 최대 30% 감액될 수 있어요.",
                "완전노령연금": "만 65세부터 감액 없이 정액 수령 가능해요.",
                "감액노령연금": "일정 조건 미충족 시 감액되어 수령됩니다.",
                "특례노령연금": "가입기간이 짧아도 일정 기준 충족 시 수령 가능."
            }
            st.success(f"💰 예측 월 수령액: **{amount}만원**  | 유형: **{ptype}**")
            st.info(explains[ptype])
            ss.flow = "ask"
            st.rerun()

    # 2-2) 수령자/미수령자 공통 설문 → 유형 분류
    if ss.flow == "ask":
        answers = render_survey()
        if st.button("유형 분류하기"):
            arr = map_survey_to_model_input(answers)
            pred = survey_model.predict(arr)
            label = survey_encoder.inverse_transform(pred)[0]

            proba = survey_model.predict_proba(arr)
            proba_df = pd.DataFrame(proba, columns=survey_encoder.classes_)
            predicted_proba = float(proba_df[label].values[0])

            st.success(f"🧾 예측된 금융 유형: **{label}** (확률 {predicted_proba*100:.1f}%)")
            st.bar_chart(proba_df.T)

            ss.answers = answers
            ss.flow = "recommend"
            st.experimental_rerun()

    # 3) 추천
    if ss.flow == "recommend":
        st.markdown("---")
        st.subheader("🧲 금융상품 추천")
        invest_amount  = st.number_input("투자금액(만원)", min_value=10, step=10, value=500)
        invest_period  = st.selectbox("투자기간(개월)", [6, 12, 24, 36], index=1)
        risk_choice    = st.selectbox("리스크 허용도", ["안정형", "위험중립형", "공격형"], index=1)
        target_monthly = st.number_input("목표 월이자(만원)", min_value=1, step=1, value=10)

        if st.button("추천 보기"):
            user_pref = {
                '투자금액': invest_amount,
                '투자기간': invest_period,
                '투자성향': risk_choice,
                '목표월이자': target_monthly
            }
            rec_df, idx = recommend_products(processed_products, user_pref)

            if "메시지" in rec_df.columns:
                st.warning(rec_df.iloc[0, 0])
            else:
                st.dataframe(rec_df, use_container_width=True)
                csv_bytes = rec_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("추천 결과 CSV 다운로드", csv_bytes, "recommendations.csv", "text/csv")

                # 경량 인덱스 저장(원하면)
                faiss.write_index(idx, os.path.join(MODELS_DIR, "faiss_index.idx"))
                st.caption("FAISS 인덱스가 저장되었습니다: faiss_index.idx")

    st.markdown("---")
    if st.button("⬅️ 홈으로"):
        st.session_state.route = "home"
        # 설문 흐름 초기화
        for k in ["flow", "pred_amount", "answers"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

# ================================
# 라우팅 실행
# ================================
if st.session_state.route == "home":
    page_home()
elif st.session_state.route == "pension":
    page_pension()
elif st.session_state.route == "survey":
    page_survey_flow()

