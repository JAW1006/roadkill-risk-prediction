# 로드킬 위험구간 예측 (Roadkill Risk Prediction)

공공데이터를 활용해 **도로 구간별 야생동물 찻길사고(로드킬) 위험도**를 예측하고,
대화형 GIS 대시보드와 LLM 정책 브리핑·챗봇으로 제공하는 3개월 캡스톤 프로젝트.

## 목표

1. 도로를 일정 길이 구간으로 나누고, 구간별 로드킬 위험도를 예측한다.
2. 위험구간을 지도 위에서 탐색할 수 있는 Streamlit 대시보드를 만든다.
3. 담당자가 위험구간을 선택하면 **자연어 정책 브리핑**을 자동 생성하고,
   **RAG 챗봇**으로 자연어 질의응답을 지원한다.

### 범위

| 포함 | 제외 (향후 확장) |
|---|---|
| 공공데이터 기반 위험도 예측 | CCTV 실시간 객체 탐지 |
| 정적 위험지도 + 기상 조건별 위험도 | 실시간 알림/신호 연동 |
| 정책 브리핑 + RAG 챗봇 | 현장 IoT 센서 연계 |

> CCTV 실시간 탐지는 이번 과제 범위가 아니다. 예측된 위험구간을 우선순위로
> 카메라를 배치하는 후속 단계로만 문서에 남긴다.

> **설계 결정의 근거**(왜 이렇게 만들었는지, 뭐가 확정이고 뭐가 아직 검증
> 필요한지)는 이 README가 아니라 [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md)
> 에 계속 누적해서 기록한다. 새로운 결정을 내리거나 기존 결정을 재검토할 때마다
> 그 문서를 갱신한다.

## 접근 방법

### 1단계 — 데이터 파이프라인
도로망을 500m 구간으로 분할해 예측 단위(= GNN의 노드)를 만들고,
로드킬 지점·서식지·기상·지형 데이터를 이 구간에 공간 조인한다.

### 2단계 — 베이스라인 모델
`scikit-learn` RandomForest → `XGBoost`. 로드킬은 희소 이벤트이므로 두 가지를
설계 기준으로 삼았다:

- **불균형 처리**: 오버샘플링(SMOTE 등) 대신 클래스 가중치
  (`class_weight="balanced_subsample"` / `scale_pos_weight`)를 사용한다.
  CV 폴드마다 학습 데이터로만 다시 계산해야 하는 오버샘플링과 달리 누수
  위험이 없고 구현이 단순하다. `imbalanced-learn`은 의존성으로 남겨뒀지만
  기본 경로에서는 쓰지 않는다.
- **평가**: 음성이 압도적으로 많으면 ROC-AUC가 낙관적으로 나오므로
  PR-AUC(average precision)를 주 지표로 삼고, 분류 임계값도 고정 0.5가
  아니라 F1을 최대화하는 지점을 탐색해서 쓴다 (`evaluate.py`).
- **분할 전략**: 같은 구간의 서로 다른 날짜가 학습·평가에 동시에 들어가면
  공간적 정보 누수가 생기므로, 기본값은 구간(`segment_id`) 단위로 통째로
  나누는 spatial split이다. "미래 시점 예측력"을 보고 싶을 때는
  `--split temporal --cutoff-date` 로 날짜 기준 분할도 가능하다.

SHAP(`interpret.py`)으로 뽑은 변수 기여도는 4단계 정책 브리핑의 근거 자료로
그대로 재사용한다.

> 구현은 끝났지만 아직 실제 데이터가 없어 실행은 못 해봤다. 대신
> `tests/test_baseline_pipeline.py` 의 합성 데이터로 전체 흐름(로딩 → 분할 →
> 전처리 → 학습 → 평가 → SHAP)이 에러 없이 도는 것만 확인한 상태다 —
> 지표 수치 자체는 의미가 없다.

### 3단계 — GNN 고도화
베이스라인은 각 구간을 독립 샘플로 보지만, 실제 로드킬은 인접 구간으로
이어지는 공간적 자기상관을 갖는다. 구간 인접 그래프 위에서 GCN/GraphSAGE를
학습해 이웃 정보를 반영하고, 베이스라인 대비 성능 향상을 검증한다.

### 4단계 — LLM 활용
- **정책 브리핑**: 위험구간 선택 → 예측 위험도 + SHAP 기여 변수 + 주변
  서식지/생태통로 현황을 Claude에 전달 → 담당자용 자연어 브리핑 생성
- **RAG 챗봇**: 구간별 위험 정보를 문서화해 임베딩(`sentence-transformers`,
  로컬 무료) → ChromaDB 저장 → 질의 시 관련 구간을 검색해 Claude가 답변

## 데이터 출처

