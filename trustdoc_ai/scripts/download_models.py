"""Prepare model-cache folders and report AI Hub setup status.

This script is intentionally conservative. It does not invent model names or
download unverified artifacts. Once final AI Hub model choices are selected,
wire the concrete fetch/export commands here.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def main() -> None:
    cache_dir = Path("trustdoc_ai/models/cache")
    tokenizer_dir = cache_dir / "tokenizers"
    tokenizer_dir.mkdir(parents=True, exist_ok=True)

    has_qai_hub = importlib.util.find_spec("qai_hub") is not None
    has_qai_hub_models = importlib.util.find_spec("qai_hub_models") is not None

    print(f"Model cache: {cache_dir.resolve()}")
    print(f"qai_hub installed: {has_qai_hub}")
    print(f"qai_hub_models installed: {has_qai_hub_models}")
    print(
        "No model artifacts were downloaded. Add verified Qualcomm AI Hub model "
        "fetch/export calls here before claiming NPU LLM execution."
    )


if __name__ == "__main__":
    main()
