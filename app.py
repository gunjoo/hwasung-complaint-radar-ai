from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from services.analyzer import (
    CATEGORY_RULES,
    analyze_complaint,
    build_action_card,
    build_prevention_alerts,
    get_repeated_keyword_counts,
)


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "sample_complaints.csv"
PUBLIC_PARKING_PATH = BASE_DIR / "data" / "public_parking_hwasung.csv"
PUBLIC_SPORTS_PATH = BASE_DIR / "data" / "public_sports_facilities_hwasung.csv"
DISCLAIMER = "본 데이터는 공모전 시연용 가상 데이터이며, 실제 국민신문고·민원 데이터와 무관함"
RISK_NOTICE = "위험도 판단은 법적 판단이나 최종 판단이 아니라 담당자 우선 확인을 위한 참고 지표입니다."


st.set_page_config(
    page_title="화성 민원 레이더 AI",
    page_icon="📡",
    layout="wide",
)


st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .notice {
        border: 1px solid #d9e2ec;
        border-left: 6px solid #2563eb;
        background: #f8fafc;
        padding: 0.85rem 1rem;
        border-radius: 8px;
        color: #243b53;
        margin-bottom: 1rem;
    }
    .soft-card {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        background: #ffffff;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        min-height: 120px;
    }
    .card-title {
        color: #334155;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .muted {
        color: #64748b;
        font-size: 0.92rem;
    }
    .tag {
        display: inline-block;
        padding: 0.15rem 0.45rem;
        border-radius: 6px;
        background: #eef2ff;
        color: #3730a3;
        margin-right: 0.25rem;
        margin-bottom: 0.25rem;
        font-size: 0.84rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


@st.cache_data
def load_public_parking_data():
    parking = pd.read_csv(PUBLIC_PARKING_PATH)
    numeric_columns = ["면수", "장애면수", "정기면수", "재입장시간", "위도", "경도"]
    for column in numeric_columns:
        parking[column] = pd.to_numeric(parking[column], errors="coerce")
    parking["권역"] = parking["주소"].fillna("").str.extract(r"화성시\s+([^\s]+)", expand=False).fillna("기타")
    return parking


@st.cache_data
def load_public_sports_data():
    sports = pd.read_csv(PUBLIC_SPORTS_PATH)
    sports = sports.drop(columns=["관리자연락처"], errors="ignore")
    numeric_columns = ["면수", "시설면적", "총 면적", "시설수", "총면수", "총시설면적"]
    for column in numeric_columns:
        if column in sports.columns:
            sports[column] = pd.to_numeric(sports[column], errors="coerce")
    if "위치" in sports.columns:
        sports["권역"] = sports["위치"].fillna("").str.extract(r"^([가-힣]+[읍면동])", expand=False).fillna("기타")
    return sports


def bool_series(series):
    return series.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def make_count_chart(dataframe, column, title, color="#2563eb"):
    counts = dataframe[column].value_counts().reset_index()
    counts.columns = [column, "count"]
    fig = px.bar(counts, x=column, y="count", text="count", title=title)
    fig.update_traces(marker_color=color, textposition="outside")
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis_title="",
        yaxis_title="건수",
        showlegend=False,
    )
    return fig


def render_notice():
    st.markdown(f"<div class='notice'><strong>{DISCLAIMER}</strong><br>{RISK_NOTICE}</div>", unsafe_allow_html=True)


