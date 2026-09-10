"""베이스라인 모델: RandomForest, XGBoost.

기본 사용 순서:
    1. ``schema.py``      — 모델 테이블이 갖춰야 할 컬럼 정의
    2. ``dataset.py``     — 테이블 로딩, 계절 피처 파생, train/test 분할
    3. ``pipeline.py``    — 공통 전처리(결측치 대체, 원-핫 인코딩)
    4. ``models.py``      — RandomForest/XGBoost 파이프라인 생성
    5. ``evaluate.py``    — PR-AUC 중심 평가 지표
    6. ``interpret.py``   — SHAP 기반 변수 기여도 (정책 브리핑에 재사용)
    7. ``train.py``       — 위 전체를 엮은 CLI (``python -m src.models.baseline.train``)
"""

from src.models.baseline.dataset import (
    add_season,
    get_feature_target,
    load_model_table,
    spatial_split,
    temporal_split,
)
from src.models.baseline.evaluate import (
    confusion_matrix_report,
    evaluate_classifier,
    find_best_threshold,
)
from src.models.baseline.interpret import (
    compute_shap_values,
    global_feature_importance,
    top_feature_contributions,
)
from src.models.baseline.models import build_random_forest, build_xgboost
from src.models.baseline.pipeline import build_preprocessor, get_output_feature_names

__all__ = [
    "load_model_table",
    "add_season",
    "spatial_split",
    "temporal_split",
    "get_feature_target",
    "build_preprocessor",
    "get_output_feature_names",
    "build_random_forest",
    "build_xgboost",
    "evaluate_classifier",
    "find_best_threshold",
    "confusion_matrix_report",
    "compute_shap_values",
    "top_feature_contributions",
    "global_feature_importance",
]
