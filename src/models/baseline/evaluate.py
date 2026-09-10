"""희소 이벤트(로드킬) 분류 평가 지표.

로드킬 발생 비율이 낮을 것으로 예상되므로 ROC-AUC는 낙관적으로 보일 수
있다(음성이 압도적으로 많으면 무의미한 분류기도 ROC-AUC가 높게 나온다).
PR-AUC(average precision)를 주 지표로 삼는다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline


def find_best_threshold(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """F1 점수를 최대화하는 분류 임계값을 찾는다.

    기본 임계값 0.5는 불균형 데이터에서 거의 항상 최적이 아니다. 정밀도-재현율
    곡선 위의 모든 후보 임계값 중 F1이 가장 높은 지점을 고른다.

    Args:
        y_true: 실제 타깃(0/1) 배열.
        y_proba: 양성 클래스 예측 확률 배열.

    Returns:
        F1 최대화 임계값.
    """
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    f1_scores = np.divide(
        2 * precision * recall,
        precision + recall,
        out=np.zeros_like(precision),
        where=(precision + recall) != 0,
    )
    # precision_recall_curve는 thresholds보다 원소가 1개 더 많은 배열을 반환한다
    # (마지막 지점은 임계값 없이 recall=0, precision=1인 경계값이므로 제외).
    best_idx = int(np.argmax(f1_scores[:-1])) if len(thresholds) > 0 else 0
    return float(thresholds[best_idx]) if len(thresholds) > 0 else 0.5


def evaluate_classifier(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float | None = None,
) -> dict[str, float]:
    """분류기를 평가하고 지표 딕셔너리를 반환한다.

    Args:
        model: 학습 완료된 파이프라인 (``predict_proba`` 지원 필요).
        X_test: 평가 세트 피처.
        y_test: 평가 세트 타깃(0/1).
        threshold: 양성 판정 임계값. ``None`` 이면 :func:`find_best_threshold`
            로 F1 최대화 임계값을 자동 탐색한다.

    Returns:
        ``pr_auc``, ``roc_auc``, ``precision``, ``recall``, ``f1``,
        ``threshold``, ``n_positive``, ``n_samples`` 를 담은 딕셔너리.

    Raises:
        ValueError: ``y_test`` 에 양성 또는 음성 클래스가 하나도 없을 때
            (ROC-AUC/PR-AUC가 정의되지 않는다). 분할 함수를 바꾸거나
            ``random_state``/``test_size`` 를 조정해야 한다.
    """
    if y_test.nunique() < 2:
        raise ValueError(
            f"평가 세트에 클래스가 하나뿐입니다 (양성={int(y_test.sum())}, "
            f"전체={len(y_test)}). ROC-AUC/PR-AUC를 계산할 수 없습니다 — "
            "분할 방식이나 시드를 바꿔서 평가 세트에 양쪽 클래스가 모두 있도록 하세요."
        )
    y_proba = model.predict_proba(X_test)[:, 1]

    if threshold is None:
        threshold = find_best_threshold(y_test.to_numpy(), y_proba)
    y_pred = (y_proba >= threshold).astype(int)

    return {
        "pr_auc": float(average_precision_score(y_test, y_proba)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "threshold": float(threshold),
        "n_positive": int(y_test.sum()),
        "n_samples": int(len(y_test)),
    }


def confusion_matrix_report(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float,
) -> pd.DataFrame:
    """혼동행렬을 라벨이 붙은 DataFrame으로 반환한다.

    Args:
        model: 학습 완료된 파이프라인.
        X_test: 평가 세트 피처.
        y_test: 평가 세트 타깃(0/1).
        threshold: 양성 판정 임계값.

    Returns:
        행=실제, 열=예측인 2x2 DataFrame.
    """
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    return pd.DataFrame(
        cm,
        index=["실제: 미발생(0)", "실제: 발생(1)"],
        columns=["예측: 미발생(0)", "예측: 발생(1)"],
    )
