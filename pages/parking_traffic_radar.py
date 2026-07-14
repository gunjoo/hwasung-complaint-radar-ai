from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
COMPLAINTS_PATH = BASE_DIR / "data" / "sample_complaints.csv"
PARKING_PATH = BASE_DIR / "data" / "public_parking_hwasung.csv"


st.set_page_config(page_title="주차·교통 민원 밀집도 레이더", page_icon="🚗", layout="wide")


st.markdown(
    """
    <style>
    .main .block-container { max-width: 1180px; padding-top: 1.5rem; }
    .notice {
        border: 1px solid #dbeafe; border-left: 6px solid #2563eb; background: #eff6ff;
        padding: 0.9rem 1rem; border-radius: 16px; color: #243b53; margin-bottom: 1rem;
    }
    .soft-card {
        border: 1px solid #e2e8f0; border-radius: 20px; padding: 1.08rem;
        background: rgba(255,255,255,0.96); box-shadow: 0 12px 32px rgba(15,23,42,0.07);
        min-height: 132px;
    }
    .card-title { color: #0f172a; font-weight: 800; margin-bottom: 0.35rem; }
    .muted { color: #64748b; font-size: 0.92rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    complaints = pd.read_csv(COMPLAINTS_PATH)
    parking = pd.read_csv(PARKING_PATH)
    for column in ["면수", "장애면수", "정기면수", "위도", "경도"]:
        if column in parking.columns:
            parking[column] = pd.to_numeric(parking[column], errors="coerce")
    return complaints, parking


def to_bool(series):
    return series.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def infer_area(text):
    value = str(text or "")
    if "동탄" in value:
        return "동탄권역"
    if any(keyword in value for keyword in ["서부", "남양", "송산", "서신", "마도", "매송", "비봉", "새솔"]):
        return "서부권역"
    if any(keyword in value for keyword in ["향남", "봉담", "팔탄", "양감", "정남", "우정", "장안"]):
        return "남부권역"
    if any(keyword in value for keyword in ["이음터", "복합", "중부", "병점", "반월", "기배", "화산", "진안"]):
        return "중부권역"
    if any(keyword in value for keyword in ["도서관", "공공"]):
        return "공통권역"
    return "기타권역"


def build_density(complaints, parking):
    traffic_keywords = ["주차", "불법주차", "불법주정차", "주정차", "교통", "혼잡", "차량", "만차", "진입", "출차"]
    pattern = "|".join(traffic_keywords)
    text = complaints["complaint_text"].fillna("").astype(str)
    keywords = complaints["keywords"].fillna("").astype(str)
    mask = (complaints["category"] == "주차") | text.str.contains(pattern, case=False, regex=True) | keywords.str.contains(pattern, case=False, regex=True)

    traffic = complaints[mask].copy()
    traffic["권역"] = traffic["facility"].apply(infer_area)

    complaint_summary = traffic.groupby("권역").agg(
        주차교통민원=("id", "count"),
        반복민원=("is_repeat", lambda values: to_bool(values).sum()),
        우선확인=("risk_flag", lambda values: to_bool(values).sum()),
    ).reset_index()

    parking_area = parking.copy()
    parking_area["권역"] = parking_area["주소"].apply(infer_area)
    parking_summary = parking_area.groupby("권역").agg(
        공영주차장수=("구간이름", "count"),
        총주차면수=("면수", "sum"),
    ).reset_index()

    areas = pd.DataFrame({"권역": sorted(set(complaint_summary["권역"]).union(set(parking_summary["권역"])))})
    density = areas.merge(complaint_summary, on="권역", how="left").merge(parking_summary, on="권역", how="left")
    for column in ["주차교통민원", "반복민원", "우선확인", "공영주차장수", "총주차면수"]:
        density[column] = density[column].fillna(0).astype(int)
    density["검토권고"] = density["반복민원"].apply(lambda count: "현장 확인 및 사전 안내 강화 권고" if count >= 2 else "모니터링")
    return traffic, density.sort_values(["반복민원", "주차교통민원", "총주차면수"], ascending=False)


complaints_df, parking_df = load_data()
traffic_df, density_df = build_density(complaints_df, parking_df)
recommended_df = density_df[density_df["검토권고"] == "현장 확인 및 사전 안내 강화 권고"]

st.title("🚗 주차·교통 민원 밀집도 레이더")
st.markdown(
    """
    <div class="notice">
    기존 가상 민원 데이터와 화성시 공영주차장 공개 데이터를 함께 활용합니다.
    단속차량 배치나 행정 처분을 단정하지 않고, 담당부서 검토 권고 수준으로만 표현합니다.
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(4)
metric_cols[0].metric("주차·교통 민원", f"{len(traffic_df):,}건")
metric_cols[1].metric("반복 민원", f"{int(density_df['반복민원'].sum()):,}건")
metric_cols[2].metric("공영주차장", f"{int(density_df['공영주차장수'].sum()):,}개")
metric_cols[3].metric("총 주차면수", f"{int(density_df['총주차면수'].sum()):,}면")

if not recommended_df.empty:
    st.subheader("검토 권고 카드")
    cards = st.columns(min(3, len(recommended_df)))
    for index, row in enumerate(recommended_df.itertuples(index=False)):
        with cards[index % len(cards)]:
            st.markdown(
                f"""
                <div class="soft-card">
                    <div class="card-title">🚗 {row.권역} 반복 신호</div>
                    <div class="muted">가상 민원 {row.주차교통민원}건 · 반복 {row.반복민원}건</div>
                    <p>공영주차장 {row.공영주차장수}개, 총 {row.총주차면수:,}면 현황과 함께 담당부서 검토가 필요합니다.</p>
                    <p><strong>권고:</strong> 현장 확인 및 사전 안내 강화 권고</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("현재 샘플 기준 반복 주차·교통 민원이 뚜렷한 권역은 없습니다.")

left, right = st.columns([1.05, 0.95])
with left:
    fig_density = px.bar(
        density_df,
        x="권역",
        y=["주차교통민원", "반복민원"],
        barmode="group",
        title="권역별 주차·교통 민원 밀집도",
    )
    fig_density.update_layout(height=390, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="", yaxis_title="건수")
    st.plotly_chart(fig_density, width="stretch")

with right:
    fig_parking = px.bar(
        density_df.sort_values("총주차면수", ascending=False),
        x="총주차면수",
        y="권역",
        orientation="h",
        text="총주차면수",
        title="권역별 공영주차장 총 주차면수",
    )
    fig_parking.update_traces(marker_color="#0f766e", textposition="outside")
    fig_parking.update_layout(height=390, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="면수", yaxis_title="")
    st.plotly_chart(fig_parking, width="stretch")

st.subheader("권역별 연결 현황")
st.dataframe(density_df, width="stretch", hide_index=True)

st.subheader("주차·교통 가상 민원 목록")
preview_columns = ["id", "date", "facility", "권역", "urgency", "complaint_text", "keywords", "expected_role"]
st.dataframe(traffic_df[preview_columns], width="stretch", hide_index=True)
