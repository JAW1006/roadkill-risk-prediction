"""지형(DEM) 데이터 로더.

출처
----
- 국가공간정보포털(nsdi.go.kr) 수치표고모델(DEM)

DEM 래스터에서 고도·경사·사면방향을 계산해 도로 구간에 부여한다. 급경사·
산지 통과 구간은 동물 이동 경로와 도로가 교차할 확률이 높다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd


def load_dem(path: str | Path) -> Any:
    """DEM 래스터를 열어 rasterio 데이터셋 핸들을 반환한다.

    Args:
        path: DEM 파일 경로 (GeoTIFF).

    Returns:
        열린 ``rasterio.DatasetReader``. 호출자가 ``close()`` 하거나
        컨텍스트 매니저로 감싸 사용한다.

    Raises:
        FileNotFoundError: 경로에 파일이 없을 때.
    """
    raise NotImplementedError


def compute_slope_aspect(dem_path: str | Path, out_dir: str | Path) -> dict[str, Path]:
    """DEM에서 경사도·사면방향 래스터를 파생 생성해 저장한다.

    QGIS에서 수동 생성한 결과를 쓸 수도 있으나, 파이프라인 재현성을 위해
    코드로도 동일 산출물을 만들 수 있게 둔다.

    Args:
        dem_path: 원본 DEM GeoTIFF 경로.
        out_dir: 파생 래스터를 저장할 디렉터리.

    Returns:
        ``{"slope": Path, "aspect": Path}`` 형태의 산출 파일 경로 딕셔너리.
    """
    raise NotImplementedError


def sample_terrain_at_segments(
    segments: gpd.GeoDataFrame,
    dem_path: str | Path,
    slope_path: str | Path | None = None,
    aspect_path: str | Path | None = None,
) -> gpd.GeoDataFrame:
    """구간 위치에서 지형 값을 샘플링해 피처로 추가한다.

    구간은 선형이므로 중점 기준 값과 구간 전체의 평균/표준편차를 함께 낸다.
    표준편차가 크면 기복이 심한 구간이라는 뜻이다.

    Args:
        segments: 구간 GeoDataFrame.
        dem_path: DEM GeoTIFF 경로.
        slope_path: 경사도 래스터 경로. ``None`` 이면 DEM에서 즉시 계산.
        aspect_path: 사면방향 래스터 경로. ``None`` 이면 DEM에서 즉시 계산.

    Returns:
        ``elevation_m``, ``slope_deg``, ``slope_std``, ``aspect_deg`` 가
        추가된 구간 GeoDataFrame.
    """
    raise NotImplementedError
