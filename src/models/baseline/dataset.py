"""베이스라인 모델 학습용 데이터 로딩 및 분할.

``src/preprocessing`` 가 만들어낼 구간-일자 단위 모델 테이블을 읽어
학습/평가 세트로 나눈다. 로드킬은 같은 구간에서 반복 관측되므로 단순
무작위 분할(random split)을 쓰면 같은 구간이 학습·평가 양쪽에 들어가
공간적 정보 누수(leakage)가 생긴다. 기본값은 구간(``segment_id``) 단위로
통째로 나누는 spatial split이며, "미래 시점 예측" 시나리오를 검증하고
싶을 때는 temporal split을 쓸 수 있다.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold

from src.models.baseline.schema import (
    CATEGORICAL_FEATURES,
    DATE_COL,
    FEATURE_COLUMNS,
    GROUP_COL,
    RAW_REQUIRED_COLUMNS,
    TARGET_COL,
)

_SEASON_BY_MONTH = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "fall", 10: "fall", 11: "fall",
}


def load_model_table(path: str | Path) -> pd.DataFrame:
    """전처리 파이프라인이 만든 구간-일자 모델 테이블을 읽는다.

    Args:
        path: parquet 또는 csv 파일 경로 (``src.models.baseline.schema``의
            ``RAW_REQUIRED_COLUMNS`` 를 만족해야 한다).

    Returns:
        원본 컬럼을 보존한 DataFrame. ``date`` 컬럼은 datetime으로 변환된다.

    Raises:
        FileNotFoundError: 경로에 파일이 없을 때.
        ValueError: 필수 컬럼이 빠져 있을 때.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"모델 테이블을 찾을 수 없습니다: {path}\n"
            "전처리(src/preprocessing)가 아직 구현되지 않았다면, "
            "tests/test_baseline_pipeline.py 의 합성 데이터로 파이프라인 동작만 먼저 확인하세요."
        )

    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)

    missing = set(RAW_REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            f"모델 테이블에 필수 컬럼이 없습니다: {sorted(missing)}\n"
            f"기대하는 스키마: src/models/baseline/schema.py 의 RAW_REQUIRED_COLUMNS 참고"
        )

    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    return df


def add_season(df: pd.DataFrame) -> pd.DataFrame:
    """``date`` 컬럼에서 계절(``season``) 피처를 파생시킨다.

    로드킬은 번식기·이동철 등 계절성이 뚜렷하므로 월(month)을 4계절로
    묶어 범주형 피처로 넣는다.

    Args:
        df: ``date`` 컬럼(datetime)을 가진 DataFrame.

    Returns:
        ``season`` 컬럼이 추가된 DataFrame (원본은 변경하지 않음).
    """
    out = df.copy()
    out["season"] = out[DATE_COL].dt.month.map(_SEASON_BY_MONTH)
    return out


def spatial_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """구간(``segment_id``) 단위로 학습/평가 세트를 분리한다 (기본 분할 전략).

    같은 구간의 서로 다른 날짜 샘플이 학습과 평가에 동시에 들어가지 않도록
    구간 전체를 한쪽에만 배정한다. "한 번도 본 적 없는 구간의 위험도를
    얼마나 잘 맞히는가"를 평가하며, 대시보드가 실제로 하는 일(신규/미관측
    구간에 대한 위험도 추정)과 가장 가깝다.

    로드킬처럼 양성이 매우 희귀하면 순수 무작위 그룹 분할은 운이 나쁠 경우
    평가 세트에 양성이 하나도 들어가지 않을 수 있다(이 경우 ROC-AUC 등이
    정의되지 않아 평가가 실패한다). 이를 피하기 위해
    :class:`~sklearn.model_selection.StratifiedGroupKFold` 로 그룹을
    유지하면서 양성 비율도 최대한 균등하게 배분한다. 그룹 수가 너무 적어
    계층화가 불가능하면 일반 :class:`~sklearn.model_selection.GroupShuffleSplit`
    로 자동 대체한다.

    Args:
        df: :func:`load_model_table` 결과.
        test_size: 평가 세트로 뺄 구간 비율.
        random_state: 재현성을 위한 시드.

    Returns:
        ``(train_df, test_df)`` 튜플.
    """
    n_splits = max(2, round(1 / test_size))
    try:
        splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        train_idx, test_idx = next(
            splitter.split(df, y=df[TARGET_COL], groups=df[GROUP_COL])
        )
    except ValueError:
        # 그룹 수가 n_splits보다 적는 등 계층화 분할이 불가능한 경우의 대체 경로.
        splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
        train_idx, test_idx = next(splitter.split(df, groups=df[GROUP_COL]))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    if test_df[TARGET_COL].sum() == 0:
        raise ValueError(
            "spatial_split 결과 평가 세트에 양성(로드킬 발생) 샘플이 하나도 없습니다. "
            "양성 비율이 너무 낮거나 구간 수가 너무 적을 수 있습니다 — "
            "random_state를 바꾸거나 test_size를 늘려서 다시 시도하세요."
        )
    return train_df, test_df


def temporal_split(
    df: pd.DataFrame,
    cutoff_date: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """기준일 이전/이후로 학습/평가 세트를 분리한다 (미래 예측 시나리오 검증용).

    Args:
        df: :func:`load_model_table` 결과.
        cutoff_date: 기준일 (``YYYY-MM-DD``). 이 날짜 이전은 학습, 이후는 평가.

    Returns:
        ``(train_df, test_df)`` 튜플.
    """
    cutoff = pd.Timestamp(cutoff_date)
    train_df = df[df[DATE_COL] < cutoff].reset_index(drop=True)
    test_df = df[df[DATE_COL] >= cutoff].reset_index(drop=True)
    if train_df.empty or test_df.empty:
        raise ValueError(
            f"cutoff_date={cutoff_date} 로 나누면 한쪽 세트가 비어 있습니다 "
            f"(train={len(train_df)}, test={len(test_df)}). 데이터 기간을 확인하세요."
        )
    if test_df[TARGET_COL].sum() == 0:
        raise ValueError(
            f"cutoff_date={cutoff_date} 이후 평가 세트에 양성(로드킬 발생) 샘플이 없습니다. "
            "cutoff_date를 앞당기거나 데이터 기간을 늘려서 다시 시도하세요."
        )
    return train_df, test_df


def get_feature_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """피처 행렬 ``X`` 와 타깃 벡터 ``y`` 로 분리한다.

    ``season`` 이 없으면 :func:`add_season` 을 먼저 적용한다.

    Args:
        df: 모델 테이블 (raw 또는 season 파생 완료 상태 모두 허용).

    Returns:
        ``(X, y)`` — ``X`` 는 ``schema.FEATURE_COLUMNS`` 순서의 DataFrame,
        ``y`` 는 0/1 정수형 Series.
    """
    if "season" not in df.columns:
        df = add_season(df)

    missing = set(FEATURE_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"피처 컬럼이 없습니다: {sorted(missing)}")

    X = df[FEATURE_COLUMNS].copy()
    for col in CATEGORICAL_FEATURES:
        X[col] = X[col].astype("category")
    y = df[TARGET_COL].astype(int)
    return X, y
