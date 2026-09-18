"""
core/hardware_detect.py

Hardware detection for TrustDoc AI.
Detects CPU architecture, QNN Execution Provider availability, and the
path to QnnHtp.dll.  Results are cached in a module-level singleton so
detection runs at most once per process.

Requirements: 11.1, 12.1, 12.2
"""

from __future__ import annotations

import glob
import os
import platform
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class HardwareProfile:
    """Snapshot of the host hardware relevant to model execution."""

    arch: str
    """Normalised CPU architecture: "arm64" | "x64" | "unknown"."""

    qnn_ep_available: bool
    """True only when QNNExecutionProvider is registered *and* QnnHtp.dll is
    found on disk.  Both conditions must hold."""

    qnn_htp_dll_path: str | None
    """Absolute path to the first QnnHtp.dll found, or None."""

    ort_version: str
    """onnxruntime version string, or "not_installed" if the package is absent."""

    platform: str
    """OS platform — always "Windows" on a supported host."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise_arch(machine: str) -> str:
    """Map platform.machine() strings to canonical arch values."""
    m = machine.upper()
    if m == "ARM64":
        return "arm64"
    if m in ("AMD64", "X86_64"):
        return "x64"
    return "unknown"


def _find_qnn_htp_dll() -> str | None:
    """
    Search for QnnHtp.dll in the following locations (in order):

    1. %PROGRAMFILES%\\Qualcomm\\AIStack\\QNN\\*\\lib\\aarch64-windows-msvc\\
    2. %PROGRAMFILES%\\Qualcomm\\AIStack\\SNPE\\*\\lib\\aarch64-windows-msvc\\
    3. Current working directory (portable / developer installs)
    4. Any directory listed in the PATH environment variable

    Returns the absolute path to the first match, or None.
    """
    search_patterns: list[str] = []

    prog_files = os.environ.get("PROGRAMFILES", r"C:\Program Files")

    # Pattern 1 – QNN SDK
    search_patterns.append(
        os.path.join(
            prog_files,
            "Qualcomm", "AIStack", "QNN", "*",
            "lib", "aarch64-windows-msvc", "QnnHtp.dll",
        )
    )

    # Pattern 2 – SNPE SDK
    search_patterns.append(
        os.path.join(
            prog_files,
            "Qualcomm", "AIStack", "SNPE", "*",
            "lib", "aarch64-windows-msvc", "QnnHtp.dll",
        )
    )

    # Pattern 3 – current working directory (portable distribution)
    search_patterns.append(os.path.join(os.getcwd(), "QnnHtp.dll"))

    # Check all glob/exact patterns first
    for pattern in search_patterns:
        matches = glob.glob(pattern)
        if matches:
            return os.path.abspath(matches[0])

    # Pattern 4 – any directory in PATH
    path_env = os.environ.get("PATH", "")
    for directory in path_env.split(os.pathsep):
        if not directory:
            continue
        candidate = os.path.join(directory, "QnnHtp.dll")
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)

    return None


def _probe_qnn_ep() -> tuple[bool, str]:
    """
    Probe onnxruntime for QNNExecutionProvider availability.

    Returns
    -------
    (ep_registered, ort_version)
        ep_registered – True if QNNExecutionProvider is in the provider list.
        ort_version   – Version string, or "unavailable" if ort is not installed.
    """
    try:
        import onnxruntime as ort  # noqa: PLC0415
        return "QNNExecutionProvider" in ort.get_available_providers(), ort.__version__
    except ImportError:
        return False, "not_installed"


# ---------------------------------------------------------------------------
# Core detection function
# ---------------------------------------------------------------------------

def detect_hardware() -> HardwareProfile:
    """
    Run hardware detection and return a :class:`HardwareProfile`.

    Steps
    -----
    1. Read ``platform.machine()`` to determine CPU arch.
    2. Probe ``ort.get_available_providers()`` for QNNExecutionProvider.
    3. Search for ``QnnHtp.dll`` in known Qualcomm SDK locations, cwd, and PATH.
    4. Combine results: ``qnn_ep_available`` requires *both* EP registration
       and the DLL being found on disk.
    5. Log the profile via Python logging at INFO level.
    """
    arch = _normalise_arch(platform.machine())
    os_name = platform.system()   # "Windows", "Linux", …

    # Probe ORT — handles ImportError gracefully
    ep_registered, ort_version = _probe_qnn_ep()

    # DLL search is fast; run it unconditionally so we can report the path
    # even on machines where the EP hasn't registered yet.
    dll_path = _find_qnn_htp_dll()

    # Both conditions required — EP registration alone is not enough if the
    # backend DLL is missing, and vice versa.
    qnn_ep_available = ep_registered and (dll_path is not None)

    profile = HardwareProfile(
        arch=arch,
        qnn_ep_available=qnn_ep_available,
        qnn_htp_dll_path=dll_path,
        ort_version=ort_version,
        platform=os_name,
    )

    # Use print rather than the logging module — the full EP logger depends on
    # the SQLite DB which is not yet initialised at this point in startup.
    print(
        f"[TrustDoc AI] Hardware detected: "
        f"arch={profile.arch!r} "
        f"platform={profile.platform!r} "
        f"ort_version={profile.ort_version!r} "
        f"qnn_ep_available={profile.qnn_ep_available} "
        f"qnn_htp_dll_path={profile.qnn_htp_dll_path!r}"
    )

    return profile


# ---------------------------------------------------------------------------
# Module-level lazy singleton
# ---------------------------------------------------------------------------

_hardware_profile: HardwareProfile | None = None


def get_hardware_profile() -> HardwareProfile:
    """
    Return the cached :class:`HardwareProfile`, running detection on the
    first call and caching the result for all subsequent calls.

    Detection does NOT run at module import time — only on the first call
    to this function.
    """
    global _hardware_profile  # noqa: PLW0603
    if _hardware_profile is None:
        _hardware_profile = detect_hardware()
    return _hardware_profile


# ---------------------------------------------------------------------------
# Manual test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    profile = detect_hardware()
    print("\n=== TrustDoc AI Hardware Profile ===")
    print(f"  arch             : {profile.arch}")
    print(f"  platform         : {profile.platform}")
    print(f"  ort_version      : {profile.ort_version}")
    print(f"  qnn_ep_available : {profile.qnn_ep_available}")
    print(f"  qnn_htp_dll_path : {profile.qnn_htp_dll_path}")
    print("=====================================\n")
