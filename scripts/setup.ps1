# ─────────────────────────────────────────────────────────────
# Windows 셋업 스크립트
#   실행: powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
# 하는 일: (1) Python 3.12+ 확인 (2) .venv 생성 (3) 의존성 설치 (4) .env 생성
# ─────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)  # 프로젝트 루트로 이동

$RequiredMinor = 12
$PythonBin = $null

Write-Host "[1/4] Python 3.12+ 인터프리터 탐색 중..."
foreach ($candidate in @("py -3.13", "py -3.12", "python", "python3")) {
    $exe, $arg = $candidate.Split(" ", 2)
    $cmd = Get-Command $exe -ErrorAction SilentlyContinue
    if ($cmd) {
        try {
            if ($arg) {
                $verOutput = & $exe $arg -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
            } else {
                $verOutput = & $exe -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
            }
            if ($verOutput) {
                $major, $minor = $verOutput.Split(".")
                if ([int]$major -eq 3 -and [int]$minor -ge $RequiredMinor) {
                    $PythonBin = $candidate
                    break
                }
            }
        } catch {}
    }
}

if (-not $PythonBin) {
    Write-Host "오류: Python 3.12 이상을 찾지 못했습니다." -ForegroundColor Red
    Write-Host "  winget install Python.Python.3.13" -ForegroundColor Yellow
    Write-Host "  또는 https://www.python.org/downloads/ 에서 3.13 설치" -ForegroundColor Yellow
    exit 1
}
Write-Host "      -> 사용: $PythonBin"

Write-Host "[2/4] 가상환경 생성 (.venv)..."
if (-not (Test-Path ".venv")) {
    $exe, $arg = $PythonBin.Split(" ", 2)
    if ($arg) { & $exe $arg -m venv .venv } else { & $exe -m venv .venv }
} else {
    Write-Host "      -> 이미 존재, 건너뜀"
}

& .\.venv\Scripts\Activate.ps1

Write-Host "[3/4] 의존성 설치 (requirements.txt)..."
python -m pip install --upgrade pip -q
try {
    pip install -r requirements.txt
} catch {
    Write-Host ""
    Write-Host "경고: 일부 패키지 설치가 실패했습니다 (geopandas/rasterio/fiona는 GDAL 등" -ForegroundColor Yellow
    Write-Host "      네이티브 라이브러리가 필요합니다). conda 사용을 권장합니다:" -ForegroundColor Yellow
    Write-Host "    conda create -n roadkill python=3.13 geopandas rasterio -c conda-forge" -ForegroundColor Yellow
    exit 1
}

Write-Host "[4/5] .env 파일 준비..."
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "      -> .env 생성 완료. ANTHROPIC_API_KEY 등 실제 값을 채워주세요."
} else {
    Write-Host "      -> 이미 존재, 건너뜀"
}

Write-Host "[5/5] 설치 검증..."
$checkResult = python -c "import pandas, geopandas, sklearn, xgboost, torch, torch_geometric, streamlit, anthropic, chromadb" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "      -> 핵심 의존성 정상 임포트 확인"
} else {
    Write-Host ""
    Write-Host "경고: 일부 패키지가 설치는 됐지만 임포트에 실패했습니다:" -ForegroundColor Yellow
    Write-Host $checkResult -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✓ 셋업 완료. 다음으로 가상환경을 활성화하세요:" -ForegroundColor Green
Write-Host "    .\.venv\Scripts\Activate.ps1"
