"""기상 데이터 로더.

출처
----
- 기상청 날씨누리 / 기상자료개방포털(data.kma.go.kr) 종관기상관측(ASOS),
  방재기상관측(AWS) 지점별 일자료

로드킬은 강수·안개·일출입 시각과 관련이 크므로, 사고 일자·지점에 맞춰
기상 조건을 붙이는 것이 목적이다. 관측은 지점 단위이므로 구간에서 최근접
관측소를 찾아 매칭한다.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


def load_weather_stations(path: str | Path) -> gpd.GeoDataFrame:
    """기상관측소 지점 목록(위경도 포함)을 읽어 반환한다.

    Args:
        path: 관측지점 정보 파일 경로 (CSV).

    Returns:
        ``station_id``, ``station_name``, Point 지오메트리를 가진 GeoDataFrame.
        좌표계는 :data:`~src.preprocessing.paths.CRS_METRIC`.

    Raises:
        FileNotFoundError: 경로에 파일이 없을 때.
    """
    raise NotImplementedError


def load_daily_weather(
    path: str | Path,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """관측소별 일 단위 기상 관측값을 읽어 반환한다.

    Args:
        path: ASOS/AWS 일자료 파일 경로 (CSV).
        start_date: 조회 시작일 (``YYYY-MM-DD``). ``None`` 이면 제한 없음.
        end_date: 조회 종료일 (``YYYY-MM-DD``). ``None`` 이면 제한 없음.

    Returns:
        ``station_id``, ``date``, ``temp_avg``, ``precipitation_mm``,
        ``humidity``, ``visibility_m``, ``snow_cm`` 컬럼을 가진 DataFrame.
    """
    raise NotImplementedError


def match_nearest_station(
    segments: gpd.GeoDataFrame,
    stations: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """각 도로 구간에 최근접 기상관측소를 매핑한다.

    Args:
        segments: 구간 GeoDataFrame.
        stations: :func:`load_weather_stations` 결과.

    Returns:
        ``segment_id``, ``station_id``, ``distance_m`` 컬럼을 가진 매핑 테이블.
    """
    raise NotImplementedError


def build_weather_features(
    events: pd.DataFrame,
    weather: pd.DataFrame,
    station_map: pd.DataFrame,
) -> pd.DataFrame:
    """구간-일자 단위로 기상 피처를 결합한다.

    베이스라인 모델은 구간-일자를 샘플로 두고 로드킬 발생 여부를 예측하므로,
    각 샘플에 해당 일자의 기상 조건을 붙인다.

    Args:
        events: ``segment_id``, ``date`` 를 가진 샘플 테이블.
        weather: :func:`load_daily_weather` 결과.
        station_map: :func:`match_nearest_station` 결과.

    Returns:
        기상 컬럼이 결합된 DataFrame. 결측 관측일은 인접일 보간으로 채운다.
    """
    raise NotImplementedError
