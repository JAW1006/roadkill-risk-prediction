"""데이터 로딩 및 전처리 모듈.

원본 공공데이터를 읽어 도로 구간(segment) 단위의 분석용 테이블로 변환한다.
모든 함수는 아직 스켈레톤 상태이며 ``NotImplementedError`` 를 발생시킨다.
"""

from src.preprocessing.load_habitat import (
    compute_habitat_features,
    load_eco_corridors,
    load_habitat_areas,
    load_landcover,
)
from src.preprocessing.load_road_network import (
    attach_traffic_volume,
    build_adjacency,
    compute_geometry_features,
    load_road_network,
    load_traffic_volume,
    segment_roads,
)
from src.preprocessing.load_roadkill import (
    load_ecobank_roadkill,
    load_roadkill_points,
    load_taas_roadkill,
    normalize_species,
)
from src.preprocessing.load_terrain import (
    compute_slope_aspect,
    load_dem,
    sample_terrain_at_segments,
)
from src.preprocessing.load_weather import (
    build_weather_features,
    load_daily_weather,
    load_weather_stations,
    match_nearest_station,
)
from src.preprocessing.paths import (
    CRS_METRIC,
    CRS_WGS84,
    PROCESSED_DIR,
    PROJECT_ROOT,
    RAW_DIR,
    SEGMENT_LENGTH_M,
)

__all__ = [
    # paths
    "PROJECT_ROOT",
    "RAW_DIR",
    "PROCESSED_DIR",
    "CRS_METRIC",
    "CRS_WGS84",
    "SEGMENT_LENGTH_M",
    # roadkill
    "load_taas_roadkill",
    "load_ecobank_roadkill",
    "normalize_species",
    "load_roadkill_points",
    # road network
    "load_road_network",
    "load_traffic_volume",
    "segment_roads",
    "compute_geometry_features",
    "attach_traffic_volume",
    "build_adjacency",
    # habitat
    "load_habitat_areas",
    "load_eco_corridors",
    "load_landcover",
    "compute_habitat_features",
    # weather
    "load_weather_stations",
    "load_daily_weather",
    "match_nearest_station",
    "build_weather_features",
    # terrain
    "load_dem",
    "compute_slope_aspect",
    "sample_terrain_at_segments",
]
