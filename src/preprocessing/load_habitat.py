"""야생동물 서식지 및 생태통로 데이터 로더.

출처
----
- 국립생태원 에코뱅크: 야생동물 서식지 분포, 생태통로 위치·유형
- (보조) 환경공간정보서비스 토지피복도: 산림·농경지 비율

로드킬은 서식지가 도로로 단절된 지점에서 집중되므로, 구간에서 서식지·
생태통로까지의 거리와 주변 토지피복 구성이 핵심 설명 변수가 된다.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd


def load_habitat_areas(path: str | Path) -> gpd.GeoDataFrame:
    """야생동물 서식지 폴리곤을 읽어 GeoDataFrame으로 반환한다.

    Args:
        path: 에코뱅크 서식지 SHP 또는 GeoPackage 경로.

    Returns:
        Polygon 지오메트리와 서식지 유형·대상종 속성을 가진 GeoDataFrame.
        좌표계는 :data:`~src.preprocessing.paths.CRS_METRIC`.

    Raises:
        FileNotFoundError: 경로에 파일이 없을 때.
    """
    raise NotImplementedError


def load_eco_corridors(path: str | Path) -> gpd.GeoDataFrame:
    """생태통로(육교형·터널형) 위치를 읽어 GeoDataFrame으로 반환한다.

    Args:
        path: 에코뱅크 생태통로 현황 파일 경로.

    Returns:
        Point 또는 LineString 지오메트리와 통로 유형·준공연도·관리기관
        속성을 가진 GeoDataFrame.

    Raises:
        FileNotFoundError: 경로에 파일이 없을 때.
    """
    raise NotImplementedError


def load_landcover(path: str | Path) -> gpd.GeoDataFrame:
    """토지피복도를 읽어 GeoDataFrame으로 반환한다.

    Args:
        path: 토지피복도 SHP 경로.

    Returns:
        피복 분류 코드를 가진 Polygon GeoDataFrame.
    """
    raise NotImplementedError


def compute_habitat_features(
    segments: gpd.GeoDataFrame,
    habitats: gpd.GeoDataFrame,
    corridors: gpd.GeoDataFrame,
    landcover: gpd.GeoDataFrame | None = None,
    *,
    buffer_m: int = 1000,
) -> gpd.GeoDataFrame:
    """구간별 서식지·생태통로 관련 피처를 계산한다.

    산출 피처:
      - ``dist_to_habitat_m``: 최근접 서식지까지 거리
      - ``habitat_ratio``: 버퍼 내 서식지 면적 비율
      - ``dist_to_corridor_m``: 최근접 생태통로까지 거리
      - ``forest_ratio`` / ``farmland_ratio``: 버퍼 내 토지피복 비율
        (``landcover`` 제공 시)

    Args:
        segments: 구간 GeoDataFrame.
        habitats: :func:`load_habitat_areas` 결과.
        corridors: :func:`load_eco_corridors` 결과.
        landcover: :func:`load_landcover` 결과. ``None`` 이면 피복 피처 생략.
        buffer_m: 구간 주변 분석 반경(m).

    Returns:
        위 피처가 추가된 구간 GeoDataFrame.
    """
    raise NotImplementedError
