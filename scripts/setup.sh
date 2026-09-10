#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# macOS / Linux 공통 셋업 스크립트
#   실행: bash scripts/setup.sh
# 하는 일: (1) Python 3.13 확인 (2) .venv 생성 (3) 의존성 설치 (4) .env 생성 (5) 검증
# ─────────────────────────────────────────────────────────────
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."  # 프로젝트 루트로 이동

REQUIRED_MINOR=12   # requirements.txt 핀 버전이 요구하는 최소 Python (3.12+)
PYTHON_BIN=""

echo "[1/5] Python 3.12+ 인터프리터 탐색 중..."
for candidate in python3.13 python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    ver=$("$candidate" -c 'import sys; print(sys.version_info[1])' 2>/dev/null || echo 0)
    major=$("$candidate" -c 'import sys; print(sys.version_info[0])' 2>/dev/null || echo 0)
    if [ "$major" = "3" ] && [ "$ver" -ge "$REQUIRED_MINOR" ]; then
      PYTHON_BIN="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "오류: Python 3.12 이상을 찾지 못했습니다." >&2
  echo "  macOS  : brew install python@3.13" >&2
  echo "  Ubuntu : sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.13 python3.13-venv" >&2
  echo "  또는   : pyenv install 3.13 && pyenv local 3.13   (pyenv가 있다면 .python-version 자동 인식)" >&2
  exit 1
fi
echo "      -> 사용: $PYTHON_BIN ($($PYTHON_BIN --version))"

echo "[2/5] 가상환경 생성 (.venv)..."
if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
else
  echo "      -> 이미 존재, 건너뜀"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if [[ "$(uname)" == "Darwin" ]]; then
  if command -v brew >/dev/null 2>&1 && ! brew list libomp >/dev/null 2>&1; then
    echo "[macOS] xgboost 실행에 필요한 libomp 설치 중..."
    brew install libomp
  fi
fi

echo "[3/5] 의존성 설치 (requirements.txt)..."
pip install --upgrade pip -q
if ! pip install -r requirements.txt; then
  echo "" >&2
  echo "경고: 일부 패키지 설치가 실패했습니다 (geopandas/rasterio/fiona는 GDAL 등" >&2
  echo "      네이티브 라이브러리가 필요합니다). 아래를 확인하세요:" >&2
  echo "  macOS  : brew install gdal geos proj" >&2
  echo "  Ubuntu : sudo apt install gdal-bin libgdal-dev libgeos-dev libproj-dev" >&2
  echo "  또는 conda 사용을 권장합니다:" >&2
  echo "    conda create -n roadkill python=3.13 geopandas rasterio -c conda-forge" >&2
  exit 1
fi

echo "[4/5] .env 파일 준비..."
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "      -> .env 생성 완료. ANTHROPIC_API_KEY 등 실제 값을 채워주세요."
else
  echo "      -> 이미 존재, 건너뜀"
fi

echo "[5/5] 설치 검증..."
if python -c "import pandas, geopandas, sklearn, xgboost, torch, torch_geometric, streamlit, anthropic, chromadb" 2>/tmp/roadkill_setup_check.log; then
  echo "      -> 핵심 의존성 정상 임포트 확인"
else
  echo "" >&2
  echo "경고: 일부 패키지가 설치는 됐지만 임포트에 실패했습니다:" >&2
  tail -5 /tmp/roadkill_setup_check.log >&2
  echo "" >&2
  echo "  xgboost dlopen 오류(libomp) -> macOS: brew install libomp" >&2
  echo "  그 외에는 위 오류 메시지를 참고해 개별 패키지를 재설치하세요." >&2
fi
rm -f /tmp/roadkill_setup_check.log

echo ""
echo "✓ 셋업 완료. 다음으로 가상환경을 활성화하세요:"
echo "    source .venv/bin/activate"
