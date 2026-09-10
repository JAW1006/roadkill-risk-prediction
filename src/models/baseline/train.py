"""베이스라인 모델(RandomForest, XGBoost) 학습 CLI.

실행:
    python -m src.models.baseline.train --data data/processed/model_table.parquet

전처리가 아직 구현되지 않아 모델 테이블이 없다면, 먼저
``tests/test_baseline_pipeline.py`` 를 실행해 파이프라인 자체가 정상
동작하는지(합성 데이터 기준) 확인할 수 있다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from src.models.baseline.dataset import (
    add_season,
    get_feature_target,
    load_model_table,
    spatial_split,
    temporal_split,
)
from src.models.baseline.evaluate import confusion_matrix_report, evaluate_classifier
from src.models.baseline.models import build_random_forest, build_xgboost
from src.preprocessing.paths import PROCESSED_DIR, PROJECT_ROOT

DEFAULT_DATA_PATH = PROCESSED_DIR / "model_table.parquet"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "models" / "baseline"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "baseline_metrics.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="로드킬 위험도 베이스라인 모델 학습")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="모델 테이블 경로")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="학습된 모델 저장 경로")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="평가 지표 저장 경로 (JSON)")
    parser.add_argument(
        "--split",
        choices=["spatial", "temporal"],
        default="spatial",
        help="spatial: 구간 단위 분할(기본, 미관측 구간 예측력 평가) / "
        "temporal: 날짜 기준 분할(미래 시점 예측력 평가)",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="spatial split의 평가 세트 비율")
    parser.add_argument("--cutoff-date", type=str, default=None, help="temporal split 기준일 (YYYY-MM-DD)")
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def train_and_evaluate(
    data_path: Path,
    output_dir: Path,
    report_path: Path,
    split: str = "spatial",
    test_size: float = 0.2,
    cutoff_date: str | None = None,
    random_state: int = 42,
) -> dict[str, dict[str, float]]:
    """전체 학습·평가 파이프라인을 실행한다.

    Args:
        data_path: 모델 테이블 경로.
        output_dir: 학습된 모델(``.joblib``)을 저장할 디렉터리.
        report_path: 평가 지표를 저장할 JSON 경로.
        split: ``"spatial"`` 또는 ``"temporal"``.
        test_size: spatial split의 평가 세트 비율.
        cutoff_date: temporal split 기준일.
        random_state: 재현성을 위한 시드.

    Returns:
        모델 이름을 키로 하는 평가 지표 딕셔너리
        (``{"random_forest": {...}, "xgboost": {...}}``).
    """
    df = load_model_table(data_path)
    df = add_season(df)

    if split == "spatial":
        train_df, test_df = spatial_split(df, test_size=test_size, random_state=random_state)
    else:
        if cutoff_date is None:
            raise ValueError("split='temporal' 이면 --cutoff-date 를 지정해야 합니다.")
        train_df, test_df = temporal_split(df, cutoff_date=cutoff_date)

    X_train, y_train = get_feature_target(train_df)
    X_test, y_test = get_feature_target(test_df)

    print(f"[데이터] train={len(X_train)} (양성 {int(y_train.sum())}), "
          f"test={len(X_test)} (양성 {int(y_test.sum())}), split={split}")

    models = {
        "random_forest": build_random_forest(random_state=random_state),
        "xgboost": build_xgboost(y_train=y_train, random_state=random_state),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    metrics: dict[str, dict[str, float]] = {}
    for name, model in models.items():
        print(f"[학습] {name} ...")
        model.fit(X_train, y_train)

        result = evaluate_classifier(model, X_test, y_test)
        metrics[name] = result
        print(
            f"[평가] {name}: PR-AUC={result['pr_auc']:.4f}  ROC-AUC={result['roc_auc']:.4f}  "
            f"F1={result['f1']:.4f} (threshold={result['threshold']:.3f})"
        )
        print(confusion_matrix_report(model, X_test, y_test, threshold=result["threshold"]))

        model_path = output_dir / f"{name}.joblib"
        joblib.dump(model, model_path)
        print(f"[저장] {model_path}")

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"[저장] 평가 지표 -> {report_path}")

    return metrics


def main() -> None:
    args = parse_args()
    train_and_evaluate(
        data_path=args.data,
        output_dir=args.output_dir,
        report_path=args.report,
        split=args.split,
        test_size=args.test_size,
        cutoff_date=args.cutoff_date,
        random_state=args.random_state,
    )


if __name__ == "__main__":
    main()