| 데이터 | 출처 | 용도 |
|---|---|---|
| 로드킬 발생 지점 | TAAS(도로교통공단), 국립생태원 에코뱅크 | 타깃 변수 |
| 서식지·생태통로 현황 | 국립생태원 에코뱅크 | 생태 피처 |
| 도로망(폭·곡률·제한속도·AADT) | 공공데이터포털 GIS | 도로 피처 |
| 기상 (강수·안개·기온) | 기상청 날씨누리 | 시간 피처 |
| 지형 (고도·경사) | 국가공간정보포털 DEM | 지형 피처 |

> 원본 데이터는 `data/raw/` 에 두며 **저장소에 커밋하지 않는다**(`.gitignore`).
> QGIS는 좌표계 변환·시각적 검수 등 로컬 전처리에 별도로 사용하며,
> 코드에서 직접 연동하지 않는다.

## 폴더 구조

```
roadkill-risk-prediction/
├── data/
│   ├── raw/                  # 원본 공공데이터 (커밋 제외)
│   └── processed/            # 전처리 완료 분석용 데이터 (커밋 제외)
├── notebooks/                # 탐색적 데이터 분석(EDA)
├── src/
│   ├── preprocessing/        # 데이터 로딩 · 공간 조인 · 피처 생성
│   │   ├── paths.py          #   경로 및 좌표계 상수
│   │   ├── load_roadkill.py  #   TAAS · 에코뱅크 로드킬 지점
│   │   ├── load_road_network.py  # 도로망 · 구간 분할 · 인접 그래프
│   │   ├── load_habitat.py   #   서식지 · 생태통로 · 토지피복
│   │   ├── load_weather.py   #   기상청 관측 자료
│   │   └── load_terrain.py   #   DEM 고도 · 경사
│   ├── models/
│   │   ├── baseline/         # RandomForest, XGBoost
│   │   │   ├── schema.py     #   모델 테이블 컬럼 정의
│   │   │   ├── dataset.py    #   로딩 · 계절 피처 · spatial/temporal split
│   │   │   ├── pipeline.py   #   공통 전처리 (결측치 · 원-핫 인코딩)
│   │   │   ├── models.py     #   RF/XGBoost 파이프라인 생성
│   │   │   ├── evaluate.py   #   PR-AUC 중심 평가 지표
│   │   │   ├── interpret.py  #   SHAP 변수 기여도 (정책 브리핑 재사용)
│   │   │   └── train.py      #   학습 CLI 진입점
│   │   └── gnn/              # GCN, GraphSAGE (PyTorch Geometric)
│   ├── rag/                  # 임베딩, ChromaDB 구축, 검색
│   ├── llm/                  # 정책 브리핑 생성, 챗봇 응답
│   └── dashboard/            # Streamlit 대시보드
├── tests/
│   └── test_baseline_pipeline.py  # 합성 데이터로 베이스라인 파이프라인 구조 검증
├── models/baseline/          # 학습된 모델 아티팩트 (.joblib, 커밋 제외)
├── reports/figures/          # 결과 그림 (커밋 제외)
├── docs/
│   ├── PROGRESS.md           # 진행 상황 한눈에 보기 (계속 업데이트)
│   └── DESIGN_DECISIONS.md   # 설계 결정 근거 기록 (계속 업데이트)
├── scripts/
│   ├── setup.sh              # macOS/Linux 자동 셋업
│   └── setup.ps1             # Windows 자동 셋업
├── requirements.txt
├── .python-version           # pyenv/asdf용 Python 버전 고정 (3.13)
├── .env.example
└── README.md
```

## 기술 스택

| 영역 | 사용 도구 |
|---|---|
| 데이터 처리 | pandas, geopandas, shapely, rasterio |
| 베이스라인 | scikit-learn (RandomForest), xgboost, imbalanced-learn, shap |
| GNN | PyTorch, PyTorch Geometric (GCN / GraphSAGE) |
| LLM | Anthropic Claude API — `claude-haiku-4-5` |
| RAG | sentence-transformers (로컬 임베딩), ChromaDB |
| 대시보드 | Streamlit + folium / pydeck |
| 전처리 보조 | QGIS (로컬 수작업, 코드 연동 없음) |

## 설치 및 실행

