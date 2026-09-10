"""베이스라인 파이프라인 구조 검증 스크립트.

⚠️ 실제 로드킬 데이터가 아니다. 여기서 만드는 데이터는 난수로 생성한
합성(synthetic) 표본이며, "코드가 스키마대로 돌아가는가"만 확인한다.
지표 수치(PR-AUC 등)는 아무 의미가 없다 — 실제 데이터가 준비되면
``python -m src.models.baseline.train --data data/processed/model_table.parquet``
로 실행해야 한다.

실행: python tests/test_baseline_pipeline.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.models.baseline.dataset import add_season, get_feature_target, spatial_split
from src.models.baseline.evaluate import confusion_matrix_report, evaluate_classifier
from src.models.baseline.interpret import (
    compute_shap_values,
    global_feature_importance,
    top_feature_contributions,
)
from src.models.baseline.models import build_random_forest, build_xgboost
from src.models.baseline.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES, RAW_REQUIRED_COLUMNS


def make_synthetic_model_table(n_segments: int = 60, n_days: int = 30, seed: int = 0) -> pd.DataFrame:
    """스키마를 만족하는 무작위 구간-일자 테이블을 만든다 (구조 검증 전용)."""
    rng = np.random.default_rng(seed)
    segment_ids = [f"seg_{i:04d}" for i in range(n_segments)]
    dates = pd.date_range("2025-01-01", periods=n_days, freq="D")

    rows = []
    for seg_id in segment_ids:
        # 구간마다 고유한 "위험 성향"을 부여해 완전 무작위보다는 그럴듯한 구조를 만든다.
        base_habitat_ratio = rng.uniform(0, 1)
        base_dist_to_habitat = rng.uniform(0, 3000)
        for date in dates:
            row = {
                "segment_id": seg_id,
                "date": date,
                "length_m": rng.uniform(200, 800),
                "road_width_m": rng.uniform(3, 12),
                "lane_count": rng.integers(1, 5),
                "speed_limit_kmh": rng.choice([50, 60, 70, 80, 100]),
                "aadt": rng.uniform(500, 30000),
                "curvature": rng.uniform(1.0, 1.5),
                "sinuosity": rng.uniform(1.0, 1.3),
                "dist_to_habitat_m": max(0.0, base_dist_to_habitat + rng.normal(0, 50)),
                "habitat_ratio": np.clip(base_habitat_ratio + rng.normal(0, 0.05), 0, 1),
                "dist_to_corridor_m": rng.uniform(0, 5000),
                "forest_ratio": rng.uniform(0, 1),
                "farmland_ratio": rng.uniform(0, 1),
                "elevation_m": rng.uniform(0, 800),
                "slope_deg": rng.uniform(0, 30),
                "slope_std": rng.uniform(0, 10),
                "temp_avg": rng.uniform(-10, 30),
                "precipitation_mm": max(0.0, rng.normal(2, 5)),
                "humidity": rng.uniform(30, 90),
                "visibility_m": rng.uniform(500, 20000),
                "snow_cm": max(0.0, rng.normal(0, 1)),
                "road_grade": rng.choice(["고속국도", "일반국도", "지방도"]),
            }
            # 서식지에 가깝고 산림 비율이 높을수록 로드킬 확률이 높아지도록 설계
            risk_score = (
                0.4 * (1 - min(row["dist_to_habitat_m"] / 3000, 1))
                + 0.4 * row["forest_ratio"]
                + 0.2 * row["habitat_ratio"]
            )
            prob = np.clip(risk_score * 0.15, 0, 1)  # 희소 이벤트가 되도록 전체 확률을 낮춤
            row["roadkill_occurred"] = int(rng.random() < prob)
            rows.append(row)

    df = pd.DataFrame(rows)
    assert set(RAW_REQUIRED_COLUMNS) <= set(df.columns), "합성 데이터가 스키마를 만족하지 않습니다."
    return df


def main() -> None:
    print("=" * 60)
    print("베이스라인 파이프라인 구조 검증 (합성 데이터 — 실제 모델링 아님)")
    print("=" * 60)

    df = make_synthetic_model_table()
    print(f"합성 테이블: {len(df)}행, 양성 비율={df['roadkill_occurred'].mean():.3%}")

    df = add_season(df)
    assert "season" in df.columns

    train_df, test_df = spatial_split(df, test_size=0.2, random_state=0)
    train_segments = set(train_df["segment_id"])
    test_segments = set(test_df["segment_id"])
    assert train_segments.isdisjoint(test_segments), "spatial split에서 구간이 겹치면 안 됩니다."
    print(f"spatial split: train 구간 {len(train_segments)}개 / test 구간 {len(test_segments)}개 (겹침 없음 확인)")

    X_train, y_train = get_feature_target(train_df)
    X_test, y_test = get_feature_target(test_df)
    assert list(X_train.columns) == NUMERIC_FEATURES + CATEGORICAL_FEATURES

    for name, builder in [
        ("random_forest", lambda: build_random_forest(n_estimators=50, random_state=0)),
        ("xgboost", lambda: build_xgboost(y_train=y_train, n_estimators=50, random_state=0)),
    ]:
        print(f"\n--- {name} ---")
        model = builder()
        model.fit(X_train, y_train)

        proba = model.predict_proba(X_test)[:, 1]
        assert proba.shape == (len(X_test),)
        assert np.all((proba >= 0) & (proba <= 1))

        metrics = evaluate_classifier(model, X_test, y_test)
        print(f"지표(의미 없는 합성 데이터 기준): {metrics}")
        assert 0 <= metrics["pr_auc"] <= 1
        assert 0 <= metrics["roc_auc"] <= 1

        cm = confusion_matrix_report(model, X_test, y_test, threshold=metrics["threshold"])
        assert cm.shape == (2, 2)
        print(cm)

        shap_values, feature_names = compute_shap_values(model, X_test.head(20))
        assert shap_values.shape[0] == 20
        assert shap_values.shape[1] == len(feature_names)

        top_feats = top_feature_contributions(shap_values, feature_names, sample_index=0, top_n=3)
        assert len(top_feats) == 3
        print(f"샘플 0의 상위 기여 피처:\n{top_feats}")

        importance = global_feature_importance(shap_values, feature_names)
        assert len(importance) == len(feature_names)
        print(f"전역 변수 중요도 상위 5개:\n{importance.head()}")

    print("\n✓ 모든 구조 검증 통과 (RandomForest, XGBoost 모두 fit → predict → 평가 → SHAP 정상 동작)")
    print("  실제 데이터가 준비되면 python -m src.models.baseline.train 로 실행하세요.")


if __name__ == "__main__":
    main()
