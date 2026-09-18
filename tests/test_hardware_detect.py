import platform
from types import SimpleNamespace

import trustdoc_ai.core.hardware_detect as hardware_detect


def test_normalise_arch_maps_windows_values():
    assert hardware_detect._normalise_arch("ARM64") == "arm64"
    assert hardware_detect._normalise_arch("AMD64") == "x64"
    assert hardware_detect._normalise_arch("x86_64") == "x64"
    assert hardware_detect._normalise_arch("mips") == "unknown"


def test_detect_hardware_requires_provider_and_dll(monkeypatch, tmp_path):
    dll = tmp_path / "QnnHtp.dll"
    dll.write_text("fake test dll")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(platform, "machine", lambda: "ARM64")
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        hardware_detect,
        "_probe_qnn_ep",
        lambda: (True, "1.19.0"),
    )

    profile = hardware_detect.detect_hardware()

    assert profile.arch == "arm64"
    assert profile.platform == "Windows"
    assert profile.ort_version == "1.19.0"
    assert profile.qnn_ep_available is True
    assert profile.qnn_htp_dll_path == str(dll)


def test_detect_hardware_reports_cpu_fallback_when_dll_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        hardware_detect,
        "_probe_qnn_ep",
        lambda: (True, "1.19.0"),
    )

    profile = hardware_detect.detect_hardware()

    assert profile.arch == "x64"
    assert profile.qnn_ep_available is False
    assert profile.qnn_htp_dll_path is None
