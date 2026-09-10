# 진행 상황 (Project Status)

> 마지막 업데이트: 2026-09-10
>
> 이 문서는 프로젝트 전체 진행률을 한눈에 보기 위한 용도다. 결정의 **근거**는
> [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md)에, 세부 실행 방법은
> [`../README.md`](../README.md)에 있다. 작업이 진행될 때마다 아래 표의 상태와
> "마지막 업데이트" 날짜, 하단 활동 이력을 갱신한다.

## 한눈에 보기

| 단계 | 상태 | 비고 |
|---|:---:|---|
| 프로젝트 스캐폴딩 | ✅ 완료 | 폴더 구조, `requirements.txt`, `.gitignore` 등 |
| 환경 재현성 | ✅ 완료 | `scripts/setup.sh`(macOS/Linux) · `setup.ps1`(Windows), `.python-version` |
| 공공데이터 수집 | ⬜ 시작 전 | **현재 블로커** — 아래 참고 |
| 전처리 구현 | 🟡 설계만 완료 | 로더 5개 스켈레톤(`NotImplementedError`), 실제 구현은 데이터 수집 후 |
| EDA | ⬜ 시작 전 | 데이터 수집 후 진행 |
| 베이스라인 모델 (RF·XGBoost) | 🟡 코드 완료 / 실데이터 학습 전 | 합성 데이터로 구조 검증 완료, 실제 지표는 아직 없음 |
| GNN (GCN·GraphSAGE) | ⬜ 시작 전 | 베이스라인 실데이터 학습 이후 |
| RAG 파이프라인 | ⬜ 시작 전 | |
| LLM 정책 브리핑 | ⬜ 시작 전 | 베이스라인 SHAP 결과가 선행 필요 |
| RAG 챗봇 | ⬜ 시작 전 | |
| Streamlit 대시보드 | ⬜ 시작 전 | |
| 설계 결정 문서화 | 🔵 계속 진행 | [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md), 매 결정마다 갱신 |

범례: ✅ 완료 · 🟡 부분 완료 · 🔵 상시 진행 · ⬜ 시작 전

---

## 모듈별 상세 현황

### 1. 프로젝트 셋업 — ✅ 완료
- 폴더 구조(`data/`, `src/`, `notebooks/`, `reports/`, `models/`, `docs/`, `tests/`) 확정
- `requirements.txt` 버전 고정 (pandas 3.0.5, scikit-learn 1.9.0, xgboost 3.4.1, torch 2.14.0 등)
- `.env.example`, `.gitignore` 작성

### 2. 환경 재현성 — ✅ 완료
- `scripts/setup.sh`, `scripts/setup.ps1`: Python 3.12+ 탐색 → venv → 의존성 설치 → `.env` 생성 → 임포트 검증
- macOS에서 실제 실행해 `libomp` 미설치로 인한 xgboost 임포트 실패를 발견·수정함
- Windows 스크립트는 작성만 했고 실제 Windows 환경에서 실행 검증은 아직 안 함

### 3. 공공데이터 수집 — ⬜ 시작 전 (현재 블로커)
필요한 5개 출처 중 아무것도 다운로드되지 않은 상태 (`data/raw/`가 비어 있음):

| 데이터 | 출처 | 상태 |
|---|---|---|
| 로드킬 발생 지점 | TAAS, 국립생태원 에코뱅크 | ⬜ |
| 도로망(폭·곡률·제한속도·AADT) | 공공데이터포털 | ⬜ |
| 서식지·생태통로 | 국립생태원 에코뱅크 | ⬜ |
| 기상 | 기상청 날씨누리 | ⬜ |
| DEM(고도·경사) | 국가공간정보포털 | ⬜ |

**이게 끝나야 전처리 구현 → EDA → 베이스라인 실제 학습으로 이어질 수 있다.**

### 4. 전처리 — 🟡 설계만 완료
- `src/preprocessing/paths.py`: 경로·좌표계(EPSG:5179/4326)·구간 길이(500m) 상수 — 구현 완료
- 로더 5개(`load_roadkill.py`, `load_road_network.py`, `load_habitat.py`, `load_weather.py`, `load_terrain.py`): 함수 시그니처·타입힌트·docstring만 있고 본문은 `NotImplementedError` (21개 함수)
- 실제 원본 데이터의 컬럼 스키마를 아직 못 봤기 때문에, 구현 시점에 `src/models/baseline/schema.py`의 컬럼명도 같이 재검토해야 함 (`DESIGN_DECISIONS.md` §2 참고)

### 5. 베이스라인 모델 — 🟡 코드 완료 / 실데이터 학습 전
- `schema.py`, `dataset.py`, `pipeline.py`, `models.py`, `evaluate.py`, `interpret.py`, `train.py` 7개 모듈 구현 완료
- `tests/test_baseline_pipeline.py`의 합성 데이터로 전체 흐름(로딩 → spatial/temporal split → 전처리 → RF/XGBoost 학습 → PR-AUC 평가 → SHAP) 실제 실행·검증 완료
- `spatial_split`을 `StratifiedGroupKFold` 기반으로 수정해, 희귀 이벤트 평가 세트에 양성이 0개가 되는 버그를 고침
- **실제 데이터로 학습한 적은 없음** — 지금 나온 지표는 전부 의미 없는 합성 데이터 기준

### 6~10. GNN / RAG / LLM 브리핑 / 챗봇 / 대시보드 — ⬜ 시작 전
아직 폴더와 `__init__.py`만 있고 구현 착수 전.

---

## 다음 액션 (우선순위 순)

1. **공공데이터 5종 수집** — API 키 발급, 원본 파일 `data/raw/`에 배치
2. **전처리 구현** — 실제 데이터 스키마를 보고 로더 5개 채우기, `schema.py` 컬럼명 재검토
3. **EDA** — 위험도 분포, 결측치, 클래스 불균형 정도 확인 (Q1: 구간-일자 vs 카운트 회귀 결정에 필요, `DESIGN_DECISIONS.md` 참고)
4. **베이스라인 실제 학습** — `python -m src.models.baseline.train` 실행, 실제 PR-AUC 확인
5. GNN 착수

## 최근 활동 (git log)

| 날짜 | 커밋 | 내용 |
|---|---|---|
| 2026-09-10 | `29df647` | 베이스라인 모델 파이프라인, `DESIGN_DECISIONS.md` 추가 |
| 2026-09-10 | `ca6b844` | 프로젝트 초기 스캐폴딩 |
