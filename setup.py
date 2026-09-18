"""
TrustDoc AI — hardware-detection installer
==========================================

Usage:
    python setup.py                     # Install all dependencies for detected hardware
    python setup.py --download-models   # Install deps + download AI Hub models

Requirements satisfied: 12.3, 17.5

Behaviour by platform / architecture:
  Windows ARM64 (Snapdragon) → installs onnxruntime-qnn==1.19.0
  Windows AMD64 (x64)        → installs onnxruntime==1.19.0  [warns: QNN_EP unavailable]
  Any other OS               → exits with a clear error message; does NOT partially install
"""

import argparse
import platform
import subprocess
import sys
import warnings


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ONNXRUNTIME_QNN_VERSION = "onnxruntime-qnn==1.19.0"
ONNXRUNTIME_CPU_VERSION = "onnxruntime==1.19.0"
REQUIREMENTS_FILE = "requirements.txt"


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _pip_install(*packages: str) -> None:
    """Install one or more packages using the current Python interpreter's pip."""
    cmd = [sys.executable, "-m", "pip", "install"] + list(packages)
    print(f"\n[setup] Running: {' '.join(cmd)}\n")
    subprocess.check_call(cmd)


def _pip_install_requirements(req_file: str) -> None:
    """Install all packages listed in a requirements file."""
    cmd = [sys.executable, "-m", "pip", "install", "-r", req_file]
    print(f"\n[setup] Running: {' '.join(cmd)}\n")
    subprocess.check_call(cmd)


# ---------------------------------------------------------------------------
# OS / architecture guards
# ---------------------------------------------------------------------------

def _check_platform() -> str:
    """
    Verify the host OS is Windows and return the machine architecture string.

    Returns:
        "ARM64" or "AMD64"

    Side-effects:
        Calls sys.exit(1) with an informative message if the OS is not Windows.
    """
    os_name = platform.system()
    if os_name != "Windows":
        print(
            "\n[setup] ERROR: TrustDoc AI requires Windows on Snapdragon (ARM64) or "
            "Windows x64.\n"
            f"       Detected OS: {os_name}\n"
            "\n"
            "       This application depends on Windows-specific QNN/ONNX Runtime "
            "components\n"
            "       and PySide6 packaging that are not available on non-Windows "
            "platforms.\n"
            "       Installation aborted — no packages have been installed.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    arch = platform.machine().upper()  # "ARM64" or "AMD64" on Windows
    return arch


# ---------------------------------------------------------------------------
# ORT variant selection
# ---------------------------------------------------------------------------

def _install_onnxruntime(arch: str) -> None:
    """
    Install the correct ONNX Runtime flavour for the detected architecture.

    ARM64 → onnxruntime-qnn (Qualcomm QNN Execution Provider included)
    AMD64 → onnxruntime (CPU-only; QNN_EP is unavailable on x64 Windows)
    Other → exit with error; unsupported architecture
    """
    if arch == "ARM64":
        print(
            f"\n[setup] Detected Windows on ARM64 (Snapdragon).\n"
            f"        Installing {ONNXRUNTIME_QNN_VERSION} — QNN_EP enabled.\n"
        )
        _pip_install(ONNXRUNTIME_QNN_VERSION)

    elif arch == "AMD64":
        warnings.warn(
            "\n[setup] WARNING: Running on Windows x64 (AMD64).\n"
            "        QNN Execution Provider (NPU acceleration) is NOT available on this "
            "platform.\n"
            "        All model inference will run on CPU. For NPU acceleration, use a\n"
            "        Snapdragon X Elite / X Plus device running Windows on ARM64.\n",
            stacklevel=2,
        )
        print(
            f"\n[setup] Installing {ONNXRUNTIME_CPU_VERSION} (CPU-only).\n"
        )
        _pip_install(ONNXRUNTIME_CPU_VERSION)

    else:
        print(
            f"\n[setup] ERROR: Unsupported CPU architecture: {arch}\n"
            "        TrustDoc AI supports Windows ARM64 (Snapdragon) and Windows AMD64 "
            "(x64) only.\n"
            "        Installation aborted — no packages have been installed.\n",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Common dependencies
# ---------------------------------------------------------------------------

def _install_common_deps() -> None:
    """Install all common dependencies from requirements.txt."""
    print(f"\n[setup] Installing common dependencies from {REQUIREMENTS_FILE} ...\n")
    try:
        _pip_install_requirements(REQUIREMENTS_FILE)
    except subprocess.CalledProcessError as exc:
        print(
            f"\n[setup] ERROR: Failed to install dependencies from {REQUIREMENTS_FILE}.\n"
            f"        pip exited with code {exc.returncode}.\n"
            "        Please check the requirements file and your network connection.\n",
            file=sys.stderr,
        )
        sys.exit(exc.returncode)


# ---------------------------------------------------------------------------
# Model download
# ---------------------------------------------------------------------------

def _download_models() -> None:
    """
    Delegate to scripts/download_models.py to pull AI Hub model artefacts.

    The actual implementation lives in Task 3.2. This call is a placeholder
    that wires the --download-models flag to the correct script location so
    that the interface is established now and the implementation can be
    dropped in without changing setup.py.
    """
    print("\n[setup] Downloading AI Hub models via scripts/download_models.py ...\n")
    try:
        subprocess.check_call(
            [sys.executable, "trustdoc_ai/scripts/download_models.py"]
        )
    except subprocess.CalledProcessError as exc:
        print(
            "\n[setup] ERROR: Model download script exited with an error "
            f"(code {exc.returncode}).\n"
            "        Check trustdoc_ai/scripts/download_models.py for details.\n",
            file=sys.stderr,
        )
        sys.exit(exc.returncode)
    except FileNotFoundError:
        print(
            "\n[setup] ERROR: trustdoc_ai/scripts/download_models.py not found.\n"
            "        This script will be implemented in Task 3.2. Run setup.py "
            "again once that task is complete.\n",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TrustDoc AI hardware-detection installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--download-models",
        action="store_true",
        default=False,
        help=(
            "After installing Python dependencies, invoke "
            "trustdoc_ai/scripts/download_models.py to download and cache "
            "the required AI Hub model artefacts."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()

    print("\n=== TrustDoc AI Setup ===\n")
    print(f"Python  : {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Machine : {platform.machine()}\n")

    # 1. Verify OS — exit immediately if not Windows (do NOT partially install)
    arch = _check_platform()

    # 2. Install the correct onnxruntime variant for this architecture
    _install_onnxruntime(arch)

    # 3. Install all other common dependencies from requirements.txt
    _install_common_deps()

    print("\n[setup] Core installation complete.\n")

    # 4. Optionally download AI Hub models
    if args.download_models:
        _download_models()
        print("\n[setup] Model download complete.\n")

    print("[setup] Setup finished successfully.\n")


if __name__ == "__main__":
    main()
