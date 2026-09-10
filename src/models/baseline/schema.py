"""베이스라인 모델의 입력 테이블(모델 테이블) 스키마 정의.

``src/preprocessing`` 의 각 로더가 만들어낼 피처를 하나의 "구간-일자
(segment-date)" 단위 샘플로 결합한 테이블을 가정한다. 한 행 = 특정 날짜에
특정 도로 구간에서 로드킬이 발생했는지 여부(``TARGET_COL``)이다.

이 파일이 정의하는 컬럼명은 ``src/preprocessing`` 각 모듈의 docstring에서
약속한 산출 컬럼(``curvature``, ``dist_to_habitat_m``, ``elevation_m`` 등)과
일치하도록 맞춰뒀다. 전처리가 구현되면 이 스키마에 맞는 테이블
(``data/processed/model_table.parquet``)을 만들어내면 된다.
"""

from __future__ import annotations

# ── 식별자 / 메타 컬럼 (피처로 사용하지 않음) ────────────────────────────
ID_COL = "segment_id"
DATE_COL = "date"

# ── 타깃 ────────────────────────────────────────────────────────────────
# 해당 구간-일자에 로드킬이 1건 이상 발생했는지 여부 (이진 분류)
TARGET_COL = "roadkill_occurred"

# GNN 단계(src/models/gnn)에서 구간 인접 그래프를 구성할 때 사용할 컬럼.
# 베이스라인은 각 구간을 독립 샘플로 취급하므로 피처로 쓰지 않는다.
GROUP_COL = ID_COL  # 공간 누수 방지를 위한 spatial split 그룹 키

# ── 수치형 피처 ────────────────────────────────────────────────────────
NUMERIC_FEATURES: list[str] = [
    # 도로 형상 (load_road_network.py)
    "length_m",
    "road_width_m",
    "lane_count",
    "speed_limit_kmh",
    "aadt",
    "curvature",
    "sinuosity",
    # 서식지 · 생태통로 (load_habitat.py)
    "dist_to_habitat_m",
    "habitat_ratio",
    "dist_to_corridor_m",
    "forest_ratio",
    "farmland_ratio",
    # 지형 (load_terrain.py)
    "elevation_m",
    "slope_deg",
    "slope_std",
    # 기상 (load_weather.py) — 구간-일자 단위이므로 결측 발생 가능
    "temp_avg",
    "precipitation_mm",
    "humidity",
    "visibility_m",
    "snow_cm",
]

# ── 범주형 피처 ────────────────────────────────────────────────────────
CATEGORICAL_FEATURES: list[str] = [
    "road_grade",  # 고속국도/일반국도/지방도 등 (load_road_network.py)
    "season",      # date에서 파생 (dataset.py의 add_season 참고)
]

FEATURE_COLUMNS: list[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# "season"은 date 컬럼에서 파생되므로(dataset.add_season 참고) 원본 테이블에는
# 없어도 된다. 원본 테이블이 최소한 갖춰야 하는 컬럼은 아래 두 가지로 나눈다.
RAW_CATEGORICAL_FEATURES: list[str] = [c for c in CATEGORICAL_FEATURES if c != "season"]
RAW_REQUIRED_COLUMNS: list[str] = [
    ID_COL,
    DATE_COL,
    TARGET_COL,
    *NUMERIC_FEATURES,
    *RAW_CATEGORICAL_FEATURES,
]

# season 파생 이후, 모델 학습 직전 테이블이 갖춰야 하는 전체 컬럼
REQUIRED_COLUMNS: list[str] = [ID_COL, DATE_COL, TARGET_COL, *FEATURE_COLUMNS]
