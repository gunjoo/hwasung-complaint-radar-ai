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
    :root {
        --radar-blue: #2563eb;
        --radar-navy: #172554;
        --radar-sky: #eff6ff;
        --radar-line: #dbeafe;
        --radar-text: #0f172a;
        --radar-muted: #64748b;
    }
    html, body, [class*="css"] {
        font-family: "Pretendard", "Noto Sans KR", "Segoe UI", sans-serif;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 28rem),
            linear-gradient(180deg, #f8fbff 0%, #ffffff 32%, #f8fafc 100%);
    }
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1220px;
    }
    .hero {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(191, 219, 254, 0.95);
        border-radius: 28px;
        padding: 2rem 2.2rem;
        margin-bottom: 1.2rem;
        background:
            linear-gradient(135deg, rgba(30, 64, 175, 0.96), rgba(37, 99, 235, 0.90)),
            radial-gradient(circle at right top, rgba(125, 211, 252, 0.42), transparent 18rem);
        color: #ffffff;
        box-shadow: 0 22px 50px rgba(37, 99, 235, 0.20);
    }
    .hero:after {
        content: "";
        position: absolute;
        right: -5rem;
        top: -5rem;
        width: 16rem;
        height: 16rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.10);
    }
    .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.14);
        border: 1px solid rgba(255, 255, 255, 0.24);
        font-size: 0.88rem;
        font-weight: 700;
    }
    .hero-title {
        margin: 0.7rem 0 0.35rem 0;
        font-size: clamp(2rem, 4vw, 3.3rem);
        font-weight: 850;
        letter-spacing: -0.05em;
        line-height: 1.08;
    }
    .hero-subtitle {
        max-width: 780px;
        margin: 0;
        color: #dbeafe;
        font-size: 1.05rem;
        line-height: 1.7;
    }
    .hero-flow {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin-top: 1.2rem;
    }
    .flow-chip {
        padding: 0.45rem 0.7rem;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.13);
        border: 1px solid rgba(255, 255, 255, 0.18);
        color: #eff6ff;
        font-size: 0.9rem;
        font-weight: 650;
    }
    .notice {
        border: 1px solid var(--radar-line);
        border-left: 6px solid var(--radar-blue);
        background: rgba(239, 246, 255, 0.86);
        padding: 0.9rem 1rem;
        border-radius: 16px;
        color: #243b53;
        margin-bottom: 1rem;
    }
    .section-head {
        margin: 1rem 0 0.8rem;
    }
    .section-eyebrow {
        color: var(--radar-blue);
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .section-title {
        color: var(--radar-text);
        font-size: 1.55rem;
        font-weight: 850;
        letter-spacing: -0.035em;
        margin: 0;
    }
    .section-desc {
        color: var(--radar-muted);
        margin: 0.25rem 0 0;
        line-height: 1.65;
    }
    .soft-card {
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 1.08rem;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: 0 12px 32px rgba(15, 23, 42, 0.07);
        min-height: 120px;
    }
    .soft-card:hover {
        border-color: #bfdbfe;
        box-shadow: 0 16px 40px rgba(37, 99, 235, 0.12);
    }
    .card-title {
        color: var(--radar-text);
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .muted {
        color: #64748b;
        font-size: 0.92rem;
    }
    .tag {
        display: inline-block;
        padding: 0.22rem 0.52rem;
        border-radius: 999px;
        background: #eef2ff;
        color: #3730a3;
        margin-right: 0.25rem;
        margin-bottom: 0.25rem;
        font-size: 0.84rem;
        font-weight: 700;
    }
    .metric-card {
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 1rem;
        min-height: 118px;
        background: linear-gradient(180deg, #ffffff, #f8fafc);
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
    }
    .metric-label {
        color: var(--radar-muted);
        font-size: 0.84rem;
        font-weight: 750;
    }
    .metric-value {
        color: var(--radar-text);
        font-size: 1.8rem;
        line-height: 1.1;
        font-weight: 850;
        margin-top: 0.45rem;
    }
    .metric-help {
        color: #94a3b8;
        font-size: 0.82rem;
        margin-top: 0.45rem;
    }
    .step-card {
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 1rem;
        background: #ffffff;
        min-height: 132px;
    }
    .step-no {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 1.8rem;
        height: 1.8rem;
        border-radius: 999px;
        background: var(--radar-blue);
        color: white;
        font-weight: 850;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 0.35rem;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
    }
    .stTabs [data-baseweb="tab"] {
        height: 2.7rem;
        border-radius: 14px;
        padding: 0 0.9rem;
        color: #475569;
        font-weight: 800;
    }
    .stTabs [aria-selected="true"] {
        background: #eff6ff;
        color: #1d4ed8;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
    }
    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
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


def render_hero():
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">📡 공모전 시연용 예방 행정 프로토타입</div>
            <h1 class="hero-title">화성 민원 레이더 AI</h1>
            <p class="hero-subtitle">
                가상 생활불편 민원을 분석해 반복 민원, 담당자 우선 확인 신호, 조치카드와 예방 리포트를
                한 화면에서 이해할 수 있게 정리합니다.
            </p>
            <div class="hero-flow">
                <span class="flow-chip">① 현황 파악</span>
                <span class="flow-chip">② 민원 분석</span>
                <span class="flow-chip">③ 반복·위험 감지</span>
                <span class="flow-chip">④ 예방 조치 제안</span>
            </div>
        </div>
        <div class='notice'><strong>{DISCLAIMER}</strong><br>{RISK_NOTICE}</div>
        """,
        unsafe_allow_html=True,
    )


def render_notice():
    st.markdown(f"<div class='notice'><strong>{DISCLAIMER}</strong><br>{RISK_NOTICE}</div>", unsafe_allow_html=True)


def render_section_header(eyebrow, title, description):
    st.markdown(
        f"""
        <div class="section-head">
            <div class="section-eyebrow">{eyebrow}</div>
            <h2 class="section-title">{title}</h2>
            <p class="section-desc">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label, value, help_text):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_cards(items):
    cols = st.columns(len(items))
    for index, item in enumerate(items):
        with cols[index]:
            st.markdown(
                f"""
                <div class="step-card">
                    <div class="step-no">{index + 1}</div>
                    <div class="card-title">{item["title"]}</div>
                    <div class="muted">{item["desc"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_analysis_result(result):
    cols = st.columns(4)
    with cols[0]:
        render_metric_card("민원 분야", result["category"], "주요 키워드 기반 분류")
    with cols[1]:
        render_metric_card("세부 분야", result["sub_category"], "담당자가 볼 상세 유형")
    with cols[2]:
        render_metric_card("긴급도", result["urgency"], "담당자 우선 확인 참고")
    with cols[3]:
        render_metric_card("담당 후보", result["owner_candidate"], "실제 부서가 아닌 역할명")

    render_section_header("Result", "AI 분석 결과", "키워드 규칙 분석 결과를 시민 안내와 내부 검토 관점으로 나눠 보여줍니다.")
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


def build_category_summary(dataframe):
    summary = dataframe.groupby("category").agg(
        total=("id", "count"),
        repeats=("is_repeat", lambda values: bool_series(values).sum()),
        risks=("risk_flag", lambda values: bool_series(values).sum()),
    ).reset_index()
    summary["attention_score"] = summary["repeats"] * 2 + summary["risks"] * 3 + summary["total"]
    return summary.sort_values("attention_score", ascending=False)


def build_prevention_report(dataframe, parking, sports):
    summary = build_category_summary(dataframe)
    top_row = summary.iloc[0]
    risk_dataframe = dataframe[dataframe["urgency"].isin(["주의", "즉시 확인 필요"]) | bool_series(dataframe["risk_flag"])]
    keyword_counts = get_repeated_keyword_counts(dataframe, limit=5)
    parking_total = int(parking["면수"].fillna(0).sum())
    sports_total = int(sports["시설수"].fillna(0).sum()) if "시설수" in sports.columns else len(sports)

    recommendations = []
    if (summary["category"] == "주차").any():
        parking_row = summary[summary["category"] == "주차"].iloc[0]
        if parking_row["repeats"] >= 2:
            recommendations.append(f"주차 반복 민원 {int(parking_row['repeats'])}건: 공영주차장 {len(parking)}개 구간·{parking_total:,}면 안내 강화 검토")
    if summary["category"].isin(["안전", "시설이용", "프로그램", "대관"]).any():
        facility_score = summary[summary["category"].isin(["안전", "시설이용", "프로그램", "대관"])]["attention_score"].sum()
        if facility_score >= 10:
            recommendations.append(f"시설 관련 민원 주의: 체육시설 {sports_total:,}개 항목 기준 점검·대관 안내 우선순위 검토")
    if len(risk_dataframe) > 0:
        recommendations.append(f"주의 이상 또는 우선 확인 민원 {len(risk_dataframe)}건: 담당자 선확인 목록으로 분리 관리")
    if not recommendations:
        recommendations.append("현재 샘플 기준 큰 위험 신호는 낮으나 반복 키워드 모니터링은 유지")

    return {
        "top_category": top_row["category"],
        "top_total": int(top_row["total"]),
        "top_repeats": int(top_row["repeats"]),
        "top_risks": int(top_row["risks"]),
        "risk_count": len(risk_dataframe),
        "keywords": keyword_counts,
        "summary": summary,
        "risk_dataframe": risk_dataframe,
        "recommendations": recommendations,
    }


def dashboard_tab(dataframe):
    render_section_header(
        "Overview",
        "오늘의 민원 흐름을 먼저 봅니다",
        "전체 규모, 반복 신호, 우선 확인 건수를 카드로 요약하고 주요 분포를 차트로 확인합니다.",
    )
    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("전체 민원", f"{len(dataframe):,}건", "가상 샘플 데이터 기준")
    with metric_cols[1]:
        render_metric_card("반복 민원", f"{bool_series(dataframe['is_repeat']).sum():,}건", "같은 이슈가 반복된 건")
    with metric_cols[2]:
        render_metric_card("우선 확인", f"{bool_series(dataframe['risk_flag']).sum():,}건", "담당자 선확인 참고")
    with metric_cols[3]:
        render_metric_card("분야 수", f"{dataframe['category'].nunique():,}개", "8개 생활불편 분야")

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

    render_section_header(
        "Signal Cards",
        "주의 신호만 카드로 빠르게 확인합니다",
        "반복 건수와 우선 확인 건수가 높은 분야를 예방 알림 카드로 요약합니다.",
    )
    alerts = build_prevention_alerts(dataframe)
    alert_cols = st.columns(min(3, len(alerts)) or 1)
    for index, alert in enumerate(alerts):
        with alert_cols[index % len(alert_cols)]:
            render_alert_card(alert)


def complaint_analysis_tab():
    render_section_header(
        "Analyze",
        "민원 문장을 넣으면 조치 방향까지 정리합니다",
        "예시를 선택하거나 직접 입력하면 요약, 분야, 긴급도, 담당 후보, 시민 답변 초안을 한 번에 보여줍니다.",
    )
    render_step_cards(
        [
            {"title": "예시 선택", "desc": "주차, 안전, 개인정보 예시로 바로 시연할 수 있습니다."},
            {"title": "규칙 분석", "desc": "외부 AI API 없이 키워드 기반 규칙으로 분류합니다."},
            {"title": "조치 연결", "desc": "시민 답변과 내부 검토 메모를 분리해 보여줍니다."},
        ]
    )

    examples = {
        "주차 혼잡 예시": "주말 행사 시간마다 주차장이 만차라 차량 진입이 어렵고 보행자 안전도 걱정됩니다.",
        "아동 안전 예시": "어린이들이 이용하는 계단 바닥이 미끄러워 넘어짐 사고가 날까 걱정됩니다.",
        "CCTV/개인정보 예시": "휴게 공간 CCTV 촬영 범위가 넓어 사생활과 개인정보 침해가 우려됩니다.",
    }

    if "complaint_input" not in st.session_state:
        st.session_state.complaint_input = examples["주차 혼잡 예시"]

    st.markdown("#### 바로 써보는 예시 민원")
    button_cols = st.columns(3)
    for index, (label, value) in enumerate(examples.items()):
        if button_cols[index].button(label, width="stretch"):
            st.session_state.complaint_input = value

    st.markdown("#### 민원 문장 입력")
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
    render_section_header(
        "Radar",
        "반복되는 불편 신호를 먼저 찾습니다",
        "분야별 반복 건수와 우선 확인 건수를 합산해 주의가 필요한 항목을 카드로 보여줍니다.",
    )
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
            level = "🚨 주의 필요" if row.risks >= 2 else "🔎 반복 관찰"
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

    st.markdown("#### 분야별 상세 점수")
    st.dataframe(summary.rename(columns={"attention_score": "관찰 점수"}), width="stretch", hide_index=True)


def prevention_report_tab(dataframe, parking, sports):
    render_section_header(
        "Report",
        "보고서 초안처럼 바로 읽히는 예방 행정 리포트",
        "반복·위험 신호를 요약하고 담당자가 먼저 볼 목록과 권장 조치를 자동 정리합니다.",
    )

    report = build_prevention_report(dataframe, parking, sports)
    cols = st.columns(4)
    with cols[0]:
        render_metric_card("최우선 관찰", report["top_category"], "가장 높은 관찰 점수")
    with cols[1]:
        render_metric_card("반복 민원", f"{report['top_repeats']:,}건", "최우선 분야 내 반복")
    with cols[2]:
        render_metric_card("우선 확인", f"{report['top_risks']:,}건", "담당자 선확인 참고")
    with cols[3]:
        render_metric_card("주의 목록", f"{report['risk_count']:,}건", "주의 이상 또는 플래그")

    st.markdown("#### 이번 주 예방 행정 요약")
    st.info(
        f"샘플 데이터 기준 `{report['top_category']}` 분야가 전체 {report['top_total']}건, "
        f"반복 {report['top_repeats']}건, 우선 확인 {report['top_risks']}건으로 가장 높은 관찰 점수를 보였습니다. "
        "이는 실제 민원 통계가 아닌 공모전 시연용 가상 데이터 기반 참고 요약입니다."
    )

    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### 반복 키워드")
        keyword_text = "".join(f"<span class='tag'>{keyword} {count}건</span>" for keyword, count in report["keywords"])
        st.markdown(keyword_text, unsafe_allow_html=True)

        st.markdown("#### 권장 조치")
        for recommendation in report["recommendations"]:
            st.success(recommendation)

    with right:
        st.markdown("#### 담당자 선확인 목록")
        preview_columns = ["id", "date", "facility", "category", "urgency", "complaint_text", "expected_role"]
        if report["risk_dataframe"].empty:
            st.write("현재 조건에 해당하는 주의 민원이 없습니다.")
        else:
            st.dataframe(report["risk_dataframe"][preview_columns], width="stretch", hide_index=True)

    st.markdown("#### 분야별 관찰 점수")
    score_chart = px.bar(
        report["summary"],
        x="attention_score",
        y="category",
        orientation="h",
        text="attention_score",
        title="반복·위험 신호 기반 관찰 점수",
    )
    score_chart.update_traces(marker_color="#dc2626", textposition="outside")
    score_chart.update_layout(height=380, margin=dict(l=10, r=10, t=50, b=10), xaxis_title="관찰 점수", yaxis_title="")
    st.plotly_chart(score_chart, width="stretch")


def public_data_tab(dataframe, parking, sports):
    render_section_header(
        "Public Data",
        "공공데이터는 민원 해석의 근거 카드로 씁니다",
        "공영주차장과 체육시설 공개 데이터를 반복 민원 예방 조치의 배경 정보로 연결합니다.",
    )

    parking_complaints = dataframe[dataframe["category"] == "주차"]
    facility_complaints = dataframe[dataframe["category"].isin(["안전", "시설이용", "프로그램", "대관"])]
    sports_total = int(sports["시설수"].fillna(0).sum()) if "시설수" in sports.columns else len(sports)
    sports_type_count = sports["시설명"].nunique()
    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("공영주차장", f"{len(parking):,}개", "공개 CSV 구간 수")
    with metric_cols[1]:
        render_metric_card("총 주차면수", f"{int(parking['면수'].fillna(0).sum()):,}면", "주차 민원 연결 근거")
    with metric_cols[2]:
        render_metric_card("체육시설", f"{sports_total:,}개", "유형별 요약 항목")
    with metric_cols[3]:
        render_metric_card("시설 민원", f"{len(facility_complaints):,}건", "가상 샘플 기준")

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
        parking_repeats = bool_series(parking_complaints["is_repeat"]).sum()
        facility_repeats = bool_series(facility_complaints["is_repeat"]).sum()
        parking_total_spaces = int(parking["면수"].fillna(0).sum())
        parking_top_area = parking.groupby("권역")["면수"].sum().sort_values(ascending=False).index[0]
        sports_top_type = sports.sort_values("시설수", ascending=False).iloc[0]["시설명"] if "시설수" in sports.columns else sports["시설명"].value_counts().index[0]

        card_cols = st.columns(3)
        with card_cols[0]:
            st.markdown(
                f"""
                <div class="soft-card">
                    <div class="card-title">주차 민원 × 공영주차장</div>
                    <div class="muted">가상 주차 민원 {len(parking_complaints)}건 · 반복 {parking_repeats}건</div>
                    <p>공영주차장 {len(parking)}개 구간, 총 {parking_total_spaces:,}면과 연결해 혼잡 안내·분산 유도 필요성을 검토합니다.</p>
                    <p><strong>우선 확인 권역:</strong> {parking_top_area}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with card_cols[1]:
            st.markdown(
                f"""
                <div class="soft-card">
                    <div class="card-title">시설 민원 × 체육시설</div>
                    <div class="muted">시설 관련 가상 민원 {len(facility_complaints)}건 · 반복 {facility_repeats}건</div>
                    <p>체육시설 {sports_total:,}개 항목, {sports_type_count}개 유형과 연결해 안전 점검·대관 안내 우선순위를 검토합니다.</p>
                    <p><strong>최다 시설 유형:</strong> {sports_top_type}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with card_cols[2]:
            st.markdown(
                f"""
                <div class="soft-card">
                    <div class="card-title">반복 민원 × 예방 조치</div>
                    <div class="muted">공공데이터는 배경 정보로만 활용</div>
                    <p>민원 원문 대신 가상 샘플과 공개 인프라 현황을 결합해 개인정보 부담을 낮추고 예방 행정 설명력을 높입니다.</p>
                    <p><strong>활용 방향:</strong> 안내 강화 · 점검 우선순위 · FAQ 개선</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("#### 연결 해석 표")
        linked_rows = pd.DataFrame(
            [
                {
                    "민원 신호": "주차 혼잡·불법주차",
                    "연결 공공데이터": "공영주차장 위치·면수",
                    "확인 포인트": f"{len(parking)}개 구간 / {parking_total_spaces:,}면 / {parking_top_area} 권역",
                    "예방 조치 예시": "주차 안내 강화, 주변 주차장 안내, 혼잡 시간대 분산 유도",
                },
                {
                    "민원 신호": "시설이용·안전·대관",
                    "연결 공공데이터": "체육시설 유형별 현황",
                    "확인 포인트": f"{sports_total:,}개 항목 / {sports_type_count}개 유형 / 최다 유형 {sports_top_type}",
                    "예방 조치 예시": "시설 점검 우선순위, 대관 안내 개선, 안전 안내문 보강",
                },
            ]
        )
        st.dataframe(linked_rows, width="stretch", hide_index=True)


def action_cards_tab():
    render_section_header(
        "Action Card",
        "담당자가 바로 확인할 조치카드",
        "민원 유형을 선택하면 시민 답변, 내부 검토 메모, 확인 체크리스트를 분리해서 보여줍니다.",
    )
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
    render_section_header(
        "About",
        "서비스의 위치와 안전 원칙",
        "국민신문고 대체 서비스가 아니라, 접수 이후 반복 민원 분석과 예방 행정을 돕는 시연 도구입니다.",
    )
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
    render_hero()

    tabs = st.tabs(["현황", "AI 분석", "반복 레이더", "예방 리포트", "공공데이터", "조치카드", "소개"])
    with tabs[0]:
        dashboard_tab(dataframe)
    with tabs[1]:
        complaint_analysis_tab()
    with tabs[2]:
        radar_tab(dataframe)
    with tabs[3]:
        prevention_report_tab(dataframe, parking, sports)
    with tabs[4]:
        public_data_tab(dataframe, parking, sports)
    with tabs[5]:
        action_cards_tab()
    with tabs[6]:
        intro_tab()


if __name__ == "__main__":
    main()
