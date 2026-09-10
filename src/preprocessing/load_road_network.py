"""도로망 데이터 로더 및 위험도 예측 단위(구간) 생성.

출처
----
- 공공데이터포털(data.go.kr) 표준노드링크 / 도로망 GIS 데이터
  : 도로 폭, 차로 수, 제한속도, 도로 등급
- 교통량(AADT): 국가교통DB / 도로교통량 통계연보

이 모듈이 만드는 **도로 구간(segment)** 이 프로젝트 전체의 예측 단위이자
GNN의 노드가 된다. 다른 모든 피처(기상·지형·서식지)는 이 구간에 조인된다.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


def load_road_network(path: str | Path) -> gpd.GeoDataFrame:
    """도로망 링크(선형) 데이터를 읽어 GeoDataFrame으로 반환한다.

    Args:
        path: 표준노드링크 SHP 또는 GeoPackage 경로.

    Returns:
        LineString 지오메트리와 도로 속성(도로등급, 차로수, 제한속도 등)을
        가진 GeoDataFrame. 좌표계는
        :data:`~src.preprocessing.paths.CRS_METRIC`.

    Raises:
        FileNotFoundError: 경로에 파일이 없을 때.
    """
    raise NotImplementedError


def load_traffic_volume(path: str | Path) -> pd.DataFrame:
    """도로 구간별 연평균 일교통량(AADT) 통계를 읽어 반환한다.

    Args:
        path: 교통량 통계 파일 경로 (CSV 또는 XLSX).

    Returns:
        도로 링크 ID를 키로 하는 교통량 DataFrame
        (``link_id``, ``aadt``, ``year``, 가능 시 대형차 혼입률).
    """
    raise NotImplementedError


def segment_roads(
    roads: gpd.GeoDataFrame,
    segment_length_m: int | None = None,
) -> gpd.GeoDataFrame:
    """도로 링크를 일정 길이의 구간으로 분할해 예측 단위를 만든다.

    링크는 길이 편차가 커서 그대로 쓰면 샘플 간 노출(exposure)이 달라진다.
    고정 길이로 잘라 구간별 로드킬 빈도를 비교 가능하게 만든다.

    Args:
        roads: :func:`load_road_network` 결과.
        segment_length_m: 구간 길이(m). ``None`` 이면
            :data:`~src.preprocessing.paths.SEGMENT_LENGTH_M` 사용.

    Returns:
        ``segment_id`` 를 가진 구간 GeoDataFrame. 원본 링크 속성을 상속하며
        ``length_m``, ``curvature``(곡률) 컬럼을 포함한다.
    """
    raise NotImplementedError


def compute_geometry_features(segments: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """구간 형상에서 곡률·방위각 등 기하 피처를 계산해 추가한다.

    곡률은 (구간 실제 연장 / 시종점 직선거리) 로 정의한다. 값이 1에 가까울수록
    직선 구간, 클수록 굽은 구간이다.

    Args:
        segments: :func:`segment_roads` 결과.

    Returns:
        ``curvature``, ``bearing``, ``sinuosity`` 가 추가된 GeoDataFrame.
    """
    raise NotImplementedError


def attach_traffic_volume(
    segments: gpd.GeoDataFrame,
    traffic: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """구간에 AADT 교통량을 조인한다.

    교통량 통계는 링크 단위로만 제공되므로 같은 링크에서 분할된 구간에는
    동일 값을 부여한다. 매칭 실패 구간은 도로 등급별 중앙값으로 대체한다.

    Args:
        segments: 구간 GeoDataFrame.
        traffic: :func:`load_traffic_volume` 결과.

    Returns:
        ``aadt`` 컬럼이 추가된 구간 GeoDataFrame.
    """
    raise NotImplementedError


def build_adjacency(segments: gpd.GeoDataFrame) -> pd.DataFrame:
    """구간 간 인접 관계(edge list)를 만든다 — GNN 입력용.

    두 구간이 끝점을 공유하면 인접한 것으로 본다. 공간적 자기상관을 학습
    시키기 위한 그래프 구조로, ``src/models/gnn`` 에서 ``edge_index`` 로
    변환해 사용한다.

    Args:
        segments: ``segment_id`` 를 가진 구간 GeoDataFrame.

    Returns:
        ``source``, ``target``, ``shared_node_id`` 컬럼을 가진 무방향 edge list.
    """
    raise NotImplementedError
