"""RandomForest·XGBoost 공통 전처리 파이프라인.

두 모델이 정확히 같은 전처리를 받도록 ``ColumnTransformer`` 하나를 공유한다.
트리 기반 모델이라 스케일링은 불필요하지만, 결측치 대체와 범주형 인코딩은
필요하다.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.models.baseline.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def build_preprocessor() -> ColumnTransformer:
    """수치형 결측치 대체 + 범주형 원-핫 인코딩 전처리기를 만든다.

    수치형: 중앙값 대체. 기상 관측 결측(예: 관측소 장애일)이 발생할 수
    있어 평균보다 이상치에 덜 민감한 중앙값을 쓴다.
    범주형: 최빈값 대체 후 원-핫 인코딩. 학습 시 보지 못한 범주(예: 신규
    도로 등급 코드)가 평가/실서비스 단계에서 나타나도 에러 없이 무시한다.

    Returns:
        ``fit``/``transform`` 가능한 ``ColumnTransformer``.
    """
    numeric_pipeline = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def get_output_feature_names(preprocessor: ColumnTransformer) -> list[str]:
    """전처리 후 컬럼 순서를 사람이 읽을 수 있는 이름으로 반환한다.

    SHAP 등 해석 단계에서 원-핫 인코딩된 컬럼(``categorical__road_grade_고속국도``
    등)을 원래 피처 이름과 매핑할 때 사용한다.

    Args:
        preprocessor: :func:`build_preprocessor` 로 만들고 ``fit`` 완료한
            ``ColumnTransformer``.

    Returns:
        변환 후 컬럼 이름 리스트 (``numeric__``/``categorical__`` 접두어는
        제거한 상태).
    """
    names = preprocessor.get_feature_names_out()
    return [n.split("__", 1)[-1] for n in names]