def render_analysis_result(result):
    cols = st.columns(4)
    cols[0].metric("민원 분야", result["category"])
    cols[1].metric("세부 분야", result["sub_category"])
    cols[2].metric("긴급도", result["urgency"])
    cols[3].metric("담당 후보", result["owner_candidate"])

    st.subheader("분석 결과")
    st.write(result["summary"])
    st.markdown("".join(f"<span class='tag'>{keyword}</span>" for keyword in result["keywords"]), unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.markdown("#### 시민 답변 초안")
        st.info(result["citizen_reply"])
        st.markdown("#### 재발 방지 제안")
        st.success(result["prevention_suggestion"])
    with right:
        st.markdown("#### 담당자 내부 처리 메모")
        st.warning(result["internal_memo"])
        st.markdown("#### 위험도 판단 사유")
        st.caption(RISK_NOTICE)
        st.error(result["risk_reason"])


def render_alert_card(alert):
    st.markdown(
        f"""
        <div class="soft-card">
            <div class="card-title">{alert["title"]}</div>
            <div class="muted">분야: {alert["category"]} · 수준: {alert["level"]}</div>
            <p>{alert["message"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dashboard_tab(dataframe):
    st.subheader("대시보드")
    metric_cols = st.columns(4)
    metric_cols[0].metric("전체 민원 건수", f"{len(dataframe):,}건")
    metric_cols[1].metric("반복 민원", f"{bool_series(dataframe['is_repeat']).sum():,}건")
    metric_cols[2].metric("우선 확인", f"{bool_series(dataframe['risk_flag']).sum():,}건")
    metric_cols[3].metric("분야 수", f"{dataframe['category'].nunique():,}개")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(make_count_chart(dataframe, "category", "분야별 민원 건수", "#2563eb"), width="stretch")
        st.plotly_chart(make_count_chart(dataframe, "facility", "시설별 민원 건수", "#0891b2"), width="stretch")
    with right:
        urgency_order = ["일반", "확인 필요", "주의", "즉시 확인 필요"]
        urgency_counts = dataframe["urgency"].value_counts().reindex(urgency_order, fill_value=0).reset_index()
        urgency_counts.columns = ["urgency", "count"]
        fig = px.bar(urgency_counts, x="urgency", y="count", text="count", title="긴급도별 민원 건수")
        fig.update_traces(marker_color=["#94a3b8", "#38bdf8", "#f59e0b", "#ef4444"], textposition="outside")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="", yaxis_title="건수")
        st.plotly_chart(fig, width="stretch")

        keyword_counts = pd.DataFrame(get_repeated_keyword_counts(dataframe), columns=["keyword", "count"])
        fig_keywords = px.bar(keyword_counts, x="count", y="keyword", orientation="h", text="count", title="반복 키워드 TOP 10")
        fig_keywords.update_traces(marker_color="#7c3aed", textposition="outside")
        fig_keywords.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="건수", yaxis_title="")
        st.plotly_chart(fig_keywords, width="stretch")

    st.subheader("AI 예방 알림 카드")
    alerts = build_prevention_alerts(dataframe)
    alert_cols = st.columns(min(3, len(alerts)) or 1)
    for index, alert in enumerate(alerts):
        with alert_cols[index % len(alert_cols)]:
            render_alert_card(alert)


def complaint_analysis_tab():
    st.subheader("민원 AI 분석")
    st.caption("첫 버전은 외부 AI API 없이 키워드 기반 규칙으로 분석합니다.")

    examples = {
        "주차 혼잡 예시": "주말 행사 시간마다 주차장이 만차라 차량 진입이 어렵고 보행자 안전도 걱정됩니다.",
        "아동 안전 예시": "어린이들이 이용하는 계단 바닥이 미끄러워 넘어짐 사고가 날까 걱정됩니다.",
        "CCTV/개인정보 예시": "휴게 공간 CCTV 촬영 범위가 넓어 사생활과 개인정보 침해가 우려됩니다.",
    }

    if "complaint_input" not in st.session_state:
        st.session_state.complaint_input = examples["주차 혼잡 예시"]

    button_cols = st.columns(3)
    for index, (label, value) in enumerate(examples.items()):
        if button_cols[index].button(label, width="stretch"):
            st.session_state.complaint_input = value

    text = st.text_area(
        "민원 문장 입력",
        key="complaint_input",
        height=130,
        placeholder="예: 주차장이 너무 혼잡해서 차량 진입이 어렵고 안전이 걱정됩니다.",
    )

    if st.button("분석하기", type="primary", width="stretch"):
        result = analyze_complaint(text)
        render_analysis_result(result)
    else:
        st.info("예시 버튼을 누르거나 민원 문장을 입력한 뒤 분석하기를 선택하세요.")


def radar_tab(dataframe):
    st.subheader("반복 민원 레이더")
    summary = dataframe.groupby("category").agg(
        total=("id", "count"),
        repeats=("is_repeat", lambda values: bool_series(values).sum()),
        risks=("risk_flag", lambda values: bool_series(values).sum()),
    ).reset_index()
    summary["attention_score"] = summary["repeats"] * 2 + summary["risks"] * 3 + summary["total"]
    summary = summary.sort_values("attention_score", ascending=False)

    cols = st.columns(4)
    for index, row in enumerate(summary.head(8).itertuples(index=False)):
        with cols[index % 4]:
            level = "주의 필요" if row.risks >= 2 else "반복 관찰"
            st.markdown(
                f"""
                <div class="soft-card">
                    <div class="card-title">{row.category}</div>
                    <div class="muted">{level}</div>
                    <p>전체 {row.total}건 · 반복 {row.repeats}건 · 우선 확인 {row.risks}건</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.dataframe(summary, width="stretch", hide_index=True)


def public_data_tab(dataframe, parking, sports):
    st.subheader("공공데이터 연계")
    st.caption("공개 공공데이터를 민원 예방 분석의 배경 정보로 활용합니다. 실제 민원 원문이나 개인정보는 사용하지 않습니다.")

    parking_complaints = dataframe[dataframe["category"] == "주차"]
    facility_complaints = dataframe[dataframe["category"].isin(["안전", "시설이용", "프로그램", "대관"])]
    sports_total = int(sports["시설수"].fillna(0).sum()) if "시설수" in sports.columns else len(sports)
    sports_type_count = sports["시설명"].nunique()
    metric_cols = st.columns(4)
    metric_cols[0].metric("공영주차장 구간", f"{len(parking):,}개")
    metric_cols[1].metric("총 주차면수", f"{int(parking['면수'].fillna(0).sum()):,}면")
    metric_cols[2].metric("체육시설 항목", f"{sports_total:,}개")
    metric_cols[3].metric("시설 관련 가상 민원", f"{len(facility_complaints):,}건")

    st.markdown(
        """
        <div class="notice">
            <strong>연계 데이터 출처</strong><br>
            경기도 화성시_공영주차장 정보_20251117, 화성도시공사_화성시 체육시설 현황_20251231 CSV 공개 데이터 기반입니다.
            주차장·체육시설 인프라 현황을 반복 민원 해석의 참고 정보로만 사용합니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    public_tabs = st.tabs(["주차 인프라", "체육시설 인프라", "민원 연결 해석"])
    with public_tabs[0]:
        left, right = st.columns([1.1, 0.9])
        with left:
            by_area = parking.groupby("권역", as_index=False)["면수"].sum().sort_values("면수", ascending=False)
            fig_area = px.bar(by_area, x="권역", y="면수", text="면수", title="권역별 공영주차장 면수")
            fig_area.update_traces(marker_color="#0f766e", textposition="outside")
            fig_area.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="", yaxis_title="면수")
            st.plotly_chart(fig_area, width="stretch")

            top_parking = parking.sort_values("면수", ascending=False).head(10)
            fig_top = px.bar(top_parking, x="면수", y="구간이름", orientation="h", text="면수", title="주차면수 상위 10개 구간")
            fig_top.update_traces(marker_color="#2563eb", textposition="outside")
            fig_top.update_layout(height=380, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="면수", yaxis_title="")
            st.plotly_chart(fig_top, width="stretch")

        with right:
            map_data = parking.dropna(subset=["위도", "경도"]).rename(columns={"위도": "latitude", "경도": "longitude"})
            st.markdown("#### 공영주차장 위치")
            st.map(map_data[["latitude", "longitude"]], size=25)

        st.markdown("#### 공영주차장 공개 데이터 미리보기")
        parking_preview = ["구간이름", "면수", "장애면수", "정기면수", "주소", "재입장시간", "데이터기준일자"]
        st.dataframe(parking[parking_preview], width="stretch", hide_index=True)

    with public_tabs[1]:
        left, right = st.columns(2)
        with left:
            if "시설수" in sports.columns:
                facility_counts = sports[["시설명", "시설수"]].sort_values("시설수", ascending=False).head(12)
                facility_counts.columns = ["시설명", "count"]
            else:
                facility_counts = sports["시설명"].value_counts().head(12).reset_index()
                facility_counts.columns = ["시설명", "count"]
            fig_facility = px.bar(facility_counts, x="count", y="시설명", orientation="h", text="count", title="체육시설 유형 TOP 12")
            fig_facility.update_traces(marker_color="#7c3aed", textposition="outside")
            fig_facility.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="개수", yaxis_title="")
            st.plotly_chart(fig_facility, width="stretch")

        with right:
            if "총면수" in sports.columns:
                facility_units = sports[["시설명", "총면수"]].sort_values("총면수", ascending=False).head(12)
                fig_units = px.bar(facility_units, x="총면수", y="시설명", orientation="h", text="총면수", title="체육시설 유형별 총 면수")
                fig_units.update_traces(marker_color="#ea580c", textposition="outside")
                fig_units.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="면수", yaxis_title="")
                st.plotly_chart(fig_units, width="stretch")
            else:
                park_counts = sports["공원명"].value_counts().head(10).reset_index()
                park_counts.columns = ["공원명", "count"]
                fig_park = px.bar(park_counts, x="count", y="공원명", orientation="h", text="count", title="시설 수 상위 공원")
                fig_park.update_traces(marker_color="#ea580c", textposition="outside")
                fig_park.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="시설 수", yaxis_title="")
                st.plotly_chart(fig_park, width="stretch")

        st.markdown("#### 체육시설 공개 데이터 미리보기")
        sports_preview = [column for column in ["시설명", "시설수", "총면수", "총시설면적", "공원명", "위치", "면수", "시설면적", "총 면적", "관리기관", "데이터기준일자"] if column in sports.columns]
        st.dataframe(sports[sports_preview], width="stretch", hide_index=True)

    with public_tabs[2]:
        left, right = st.columns(2)
        with left:
            st.markdown("#### 주차 민원 연결")
            st.info(
                f"가상 주차 민원 {len(parking_complaints)}건과 공영주차장 {len(parking)}개 구간, "
                f"총 {int(parking['면수'].fillna(0).sum()):,}면 정보를 함께 확인합니다. "
                "반복 혼잡 민원 발생 시 안내 강화, 분산 주차 유도, 주변 주차장 안내 개선을 검토할 수 있습니다."
            )
        with right:
            st.markdown("#### 시설·대관·안전 민원 연결")
            st.success(
                f"안전·시설이용·프로그램·대관 관련 가상 민원 {len(facility_complaints)}건과 "
                f"체육시설 공개 데이터 {sports_total}개 항목, {sports_type_count}개 유형을 함께 봅니다. "
                "시설 유형별 반복 민원, 대관 안내 개선, 안전 점검 우선순위 도출에 활용할 수 있습니다."
            )


def action_cards_tab():
    st.subheader("담당자 조치카드")
    category = st.selectbox("민원 유형 선택", list(CATEGORY_RULES.keys()))
    card = build_action_card(category)

    cols = st.columns([1, 1])
    with cols[0]:
        st.metric("담당 후보", card["owner_candidate"])
        st.markdown("#### 확인해야 할 조치사항")
        for item in card["checklist"]:
            st.checkbox(item, value=False)
    with cols[1]:
        st.markdown("#### 시민 답변")
        st.info(card["citizen_reply"])
        st.markdown("#### 내부 검토 메모")
        st.warning(card["internal_memo"])
        st.markdown("#### 재발 방지 제안")
        st.success(card["prevention_suggestion"])


def intro_tab():
    st.subheader("솔루션 소개")
    st.markdown(
        """
        **화성 민원 레이더 AI**는 국민신문고를 대체하는 접수 시스템이 아닙니다.

        이 프로토타입은 민원 접수 이후 단계에서 가상 생활불편 민원을 분석해 반복 이슈,
        담당자 우선 확인 신호, 시민 답변 표준문안, 내부 처리 메모, 예방 알림을 보여주는
        공모전 시연용 도구입니다.
        """
    )
    st.markdown("#### 핵심 원칙")
    st.write("- 실제 민원 데이터, 개인정보, 내부 시스템 정보는 사용하지 않습니다.")
    st.write("- 모든 분석은 외부 AI API가 아닌 키워드 기반 규칙으로 동작합니다.")
    st.write("- 공개 공공데이터는 시설·인프라 현황을 파악하기 위한 참고 정보로만 활용합니다.")
    st.write("- 위험도 표시는 담당자 우선 확인을 돕는 참고 지표입니다.")
    st.write("- 향후 AI API를 붙일 경우에도 비식별화와 보안 검토가 선행되어야 합니다.")


def main():
    dataframe = load_data()
    parking = load_public_parking_data()
    sports = load_public_sports_data()
    st.title("화성 민원 레이더 AI")
    render_notice()

    tabs = st.tabs(["대시보드", "민원 AI 분석", "반복 민원 레이더", "공공데이터 연계", "담당자 조치카드", "솔루션 소개"])
    with tabs[0]:
        dashboard_tab(dataframe)
    with tabs[1]:
        complaint_analysis_tab()
    with tabs[2]:
        radar_tab(dataframe)
    with tabs[3]:
        public_data_tab(dataframe, parking, sports)
    with tabs[4]:
        action_cards_tab()
    with tabs[5]:
        intro_tab()


if __name__ == "__main__":
    main()
