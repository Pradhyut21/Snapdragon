param(
    [switch]$DownloadModels
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath ".venv")) {
    py -3.11 -m venv .venv
}

& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip

if ($DownloadModels) {
    python setup.py --download-models
} else {
    python setup.py
}

python -m pytest tests
