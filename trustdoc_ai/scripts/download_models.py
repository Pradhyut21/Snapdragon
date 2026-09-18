"""Prepare model-cache folders, download verified ONNX Judge artifacts, and report AI Hub status."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

from trustdoc_ai.core.hardware_detect import detect_hardware


JUDGE_MODEL_REPO = "cross-encoder/nli-MiniLM2-L6-H768"
CACHE_ROOT = Path("trustdoc_ai/models/cache")
JUDGE_CACHE_DIR = CACHE_ROOT / "judge"


def download_judge_model() -> Path:
    """Download the quantized ONNX NLI model for the Adversarial Judge role."""
    from huggingface_hub import hf_hub_download

    JUDGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    hardware = detect_hardware()

    # Determine optimal quantized ONNX weight artifact for current architecture
    onnx_filename = (
        "onnx/model_qint8_arm64.onnx"
        if hardware.arch == "arm64"
        else "onnx/model_quint8_avx2.onnx"
    )

    files_to_fetch = [
        onnx_filename,
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
    ]

    print(f"[TrustDoc AI] Downloading Judge ONNX artifacts ({JUDGE_MODEL_REPO})...")
    for file_name in files_to_fetch:
        src = hf_hub_download(repo_id=JUDGE_MODEL_REPO, filename=file_name)
        dst = JUDGE_CACHE_DIR / Path(file_name).name
        if not dst.exists() or dst.stat().st_size == 0:
            shutil.copyfile(src, dst)
            print(f"  Fetched: {dst.name} ({dst.stat().st_size / (1024 * 1024):.1f} MB)")
        else:
            print(f"  Cached:  {dst.name}")

    # Ensure canonical model.onnx exists
    active_weight = JUDGE_CACHE_DIR / Path(onnx_filename).name
    canonical_model = JUDGE_CACHE_DIR / "model.onnx"
    if active_weight.exists() and (not canonical_model.exists() or canonical_model.stat().st_size == 0):
        shutil.copyfile(active_weight, canonical_model)
        print(f"  Active model linked: {canonical_model.name}")

    return JUDGE_CACHE_DIR


def main() -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    tokenizer_dir = CACHE_ROOT / "tokenizers"
    tokenizer_dir.mkdir(parents=True, exist_ok=True)

    has_qai_hub = importlib.util.find_spec("qai_hub") is not None
    has_qai_hub_models = importlib.util.find_spec("qai_hub_models") is not None

    print(f"Model cache: {CACHE_ROOT.resolve()}")
    print(f"qai_hub installed: {has_qai_hub}")
    print(f"qai_hub_models installed: {has_qai_hub_models}")

    try:
        judge_path = download_judge_model()
        print(f"[TrustDoc AI] Judge model ready at: {judge_path.resolve()}")
    except Exception as exc:
        print(f"[TrustDoc AI] Note: Could not download ONNX Judge artifacts ({exc}).")
        print("  The verifier will use local_rules_debate_v1 as an offline fallback.")


if __name__ == "__main__":
    main()

