"""대시보드 전역 시각 상수.

색상은 dataviz 스킬의 **status 팔레트**(고정값, 테마 영향 없음)를 그대로
쓴다. 위험도는 이산적인 "상태"(안전→주의→위험→매우 위험)로 보여주는 게
연속값 그라데이션보다 정책 판단에 더 직관적이라 판단해 status 팔레트를
선택했다 (자세한 근거는 ``docs/DESIGN_DECISIONS.md`` 참고). Status 색상은
저대비 구간(주의·위험 단계)이 있어 항상 아이콘+텍스트 라벨과 함께 쓴다 —
색상 하나에만 의존하지 않는다.
"""

from __future__ import annotations

# 도로등급 표시 이름 — 실제 표준노드링크 코드 체계 확인 전까지의 임시 매핑
ROAD_GRADES: list[str] = ["고속국도", "일반국도", "지방도"]

# 위험도 4단계: (하한 포함, 라벨, 아이콘, RGB)
# RGB는 dataviz 스킬 status 팔레트 고정값
#   good #0ca30c / warning #fab219 / serious #ec835a / critical #d03b3b
RISK_LEVELS: list[dict] = [
    {"min_score": 0.0, "label": "안전", "icon": "🟢", "color": (12, 163, 12)},
    {"min_score": 0.25, "label": "주의", "icon": "🟡", "color": (250, 178, 25)},
    {"min_score": 0.5, "label": "위험", "icon": "🟠", "color": (236, 131, 90)},
    {"min_score": 0.75, "label": "매우 위험", "icon": "🔴", "color": (208, 59, 59)},
]


def risk_level_for(score: float) -> dict:
    """0~1 위험도 점수를 4단계 라벨/아이콘/색상 정보로 변환한다.

    Args:
        score: 0~1 사이 위험도 점수.

    Returns:
        ``RISK_LEVELS`` 원소 중 하나 (``min_score``, ``label``, ``icon``, ``color``).
    """
    level = RISK_LEVELS[0]
    for candidate in RISK_LEVELS:
        if score >= candidate["min_score"]:
            level = candidate
    return level