### 요구 사항
**Python 3.12 이상** (핀 고정된 pandas·xgboost·numpy가 3.12+ 요구). 팀원마다
시스템 Python 버전이 다를 수 있으므로, 아래 자동 셋업 스크립트가 3.12+
인터프리터를 직접 탐색해 가상환경을 만든다. `.python-version` 파일이 있어
[pyenv](https://github.com/pyenv/pyenv)/[asdf](https://asdf-vm.com/) 사용자는
`pyenv install 3.13 && pyenv local 3.13` 만으로 버전을 맞출 수 있다.

### 1. 저장소 클론 및 자동 셋업

**macOS / Linux**

```bash
git clone <repo-url> roadkill-risk-prediction
cd roadkill-risk-prediction
bash scripts/setup.sh
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
git clone <repo-url> roadkill-risk-prediction
cd roadkill-risk-prediction
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
.\.venv\Scripts\Activate.ps1
```

`scripts/setup.sh` / `scripts/setup.ps1` 이 하는 일은 동일하다:

1. Python 3.12+ 인터프리터 탐색 (없으면 OS별 설치 명령 안내 후 종료)
2. `.venv` 가상환경 생성
3. `pip install -r requirements.txt`
4. `.env.example` → `.env` 복사 (이미 있으면 건너뜀)

셋업 스크립트 없이 수동으로 하려면:

```bash
python3.13 -m venv .venv         # Windows: py -3.13 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
```

> **GDAL/GEOS 네이티브 라이브러리 문제 (geopandas·rasterio·fiona)**
> pip 설치가 실패하면 OS에 네이티브 라이브러리가 없는 경우다.
> - macOS: `brew install gdal geos proj`
> - Ubuntu/Debian: `sudo apt install gdal-bin libgdal-dev libgeos-dev libproj-dev`
> - Windows 또는 위 방법으로도 안 될 때: conda가 가장 안정적이다.
>   ```bash
>   conda create -n roadkill python=3.13 geopandas rasterio -c conda-forge
>   conda activate roadkill
>   pip install -r requirements.txt   # geopandas/rasterio는 이미 설치됐으므로 나머지만 설치됨
>   ```
>
> **macOS: xgboost가 `libomp.dylib` 를 찾지 못하는 오류**
> pip whl은 OpenMP 런타임을 포함하지 않는다. `scripts/setup.sh` 가 자동으로
> `brew install libomp` 를 실행하지만, 수동 설치 시에는 직접 실행해야 한다:
> ```bash
> brew install libomp
> ```

### 2. 환경변수 설정

셋업 스크립트가 `.env` 를 자동 생성한다. 아직 없다면:

```bash
cp .env.example .env
```

`.env` 를 열어 `ANTHROPIC_API_KEY` 등 실제 값을 채운다. 이 파일은
`.gitignore` 에 등록되어 있어 커밋되지 않는다.

### 3. 데이터 배치

각 기관에서 내려받은 원본 파일을 `data/raw/` 에 둔다. (아직 수집 전)

### 4. 설치 확인

```bash
python -c "import pandas, geopandas, sklearn, xgboost, torch, torch_geometric, streamlit, anthropic, chromadb; print('OK')"
```

`OK` 가 출력되면 모든 핵심 의존성이 정상 설치된 것이다.

### 5. 실행

```bash
# 전처리 — 구간 생성 및 피처 결합 (구현 예정)
python -m src.preprocessing

# 베이스라인 파이프라인 구조 검증 (합성 데이터, 실제 데이터 없이도 지금 실행 가능)
python tests/test_baseline_pipeline.py

# 베이스라인 학습 (data/processed/model_table.parquet 준비 후)
python -m src.models.baseline.train
python -m src.models.baseline.train --split temporal --cutoff-date 2025-06-01

# GNN 학습
python -m src.models.gnn.train

# RAG 벡터 저장소 구축
python -m src.rag.build_index

# 대시보드 실행
streamlit run src/dashboard/app.py
```

## 진행 상황

> 모듈별 상세 현황·블로커·다음 액션은 [`docs/PROGRESS.md`](docs/PROGRESS.md)에서
> 한눈에 볼 수 있다. 아래는 요약 체크리스트.

- [x] 프로젝트 스캐폴딩, 의존성 정의
- [x] 전처리 모듈 인터페이스 설계 (스켈레톤)
- [x] 환경 재현성 확보 — 자동 셋업 스크립트, `.python-version`
- [x] 베이스라인 파이프라인 구현 — RandomForest, XGBoost, PR-AUC 평가, SHAP 해석
      (합성 데이터로 구조 검증 완료, 실제 데이터 학습은 전처리 완료 후)
- [ ] 공공데이터 수집 및 `data/raw/` 배치
- [ ] 전처리 구현 — 구간 분할 및 피처 결합
- [ ] EDA
- [ ] 베이스라인 실제 데이터 학습 및 성능 확인
- [ ] GNN (GCN / GraphSAGE)
- [ ] RAG 파이프라인
- [ ] 정책 브리핑 생성
- [ ] Streamlit 대시보드

## 향후 확장 (이번 범위 외)

- CCTV 영상 기반 실시간 야생동물 탐지 및 운전자 경고
- 예측 위험구간 기반 생태통로/유도울타리 설치 우선순위 최적화
- 계절·시간대별 동적 위험도 예보
