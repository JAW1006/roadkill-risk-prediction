"""대시보드가 소비하는 데이터의 단일 진입점.

대시보드 화면(``app.py``, ``components.py``)은 데이터가 목업인지 실제
파이프라인 결과인지 몰라도 되도록, 이 모듈 하나만 거쳐서 데이터를 받는다.
지금은 :func:`load_segments` 가 :mod:`src.dashboard.mock_data` 를 호출하지만,
실제 데이터가 준비되면 이 함수 내부만 아래 계약(contract)을 만족하는 실제
로더로 바꾸면 되고 ``app.py``/``components.py`` 는 손댈 필요가 없다.

데이터 계약 (``load_segments()`` 반환 DataFrame이 갖춰야 하는 컬럼)
--------------------------------------------------------------
- ``segment_id`` (str, 고유값)
- ``road_name`` (str)
- ``road_grade`` (str, 범주형)
- ``path`` (``[[lon, lat], [lon, lat]]`` — pydeck LineLayer용 시종점)
- ``lon``, ``lat`` (float, 구간 중점 — 정렬/검색용)
- ``risk_score`` (float, 0~1)
- ``risk_level`` (str — "안전"/"주의"/"위험"/"매우 위험")
- ``risk_icon`` (str, 이모지)
- ``color_r``, ``color_g``, ``color_b``, ``color_a`` (int 0~255, pydeck 색상)
- ``top_factors`` (``list[tuple[str, float]]`` — 상위 기여 요인)
- ``policy_brief`` (str — 정책 브리핑 텍스트)
- 그 외 ``src.models.baseline.schema`` 의 ``NUMERIC_FEATURES``/``CATEGORICAL_FEATURES``
  전체 (상세 패널에 원본 피처값을 보여주기 위함)
"""

from __future__ import annotations

import pandas as pd

from src.dashboard.mock_data import generate_mock_segments

# 실제 파이프라인이 준비되면 False로 바꾸고 아래 분기에 실제 로더를 연결한다.
USE_MOCK_DATA = True


def load_segments() -> pd.DataFrame:
    """대시보드에 표시할 구간 테이블을 불러온다.

    Returns:
        모듈 docstring의 데이터 계약을 만족하는 DataFrame.
    """
    if USE_MOCK_DATA:
        return generate_mock_segments()

    # TODO(전처리·베이스라인·GNN 완료 후): 학습된 모델의 예측 결과와
    # src.models.baseline.interpret 의 SHAP 기여도, src.llm 의 정책 브리핑을
    # 여기서 읽어와 위 계약에 맞는 DataFrame으로 조립한다.
    raise NotImplementedError(
        "실제 데이터 로더가 아직 연결되지 않았습니다. "
        "USE_MOCK_DATA=True 상태로 목업 데이터를 사용하세요."
    )
