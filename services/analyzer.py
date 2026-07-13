from collections import Counter


URGENCY_ORDER = {
    "일반": 0,
    "확인 필요": 1,
    "주의": 2,
    "즉시 확인 필요": 3,
}


CATEGORY_RULES = {
    "주차": {
        "keywords": ["주차", "차량", "불법주차", "주차장", "혼잡", "진입", "출차", "만차"],
        "sub_category": "주차 혼잡",
        "owner": "시설관리 담당",
        "reply": "주차 이용 불편 사항을 접수했습니다. 현장 혼잡 시간대와 안내 동선을 우선 확인하겠습니다.",
        "memo": "혼잡 시간대, 주차 안내 표지, 진입·출차 동선, 반복 민원 여부를 확인합니다.",
        "prevention": "혼잡 시간대 안내 강화, 임시 안내 표지 배치, 주차 동선 분리 검토가 필요합니다.",
    },
    "안전": {
        "keywords": ["안전", "아동", "어린이", "미끄럼", "넘어짐", "파손", "사고", "부상", "위험", "계단"],
        "sub_category": "시설 안전",
        "owner": "안전관리 담당",
        "reply": "안전 관련 불편 사항을 접수했습니다. 담당자가 현장 상태를 우선 확인하도록 하겠습니다.",
        "memo": "위험 지점, 파손 여부, 임시 안전조치 필요성, 이용자 접근 제한 여부를 확인합니다.",
        "prevention": "안전 안내문 보강, 위험 구역 임시 통제, 정기 점검 항목 반영을 검토합니다.",
    },
    "CCTV/개인정보": {
        "keywords": ["CCTV", "촬영", "영상", "개인정보", "사생활", "녹화", "카메라", "동의"],
        "sub_category": "개인정보 확인",
        "owner": "개인정보보호 담당",
        "reply": "CCTV 및 개인정보 관련 문의를 접수했습니다. 운영 기준과 안내 표기 여부를 확인하겠습니다.",
        "memo": "촬영 범위, 안내문 게시, 보관 기간, 열람 절차, 개인정보보호 기준 준수 여부를 확인합니다.",
        "prevention": "CCTV 안내문 정비, 촬영 범위 재점검, 개인정보 문의 대응 문안 보강이 필요합니다.",
    },
    "시설이용": {
        "keywords": ["시설", "이용", "화장실", "냉난방", "고장", "문", "엘리베이터", "청소", "장비"],
        "sub_category": "시설 이용 불편",
        "owner": "시설관리 담당",
        "reply": "시설 이용 불편 사항을 접수했습니다. 담당자가 시설 상태를 확인하겠습니다.",
        "memo": "고장 위치, 이용 불편 시간대, 현장 조치 가능 여부, 추가 안내 필요성을 확인합니다.",
        "prevention": "시설 점검 주기 보완, 이용 안내 강화, 고장 접수 동선 단순화를 검토합니다.",
    },
    "프로그램": {
        "keywords": ["프로그램", "강좌", "수업", "강사", "접수", "신청", "정원", "취소", "대기"],
        "sub_category": "프로그램 운영",
        "owner": "프로그램 운영 담당",
        "reply": "프로그램 운영 관련 의견을 접수했습니다. 신청 및 운영 기준을 확인하겠습니다.",
        "memo": "모집 정원, 대기자 안내, 취소 규정, 강좌 운영 공지의 명확성을 확인합니다.",
        "prevention": "접수 안내 문구 개선, 대기자 알림 강화, 반복 문의 FAQ 추가를 검토합니다.",
    },
    "대관": {
        "keywords": ["대관", "예약", "사용료", "환불", "일정", "장소", "승인", "변경"],
        "sub_category": "대관 예약",
        "owner": "대관 운영 담당",
        "reply": "대관 이용 관련 문의를 접수했습니다. 예약 기준과 안내 내용을 확인하겠습니다.",
        "memo": "예약 상태, 사용 기준, 환불 규정, 일정 변경 가능 여부를 확인합니다.",
        "prevention": "대관 절차 안내 개선, 예약 확인 알림, 환불 기준 표시 강화를 검토합니다.",
    },
    "환경": {
        "keywords": ["소음", "냄새", "쓰레기", "분리수거", "청결", "먼지", "벌레", "악취", "환경"],
        "sub_category": "환경·청결",
        "owner": "환경관리 담당",
        "reply": "환경 및 청결 관련 불편 사항을 접수했습니다. 현장 상태를 확인하겠습니다.",
        "memo": "발생 위치, 반복 시간대, 청소 주기, 외부 요인 여부를 확인합니다.",
        "prevention": "청소 순찰 강화, 안내문 보강, 반복 발생 지점 관리대장 반영을 검토합니다.",
    },
    "행정안내": {
        "keywords": ["문의", "안내", "서류", "절차", "홈페이지", "전화", "운영시간", "공지", "민원"],
        "sub_category": "행정 안내",
        "owner": "민원안내 담당",
        "reply": "행정 안내 관련 문의를 접수했습니다. 안내 경로와 공지 내용을 확인하겠습니다.",
        "memo": "홈페이지 공지, 현장 안내문, 전화 응대 기준, 반복 문의 여부를 확인합니다.",
        "prevention": "자주 묻는 질문 보강, 안내 문구 단순화, 홈페이지 공지 위치 개선을 검토합니다.",
    },
}


URGENCY_KEYWORDS = {
    "즉시 확인 필요": ["사고", "부상", "화재", "감전", "추락", "개인정보", "사생활", "아동", "어린이"],
    "주의": ["위험", "파손", "미끄럼", "누수", "CCTV", "촬영", "악취", "불법주차"],
    "확인 필요": ["고장", "혼잡", "소음", "환불", "민원", "불편", "대기"],
}


