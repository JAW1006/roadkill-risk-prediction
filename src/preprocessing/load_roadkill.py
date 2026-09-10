"""로드킬 발생 지점 데이터 로더.

출처
----
- TAAS (도로교통공단 교통사고분석시스템): 로드킬 신고·사고 지점
- 국립생태원 에코뱅크: 야생동물 찻길사고 조사 지점

두 출처는 컬럼 스키마와 좌표계가 서로 다르므로 개별 로더로 읽은 뒤
:func:`load_roadkill_points` 에서 공통 스키마로 통합한다.

공통 스키마 (통합 후)
--------------------
=================  ==========================================================
컬럼                설명
=================  ==========================================================
``event_id``        고유 식별자 (출처 접두어 포함, 예: ``taas_000123``)
``occurred_at``     발생 일시 (tz-naive, Asia/Seoul 기준)
``species``         동물 종명 (원본 표기 유지)
``species_group``   종 분류군 (고라니/멧돼지/너구리/조류/기타)
``road_name``       도로명 (원본 제공 시)
``source``          출처 구분 (``taas`` / ``ecobank``)
``geometry``        Point, :data:`~src.preprocessing.paths.CRS_METRIC`
=================  ==========================================================
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd


def load_taas_roadkill(path: str | Path) -> gpd.GeoDataFrame:
    """TAAS 로드킬 사고 지점 원본을 읽어 GeoDataFrame으로 반환한다.

    Args:
        path: TAAS에서 내려받은 원본 파일 경로 (CSV 또는 SHP).

    Returns:
        원본 컬럼을 보존한 GeoDataFrame. 좌표계는
        :data:`~src.preprocessing.paths.CRS_METRIC` 으로 통일한다.

    Raises:
        FileNotFoundError: 경로에 파일이 없을 때.
    """
    raise NotImplementedError


def load_ecobank_roadkill(path: str | Path) -> gpd.GeoDataFrame:
    """에코뱅크 야생동물 찻길사고 조사 지점을 읽어 GeoDataFrame으로 반환한다.

    Args:
        path: 에코뱅크에서 내려받은 원본 파일 경로 (CSV 또는 SHP).

    Returns:
        원본 컬럼을 보존한 GeoDataFrame. 좌표계는
        :data:`~src.preprocessing.paths.CRS_METRIC` 으로 통일한다.

    Raises:
        FileNotFoundError: 경로에 파일이 없을 때.
    """
    raise NotImplementedError


def normalize_species(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """종명 표기를 정규화하고 ``species_group`` 분류군 컬럼을 부여한다.

    출처마다 같은 종을 다르게 표기하므로(예: "고라니" / "고라니(Hydropotes)")
    표기를 통일한 뒤 모델링에 쓸 분류군으로 묶는다.

    Args:
        gdf: ``species`` 컬럼을 가진 GeoDataFrame.

    Returns:
        ``species`` 가 정규화되고 ``species_group`` 이 추가된 GeoDataFrame.
    """
    raise NotImplementedError


def load_roadkill_points(
    taas_path: str | Path | None = None,
    ecobank_path: str | Path | None = None,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    species_group: str | None = None,
) -> gpd.GeoDataFrame:
    """TAAS·에코뱅크 로드킬 지점을 통합 스키마로 병합해 반환한다.

    모듈 docstring의 공통 스키마를 따르며, 두 출처 간 중복 신고로 추정되는
    지점(동일 일자 + 근접 거리)은 제거한다.

    Args:
        taas_path: TAAS 원본 경로. ``None`` 이면 ``data/raw`` 기본 경로 사용.
        ecobank_path: 에코뱅크 원본 경로. ``None`` 이면 기본 경로 사용.
        start_date: 조회 시작일 (``YYYY-MM-DD``). ``None`` 이면 제한 없음.
        end_date: 조회 종료일 (``YYYY-MM-DD``). ``None`` 이면 제한 없음.
        species_group: 특정 분류군만 필터링. ``None`` 이면 전체.

    Returns:
        공통 스키마를 따르는 GeoDataFrame.
    """
    raise NotImplementedError
