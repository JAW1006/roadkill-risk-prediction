"""프로젝트 전역 경로 및 좌표계(CRS) 상수.

데이터 로더가 공통으로 참조하는 설정만 담는다. 실제 데이터 I/O 로직은
각 ``load_*.py`` 모듈에 위치한다.
"""

from __future__ import annotations

import os
from pathlib import Path

# ── 디렉터리 ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / os.getenv("DATA_RAW_DIR", "data/raw")
PROCESSED_DIR = PROJECT_ROOT / os.getenv("DATA_PROCESSED_DIR", "data/processed")

# ── 좌표계 ──────────────────────────────────────────────────────────────
# 거리·면적·버퍼 등 미터 단위 공간 연산에 사용 (Korea 2000 / Unified CS)
CRS_METRIC = "EPSG:5179"
# 지도 시각화(folium/pydeck) 및 데이터 교환에 사용 (WGS84)
CRS_WGS84 = "EPSG:4326"

# ── 도로 구간 분할 기준 ─────────────────────────────────────────────────
# 도로망을 위험도 예측 단위로 자를 때의 기본 구간 길이(m).
# 베이스라인/GNN 모두 이 단위를 하나의 샘플(= GNN의 노드)로 취급한다.
SEGMENT_LENGTH_M = 500