def analyze_complaint(text, use_ai=False):
    if use_ai:
        return analyze_with_ai_api_placeholder(text)
    return analyze_with_rules(text)


def analyze_with_ai_api_placeholder(text):
    result = analyze_with_rules(text)
    result["analysis_mode"] = "rule_based_placeholder_for_future_ai"
    return result


def analyze_with_rules(text):
    normalized = (text or "").strip()
    matched_category = _detect_category(normalized)
    rule = CATEGORY_RULES[matched_category]
    keywords = _extract_keywords(normalized)
    urgency = _detect_urgency(normalized, matched_category)
    risk_reason = _build_risk_reason(normalized, urgency, keywords)

    return {
        "summary": _summarize(normalized, matched_category, rule["sub_category"]),
        "category": matched_category,
        "sub_category": rule["sub_category"],
        "urgency": urgency,
        "keywords": keywords,
        "owner_candidate": rule["owner"],
        "citizen_reply": rule["reply"],
        "internal_memo": rule["memo"],
        "prevention_suggestion": rule["prevention"],
        "risk_reason": risk_reason,
    }


def get_repeated_keyword_counts(dataframe, limit=10):
    counter = Counter()
    for value in dataframe["keywords"].dropna():
        for keyword in str(value).split("|"):
            cleaned = keyword.strip()
            if cleaned:
                counter[cleaned] += 1
    return counter.most_common(limit)


def build_prevention_alerts(dataframe):
    alerts = []
    grouped = dataframe.groupby("category").agg(
        total=("id", "count"),
        repeats=("is_repeat", lambda values: sum(_to_bool(value) for value in values)),
        risks=("risk_flag", lambda values: sum(_to_bool(value) for value in values)),
    )

    for category, row in grouped.sort_values(["risks", "repeats", "total"], ascending=False).iterrows():
        if row["repeats"] >= 3 or row["risks"] >= 2:
            alerts.append(
                {
                    "category": category,
                    "title": f"{category} 분야 반복·주의 신호",
                    "message": f"최근 샘플 기준 반복 {int(row['repeats'])}건, 우선 확인 {int(row['risks'])}건이 감지되었습니다.",
                    "level": "주의" if row["risks"] else "확인 필요",
                }
            )
    return alerts[:5]


def build_action_card(category):
    rule = CATEGORY_RULES.get(category, CATEGORY_RULES["행정안내"])
    return {
        "category": category,
        "owner_candidate": rule["owner"],
        "checklist": _checklist_for(category),
        "citizen_reply": rule["reply"],
        "internal_memo": rule["memo"],
        "prevention_suggestion": rule["prevention"],
    }


def _detect_category(text):
    scores = {}
    lower_text = text.lower()
    for category, rule in CATEGORY_RULES.items():
        score = sum(1 for keyword in rule["keywords"] if keyword.lower() in lower_text)
        scores[category] = score
    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    return best_category if best_score > 0 else "행정안내"


def _extract_keywords(text):
    lower_text = text.lower()
    matched = []
    for rule in CATEGORY_RULES.values():
        for keyword in rule["keywords"]:
            if keyword.lower() in lower_text and keyword not in matched:
                matched.append(keyword)
    return matched[:8] or ["일반 문의"]


def _detect_urgency(text, category):
    lower_text = text.lower()
    urgency = "일반"
    for label, keywords in URGENCY_KEYWORDS.items():
        if any(keyword.lower() in lower_text for keyword in keywords):
            if URGENCY_ORDER[label] > URGENCY_ORDER[urgency]:
                urgency = label
    if category == "CCTV/개인정보" and URGENCY_ORDER[urgency] < URGENCY_ORDER["주의"]:
        urgency = "주의"
    return urgency


def _build_risk_reason(text, urgency, keywords):
    if urgency in ["주의", "즉시 확인 필요"]:
        return (
            "담당자 우선 확인을 위한 참고 지표입니다. "
            f"입력 문장에서 {', '.join(keywords[:4])} 관련 표현이 감지되어 '{urgency}'로 표시했습니다."
        )
    return "담당자 우선 확인을 위한 참고 지표입니다. 긴급 위험 키워드는 뚜렷하게 감지되지 않았습니다."


def _summarize(text, category, sub_category):
    if not text:
        return "입력된 민원 문장이 없어 일반 안내 요청으로 분류했습니다."
    short_text = text if len(text) <= 42 else f"{text[:42]}..."
    return f"{category} 분야의 {sub_category} 관련 민원으로 요약됩니다: {short_text}"


def _checklist_for(category):
    checklists = {
        "주차": ["혼잡 시간대 확인", "진입·출차 동선 점검", "안내 표지 추가 필요성 검토"],
        "안전": ["현장 위험 지점 확인", "임시 통제 필요성 판단", "재발 방지 점검 항목 등록"],
        "CCTV/개인정보": ["촬영 범위 확인", "안내문 게시 여부 점검", "열람·보관 기준 확인"],
        "시설이용": ["고장 위치 확인", "이용 제한 안내 필요성 검토", "보수 일정 등록"],
        "프로그램": ["접수 기준 확인", "대기자 안내 점검", "공지 문구 개선 검토"],
        "대관": ["예약 상태 확인", "환불·변경 기준 확인", "이용자 안내 문구 점검"],
        "환경": ["발생 위치 확인", "청소·순찰 주기 점검", "반복 발생 지점 등록"],
        "행정안내": ["공지 위치 확인", "전화·현장 안내 문구 점검", "FAQ 추가 검토"],
    }
    return checklists.get(category, checklists["행정안내"])


def _to_bool(value):
    return str(value).strip().lower() in ["true", "1", "yes", "y"]
