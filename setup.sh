#!/usr/bin/env bash
set -euo pipefail

echo "TrustDoc AI targets Windows ARM64/x64. This shell wrapper is provided for repository completeness."
echo "Use setup.ps1 on Windows. Running setup.py on non-Windows hosts exits before installing dependencies."

python setup.py "$@"
