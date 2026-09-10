"""대시보드 UI 조각들.

``app.py`` 는 이 모듈의 함수들을 조합만 하고, 지도·범례·KPI·상세 패널을
만드는 실제 로직은 여기에 둔다.
"""

from __future__ import annotations

import pandas as pd
import pydeck as pdk
import streamlit as st

from src.dashboard.style import RISK_LEVELS
from src.models.baseline.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES

SEGMENTS_LAYER_ID = "segments"

# 사람이 읽을 피처 이름 (상세 패널 표시용)
_FEATURE_LABELS: dict[str, str] = {
    "length_m": "구간 길이 (m)",
    "road_width_m": "도로 폭 (m)",
    "lane_count": "차로 수",
    "speed_limit_kmh": "제한속도 (km/h)",
    "aadt": "연평균 일교통량(AADT)",
    "curvature": "곡률",
    "sinuosity": "굴곡도",
    "dist_to_habitat_m": "서식지까지 거리 (m)",
    "habitat_ratio": "서식지 면적 비율",
    "dist_to_corridor_m": "생태통로까지 거리 (m)",
    "forest_ratio": "산림 비율",
    "farmland_ratio": "농경지 비율",
    "elevation_m": "고도 (m)",
    "slope_deg": "경사도 (°)",
    "slope_std": "경사 기복도",
    "temp_avg": "평균 기온 (°C)",
    "precipitation_mm": "강수량 (mm)",
    "humidity": "습도 (%)",
    "visibility_m": "가시거리 (m)",
    "snow_cm": "적설량 (cm)",
    "road_grade": "도로 등급",
    "season": "계절",
}


def _unpack_path(df: pd.DataFrame) -> pd.DataFrame:
    """``path`` 컬럼(``[[lon,lat],[lon,lat]]``)을 pydeck LineLayer용 평탄 컬럼으로 푼다."""
    out = df.copy()
    starts = out["path"].apply(lambda p: p[0])
    ends = out["path"].apply(lambda p: p[1])
    out["lon1"] = starts.apply(lambda p: p[0])
    out["lat1"] = starts.apply(lambda p: p[1])
    out["lon2"] = ends.apply(lambda p: p[0])
    out["lat2"] = ends.apply(lambda p: p[1])
    return out


def build_deck(df: pd.DataFrame) -> pdk.Deck:
    """구간 DataFrame으로 클릭 가능한 pydeck Deck을 만든다.

    ``id="segments"`` 를 지정해야 ``st.pydeck_chart(..., on_select="rerun")`` 의
    선택 상태가 유지된다 (pydeck 요구사항).

    Args:
        df: ``src.dashboard.data_provider.load_segments()`` 계약을 만족하는 DataFrame.

    Returns:
        렌더링 가능한 ``pydeck.Deck``.
    """
    plot_df = _unpack_path(df)

    layer = pdk.Layer(
        "LineLayer",
        id=SEGMENTS_LAYER_ID,
        data=plot_df,
        get_source_position="[lon1, lat1]",
        get_target_position="[lon2, lat2]",
        get_color="[color_r, color_g, color_b, color_a]",
        get_width=4,
        pickable=True,
        auto_highlight=True,
    )

    if len(plot_df):
        center_lat = float(plot_df["lat"].mean())
        center_lon = float(plot_df["lon"].mean())
    else:
        center_lat, center_lon = 37.6, 128.2

    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=9, pitch=0)

    tooltip = {
        "html": "<b>{road_name}</b> ({segment_id})<br/>"
        "위험도: {risk_icon} {risk_level} ({risk_score})<br/>"
        "도로 등급: {road_grade}",
        "style": {"backgroundColor": "#1a1a19", "color": "white"},
    }

    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=None,
    )


def render_legend() -> None:
    """위험도 4단계 범례를 렌더링한다 (색상 단독이 아니라 아이콘+라벨 병기)."""
    cols = st.columns(len(RISK_LEVELS))
    for col, level in zip(cols, RISK_LEVELS):
        r, g, b = level["color"]
        col.markdown(
            f"<div style='display:flex;align-items:center;gap:6px;'>"
            f"<span style='display:inline-block;width:14px;height:14px;"
            f"background:rgb({r},{g},{b});border-radius:3px;'></span>"
            f"<span>{level['icon']} {level['label']}</span></div>",
            unsafe_allow_html=True,
        )


def render_kpi_row(all_df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    """상단 KPI(핵심 지표) 행을 렌더링한다.

    Args:
        all_df: 필터 적용 전 전체 구간.
        filtered_df: 현재 필터가 적용된 구간 (지도에 표시 중인 것).
    """
    high_risk = filtered_df[filtered_df["risk_level"].isin(["위험", "매우 위험"])]
    avg_risk = filtered_df["risk_score"].mean() if len(filtered_df) else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 구간 수", f"{len(all_df):,}")
    c2.metric("표시 중 구간 수", f"{len(filtered_df):,}")
    c3.metric("고위험 구간 수", f"{len(high_risk):,}", help="'위험' 또는 '매우 위험' 등급")
    c4.metric("평균 위험도", f"{avg_risk:.2f}")


def render_segment_detail(row: pd.Series) -> None:
    """선택된 구간 하나의 상세 정보(피처·기여 요인·정책 브리핑)를 렌더링한다.

    Args:
        row: 구간 DataFrame의 한 행 (``pandas.Series``).
    """
    st.subheader(f"{row['road_name']} — {row['segment_id']}")
    st.markdown(f"**위험도**: {row['risk_icon']} {row['risk_level']} ({row['risk_score']:.2f})")

    st.markdown("**상위 기여 요인** (목업 — 실제 SHAP 아님)")
    for name, value in row["top_factors"]:
        direction = "위험 ↑" if value > 0 else "위험 ↓"
        st.markdown(f"- {name}: {value:+.3f} ({direction})")

    with st.expander("전체 피처 값 보기"):
        feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
        detail = pd.DataFrame(
            {
                "피처": [_FEATURE_LABELS.get(c, c) for c in feature_cols],
                # 숫자·문자열 피처가 섞여 있어 컬럼을 문자열로 통일한다.
                # (섞인 채로 두면 Streamlit이 Arrow 직렬화에 실패해 내부적으로
                # 복구 로직을 타면서 경고를 남긴다 — 처음부터 문자열로 맞춰 회피)
                "값": [
                    f"{row[c]:.2f}" if isinstance(row[c], float) else str(row[c])
                    for c in feature_cols
                ],
            }
        )
        st.dataframe(detail, hide_index=True, width="stretch")

    st.markdown("**정책 브리핑** (목업 — 실제 LLM 생성 아님)")
    st.info(row["policy_brief"])
