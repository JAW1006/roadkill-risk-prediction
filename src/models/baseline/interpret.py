"""SHAP 기반 변수 기여도 해석.

여기서 계산하는 피처별 기여도는 이후 LLM 정책 브리핑 단계
(``src/llm``)에서 "이 구간이 왜 위험한지"를 자연어로 설명하는 근거
자료로 그대로 재사용된다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline

from src.models.baseline.pipeline import get_output_feature_names


def compute_shap_values(model: Pipeline, X: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """학습된 트리 모델(RandomForest/XGBoost)의 SHAP 값을 계산한다.

    ``model`` 은 ``(preprocessor, model)`` 2단계 파이프라인이어야 한다.
    SHAP은 전처리 이후(원-핫 인코딩된) 피처 공간에서 계산되므로, 함께
    반환하는 피처 이름과 짝을 맞춰 사용해야 한다.

    Args:
        model: :func:`src.models.baseline.models.build_random_forest` 또는
            :func:`~src.models.baseline.models.build_xgboost` 로 만들고
            학습을 마친 파이프라인.
        X: SHAP 값을 계산할 원본(전처리 전) 피처 DataFrame. 샘플이 많으면
            느려지므로 호출 전에 서브샘플링하는 것을 권장한다.

    Returns:
        ``(shap_values, feature_names)`` — ``shap_values`` 는
        ``(n_samples, n_features)`` 배열(양성 클래스 기준),
        ``feature_names`` 는 전처리 후 컬럼 이름 리스트.
    """
    preprocessor = model.named_steps["preprocessor"]
    estimator = model.named_steps["model"]

    X_transformed = preprocessor.transform(X)
    if hasattr(X_transformed, "toarray"):
        X_transformed = X_transformed.toarray()

    explainer = shap.TreeExplainer(estimator)
    raw_values = explainer.shap_values(X_transformed)

    # RandomForest(이진 분류)는 (n_samples, n_features, n_classes) 배열을
    # 반환할 수 있다 — 양성 클래스(index 1)만 취한다. XGBoost는 이미
    # (n_samples, n_features) 형태를 반환한다.
    if isinstance(raw_values, list):
        shap_values = raw_values[1]
    elif raw_values.ndim == 3:
        shap_values = raw_values[:, :, 1]
    else:
        shap_values = raw_values

    return shap_values, get_output_feature_names(preprocessor)


def top_feature_contributions(
    shap_values: np.ndarray,
    feature_names: list[str],
    sample_index: int,
    top_n: int = 5,
) -> pd.DataFrame:
    """특정 샘플(구간-일자)에 대해 위험도를 가장 크게 밀어올린 피처를 뽑는다.

    정책 브리핑 생성 시 "이 구간이 위험한 이유"를 순서대로 나열하는 데
    사용한다.

    Args:
        shap_values: :func:`compute_shap_values` 의 첫 번째 반환값.
        feature_names: :func:`compute_shap_values` 의 두 번째 반환값.
        sample_index: ``shap_values`` 내 대상 샘플의 행 인덱스.
        top_n: 반환할 상위 피처 개수.

    Returns:
        ``feature``, ``shap_value`` 컬럼을 가진 DataFrame. 절댓값 기준
        내림차순 정렬 (양수 = 위험도를 높이는 방향).
    """
    row = shap_values[sample_index]
    order = np.argsort(-np.abs(row))[:top_n]
    return pd.DataFrame(
        {
            "feature": [feature_names[i] for i in order],
            "shap_value": [float(row[i]) for i in order],
        }
    )


def global_feature_importance(
    shap_values: np.ndarray,
    feature_names: list[str],
) -> pd.DataFrame:
    """전체 샘플에 대한 평균 |SHAP| 기준 전역 변수 중요도를 계산한다.

    Args:
        shap_values: :func:`compute_shap_values` 의 첫 번째 반환값.
        feature_names: :func:`compute_shap_values` 의 두 번째 반환값.

    Returns:
        ``feature``, ``mean_abs_shap`` 컬럼을 가진 DataFrame. 내림차순 정렬.
    """
    importance = np.abs(shap_values).mean(axis=0)
    return (
        pd.DataFrame({"feature": feature_names, "mean_abs_shap": importance})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )
