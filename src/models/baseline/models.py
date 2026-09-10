"""베이스라인 모델 정의: RandomForest, XGBoost.

로드킬은 전체 구간-일자 샘플 중 극소수만 발생하는 희소 이벤트(rare event)다.
두 모델 모두 오버샘플링 대신 클래스 가중치 방식으로 불균형을 다룬다.
CV 폴드마다 학습 데이터로만 재계산해야 하는 오버샘플링(SMOTE 등)과 달리
가중치 방식은 데이터 누수 위험이 없고 구현이 단순하다.
"""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from src.models.baseline.pipeline import build_preprocessor


def build_random_forest(
    n_estimators: int = 300,
    max_depth: int | None = None,
    random_state: int = 42,
    n_jobs: int = -1,
) -> Pipeline:
    """전처리 + RandomForestClassifier 파이프라인을 만든다.

    ``class_weight="balanced_subsample"`` 로 각 트리의 부트스트랩 샘플마다
    클래스 비율에 따라 가중치를 재계산해 희소 이벤트(로드킬 발생)에 더
    민감하게 만든다.

    Args:
        n_estimators: 트리 개수.
        max_depth: 트리 최대 깊이. ``None`` 이면 제한 없음(과적합 주의).
        random_state: 재현성을 위한 시드.
        n_jobs: 병렬 처리 코어 수. ``-1`` 이면 전체 사용.

    Returns:
        ``fit(X, y)`` 가능한 ``sklearn.pipeline.Pipeline``.
    """
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=n_jobs,
    )
    return Pipeline(steps=[("preprocessor", build_preprocessor()), ("model", clf)])


def build_xgboost(
    y_train: pd.Series,
    n_estimators: int = 300,
    max_depth: int = 6,
    learning_rate: float = 0.1,
    random_state: int = 42,
    n_jobs: int = -1,
) -> Pipeline:
    """전처리 + XGBClassifier 파이프라인을 만든다.

    ``scale_pos_weight`` 를 학습 세트의 음성/양성 비율로 설정해 불균형을
    보정한다. 이 값은 세트마다 달라지므로 ``y_train`` 을 받아 즉석에서
    계산한다 — 반드시 학습 세트의 ``y`` 만 넘겨야 하며, 평가 세트를 섞으면
    데이터 누수가 된다.

    Args:
        y_train: 학습 세트의 타깃 벡터 (0/1). ``scale_pos_weight`` 계산에만
            쓰이고 모델에 직접 들어가지 않는다.
        n_estimators: 부스팅 라운드 수.
        max_depth: 트리 최대 깊이.
        learning_rate: 학습률.
        random_state: 재현성을 위한 시드.
        n_jobs: 병렬 처리 코어 수. ``-1`` 이면 전체 사용.

    Returns:
        ``fit(X, y)`` 가능한 ``sklearn.pipeline.Pipeline``.
    """
    n_pos = int((y_train == 1).sum())
    n_neg = int((y_train == 0).sum())
    scale_pos_weight = (n_neg / n_pos) if n_pos > 0 else 1.0

    clf = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        random_state=random_state,
        n_jobs=n_jobs,
    )
    return Pipeline(steps=[("preprocessor", build_preprocessor()), ("model", clf)])
