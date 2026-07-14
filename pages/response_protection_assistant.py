import streamlit as st


COUNSELING_NOTICE = "본 기능은 실제 통화 녹취를 사용하지 않는 시연용 텍스트 분석 기능입니다."

COUNSELING_EXAMPLES = {
    "장시간 반복 문의": "같은 주차 민원으로 오늘 세 번째 연락드립니다. 40분 넘게 설명했는데도 해결이 안 됐다고 느껴 다시 문의합니다.",
    "격앙된 표현 포함": "계속 기다리라고만 하면 너무 화가 납니다. 담당자가 일부러 피하는 것 아닌지 따지고 싶습니다.",
    "절차 안내 요청": "대관 환불 기준을 여러 번 문의했는데 안내가 조금씩 달라서 다시 확인하고 싶습니다.",
    "안전 우려 반복": "아이들이 다칠까 봐 지난주에도 말했는데 아직 조치가 없어 다시 연락드립니다.",
    "일반 문의": "프로그램 신청 일정과 대기자 안내가 언제 올라오는지 궁금합니다.",
}


st.set_page_config(page_title="AI 민원응대 보호 어시스턴트", page_icon="🛡️", layout="wide")


st.markdown(
    """
    <style>
    .main .block-container { max-width: 1100px; padding-top: 1.5rem; }
    .notice {
        border: 1px solid #dbeafe; border-left: 6px solid #2563eb; background: #eff6ff;
        padding: 0.9rem 1rem; border-radius: 16px; color: #243b53; margin-bottom: 1rem;
    }
    .tag {
        display: inline-block; padding: 0.22rem 0.52rem; border-radius: 999px;
        background: #eef2ff; color: #3730a3; margin-right: 0.25rem; margin-bottom: 0.25rem;
        font-size: 0.84rem; font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def analyze_counseling_text(text):
    normalized = str(text or "").strip()
    repeat_keywords = ["다시", "반복", "세 번째", "여러 번", "지난주", "계속", "또", "재문의"]
    long_keywords = ["40분", "30분", "장시간", "오래", "계속 설명", "길게"]
    high_risk_keywords = ["화가", "따지", "고소", "신고", "욕", "폭언", "위협", "찾아가", "민원 넣"]

    repeat_matches = [keyword for keyword in repeat_keywords if keyword in normalized]
    long_matches = [keyword for keyword in long_keywords if keyword in normalized]
    high_risk_matches = [keyword for keyword in high_risk_keywords if keyword in normalized]

    is_repeat = bool(repeat_matches)
    is_long = bool(long_matches) or len(normalized) >= 120
    is_high_risk = bool(high_risk_matches)

    if is_high_risk:
        protection_level = "주의"
        guide = "감정적 표현에 직접 맞대응하지 말고, 사실 확인 범위와 공식 처리 절차를 짧게 안내한 뒤 필요 시 관리자 동석 또는 상담 이관을 검토합니다."
    elif is_repeat or is_long:
        protection_level = "확인 필요"
        guide = "반복 설명으로 인한 담당자 피로를 줄이기 위해 이전 안내 이력, 처리 기준, 다음 확인 시점을 표준 문장으로 정리합니다."
    else:
        protection_level = "일반"
        guide = "일반 문의로 분류되며, 핵심 요청을 확인한 뒤 동일한 기준의 표준 안내문으로 응대합니다."

    response = (
        "문의 주신 내용을 확인했습니다. 동일 기준에 따라 관련 사항을 검토하고, 확인 가능한 범위와 절차를 안내드리겠습니다. "
        "추가 확인이 필요한 경우 담당자가 정리된 기준에 따라 안내드리겠습니다."
    )
    internal_note = (
        f"장시간 여부: {'해당' if is_long else '미해당'} / 반복 민원 여부: {'해당' if is_repeat else '미해당'} / "
        f"고위험 표현 참고: {'감지' if is_high_risk else '미감지'}"
    )

    return {
        "is_long": is_long,
        "is_repeat": is_repeat,
        "is_high_risk": is_high_risk,
        "protection_level": protection_level,
        "matched_keywords": list(dict.fromkeys(repeat_matches + long_matches + high_risk_matches)) or ["특이 키워드 없음"],
        "guide": guide,
        "standard_response": response,
        "internal_note": internal_note,
    }


st.title("🛡️ AI 민원응대 보호 어시스턴트")
st.markdown(
    f"""
    <div class="notice">
    <strong>{COUNSELING_NOTICE}</strong><br>
    실제 통화 음성, 녹취, 개인정보는 사용하지 않습니다. 실시간 STT 연동은 향후 확장 기능으로만 가정합니다.
    </div>
    """,
    unsafe_allow_html=True,
)

if "counseling_input_page" not in st.session_state:
    st.session_state.counseling_input_page = COUNSELING_EXAMPLES["장시간 반복 문의"]

st.subheader("가상 상담기록 예시")
example_cols = st.columns(5)
for index, (label, value) in enumerate(COUNSELING_EXAMPLES.items()):
    if example_cols[index].button(label, width="stretch"):
        st.session_state.counseling_input_page = value

st.subheader("상담기록 텍스트 입력")
text = st.text_area(
    "상담기록 텍스트",
    key="counseling_input_page",
    height=150,
    placeholder="가상 상담기록을 입력하세요. 실제 통화 녹취나 개인정보는 입력하지 않습니다.",
)

if st.button("응대 보호 분석하기", type="primary", width="stretch"):
    result = analyze_counseling_text(text)
    cols = st.columns(4)
    cols[0].metric("장시간 신호", "해당" if result["is_long"] else "미해당")
    cols[1].metric("반복 민원", "해당" if result["is_repeat"] else "미해당")
    cols[2].metric("고위험 표현", "감지" if result["is_high_risk"] else "미감지")
    cols[3].metric("보호 수준", result["protection_level"])

    st.subheader("감지 키워드")
    st.markdown("".join(f"<span class='tag'>{keyword}</span>" for keyword in result["matched_keywords"]), unsafe_allow_html=True)

    left, right = st.columns(2)
    with left:
        st.subheader("담당자 보호 가이드")
        st.warning(result["guide"])
        st.subheader("내부 참고 메모")
        st.info(result["internal_note"])
    with right:
        st.subheader("표준 응대문안")
        st.success(result["standard_response"])
        st.caption("본 문안은 시연용 초안이며, 실제 응대 시 기관 기준과 담당자 판단에 따라 조정해야 합니다.")
else:
    st.info("가상 상담기록 예시를 선택하거나 텍스트를 입력한 뒤 분석하기를 눌러보세요.")
