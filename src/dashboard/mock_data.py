"""대시보드 목업(mock) 데이터 생성.

⚠️ 여기서 만드는 도로 구간·좌표·위험도는 전부 난수로 생성한 합성 데이터다.
실제 로드킬 발생 지점이나 실제 도로 위치와 무관하다. 대시보드 UI/UX를
전처리·모델 학습과 독립적으로 먼저 개발하기 위한 용도이며(자세한 배경은
``docs/DESIGN_DECISIONS.md`` 참고), 실제 파이프라인이 준비되면
``src/dashboard/data_provider.py`` 의 ``load_segments()`` 내부만 실데이터
로더로 교체하면 된다 — 이 파일과 나머지 대시보드 코드는 바뀌지 않는다.

``src/models/baseline/schema.py`` 와 최대한 같은 피처 이름을 쓴다. 그래야
나중에 실제 모델 출력으로 바꿔 끼울 때 화면 쪽 코드를 다시 안 써도 된다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.dashboard.style import ROAD_GRADES, risk_level_for
from src.models.baseline.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES

# 지도 초기 중심 — 실제 지명이 아닌 임의의 기준점(강원권 산간 국도를 가정한 좌표대)
_CENTER_LON, _CENTER_LAT = 128.2, 37.6


def _make_road_path(rng: np.random.Generator, n_points: int) -> np.ndarray:
    """임의의 지점에서 시작하는 완만한 랜덤워크 경로(위경도)를 만든다."""
    start_lon = _CENTER_LON + rng.uniform(-0.6, 0.6)
    start_lat = _CENTER_LAT + rng.uniform(-0.4, 0.4)
    heading = rng.uniform(0, 2 * np.pi)

    lons, lats = [start_lon], [start_lat]
    for _ in range(n_points - 1):
        heading += rng.normal(0, 0.25)  # 완만하게만 방향을 바꿔 도로처럼 보이게
        step = 0.0045  # 대략 500m 상당
        lons.append(lons[-1] + step * np.cos(heading))
        lats.append(lats[-1] + step * np.sin(heading))
    return np.column_stack([lons, lats])


def generate_mock_segments(
    n_roads: int = 6,
    segments_per_road: int = 25,
    seed: int = 42,
) -> pd.DataFrame:
    """지도에 표시할 목업 도로 구간 테이블을 생성한다.

    서식지 인접도가 높고 산림 비율이 높을수록 위험도가 올라가도록 설계해,
    지도를 봤을 때 "그럴듯한" 공간 패턴(서식지 근처가 빨갛게 표시)이
    보이게 만들었다. 실제 상관관계와는 무관하다.

    Args:
        n_roads: 생성할 도로(경로) 개수.
        segments_per_road: 도로 하나를 몇 개의 500m급 구간으로 나눌지.
        seed: 재현성을 위한 시드.

    Returns:
        지도 렌더링과 상세 패널에 필요한 모든 컬럼을 가진 DataFrame.
        컬럼: ``segment_id``, ``road_name``, ``road_grade``, ``path``
        (``[[lon, lat], [lon, lat]]``), ``lon``/``lat``(중점, 툴팁·정렬용),
        ``risk_score``, ``risk_level``, ``risk_icon``, ``color_r/g/b/a``,
        + ``src.models.baseline.schema`` 의 피처 컬럼 전체,
        ``top_factors``(문자열 리스트), ``policy_brief``(문자열).
    """
    rng = np.random.default_rng(seed)
    rows: list[dict] = []

    for road_idx in range(n_roads):
        road_name = f"목업{road_idx + 1}로"
        road_grade = rng.choice(ROAD_GRADES, p=[0.15, 0.35, 0.5])
        path_points = _make_road_path(rng, segments_per_road + 1)

        base_habitat_ratio = rng.uniform(0, 1)
        base_dist_to_habitat = rng.uniform(0, 3000)
        speed_limit = int(rng.choice([50, 60, 70, 80, 100]))
        aadt = rng.uniform(500, 30000)

        for seg_idx in range(segments_per_road):
            p1, p2 = path_points[seg_idx], path_points[seg_idx + 1]

            dist_to_habitat = max(0.0, base_dist_to_habitat + rng.normal(0, 200))
            habitat_ratio = float(np.clip(base_habitat_ratio + rng.normal(0, 0.08), 0, 1))
            forest_ratio = float(np.clip(rng.uniform(0, 1) * 0.6 + habitat_ratio * 0.4, 0, 1))

            features = {
                "length_m": float(rng.uniform(400, 600)),
                "road_width_m": float(rng.uniform(3, 12)),
                "lane_count": int(rng.integers(1, 5)),
                "speed_limit_kmh": speed_limit,
                "aadt": float(aadt + rng.normal(0, 500)),
                "curvature": float(rng.uniform(1.0, 1.5)),
                "sinuosity": float(rng.uniform(1.0, 1.3)),
                "dist_to_habitat_m": float(dist_to_habitat),
                "habitat_ratio": habitat_ratio,
                "dist_to_corridor_m": float(rng.uniform(0, 5000)),
                "forest_ratio": forest_ratio,
                "farmland_ratio": float(rng.uniform(0, 1 - forest_ratio)),
                "elevation_m": float(rng.uniform(0, 800)),
                "slope_deg": float(rng.uniform(0, 30)),
                "slope_std": float(rng.uniform(0, 10)),
                "temp_avg": float(rng.uniform(-5, 25)),
                "precipitation_mm": float(max(0.0, rng.normal(2, 5))),
                "humidity": float(rng.uniform(30, 90)),
                "visibility_m": float(rng.uniform(500, 20000)),
                "snow_cm": float(max(0.0, rng.normal(0, 1))),
                "road_grade": road_grade,
                "season": rng.choice(["spring", "summer", "fall", "winter"]),
            }
            assert set(features) == set(NUMERIC_FEATURES) | set(CATEGORICAL_FEATURES)

            risk_score = float(
                np.clip(
                    0.45 * (1 - min(dist_to_habitat / 3000, 1))
                    + 0.35 * forest_ratio
                    + 0.15 * habitat_ratio
                    + 0.05 * min(features["aadt"] / 30000, 1)
                    + rng.normal(0, 0.08),
                    0,
                    1,
                )
            )
            level = risk_level_for(risk_score)

            # 실제 SHAP이 아니라, 위 risk_score 산식에서 기여가 큰 항을 그대로 보여주는
            # 흉내(heuristic)다 — 실제 모델이 붙으면 src.models.baseline.interpret 로 교체.
            top_factors = sorted(
                [
                    ("서식지와의 거리", -(1 - min(dist_to_habitat / 3000, 1))),
                    ("산림 비율", forest_ratio),
                    ("서식지 면적 비율", habitat_ratio),
                    ("교통량(AADT)", features["aadt"] / 30000 * 0.3),
                ],
                key=lambda kv: -abs(kv[1]),
            )[:3]

            segment_id = f"{road_name}_{seg_idx:03d}"
            rows.append(
                {
                    "segment_id": segment_id,
                    "road_name": road_name,
                    "path": [[float(p1[0]), float(p1[1])], [float(p2[0]), float(p2[1])]],
                    "lon": float((p1[0] + p2[0]) / 2),
                    "lat": float((p1[1] + p2[1]) / 2),
                    "risk_score": risk_score,
                    "risk_level": level["label"],
                    "risk_icon": level["icon"],
                    "color_r": level["color"][0],
                    "color_g": level["color"][1],
                    "color_b": level["color"][2],
                    "color_a": 200,
                    "top_factors": top_factors,
                    "policy_brief": _mock_policy_brief(segment_id, road_name, risk_score, level["label"], top_factors),
                    **features,
                }
            )

    return pd.DataFrame(rows)


def _mock_policy_brief(
    segment_id: str,
    road_name: str,
    risk_score: float,
    risk_label: str,
    top_factors: list[tuple[str, float]],
) -> str:
    """LLM이 나중에 생성할 정책 브리핑의 형태를 흉내낸 템플릿 문장.

    ⚠️ 실제 Claude API 호출 없이 문자열 템플릿으로 채운 자리표시자다.
    ``src/llm`` 구현 후 이 함수 대신 실제 브리핑 생성 함수로 교체한다.
    """
    factor_text = ", ".join(f"{name}" for name, _ in top_factors)
    return (
        f"[목업 브리핑] {road_name} 내 구간 {segment_id}은 위험도 {risk_score:.2f}"
        f"({risk_label} 등급)으로 평가되었습니다. 주요 기여 요인은 {factor_text}입니다. "
        "이 문장은 실제 LLM이 생성한 내용이 아니라 화면 레이아웃 검증용 예시입니다."
    )


def get_mock_chat_response(question: str, segments: pd.DataFrame) -> str:
    """RAG 챗봇이 나중에 처리할 질의에 대한 목업 응답을 만든다.

    ⚠️ 실제 임베딩 검색이나 Claude API 호출 없이 키워드 매칭으로만 응답한다.
    ``src/rag``·``src/llm`` 구현 후 이 함수를 실제 RAG 파이프라인 호출로
    교체한다.

    Args:
        question: 사용자가 입력한 질의.
        segments: :func:`generate_mock_segments` 결과 (필터 적용된 현재 화면 기준).

    Returns:
        목업 응답 문자열.
    """
    if segments.empty:
        return "현재 필터 조건에 맞는 구간이 없어 답변할 수 없습니다. 필터를 조정해보세요."

    q = question.strip()
    top = segments.sort_values("risk_score", ascending=False).iloc[0]

    if any(kw in q for kw in ["가장 위험", "제일 위험", "최고 위험"]):
        return (
            f"[목업 응답] 현재 화면 기준 가장 위험도가 높은 구간은 "
            f"{top['road_name']}의 {top['segment_id']} (위험도 {top['risk_score']:.2f}, "
            f"{top['risk_level']} 등급)입니다."
        )
    if any(kw in q for kw in ["서식지", "생태통로"]):
        near = segments.sort_values("dist_to_habitat_m").iloc[0]
        return (
            f"[목업 응답] 서식지에 가장 가까운 구간은 {near['segment_id']}이며 "
            f"거리는 약 {near['dist_to_habitat_m']:.0f}m입니다."
        )
    return (
        "[목업 응답] 이 챗봇은 아직 실제 데이터에 연결되지 않은 자리표시자입니다. "
        "RAG 파이프라인(src/rag)과 Claude API 연동(src/llm) 구현 후 실제 검색 기반 "
        "답변으로 교체될 예정입니다."
    )
