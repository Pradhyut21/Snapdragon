"""Benchmark the currently implemented local demo pipeline."""

from __future__ import annotations

import json
import time
from pathlib import Path

from trustdoc_ai.demo.run_demo import main as run_demo


def main() -> None:
    started = time.perf_counter()
    run_demo()
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    output = {
        "benchmark_type": "locally measured CPU/local-rules demo",
        "elapsed_ms": elapsed_ms,
        "note": "This is not an NPU benchmark and does not measure ONNX LLM inference.",
    }
    path = Path("trustdoc_ai/benchmarks/latest_local_demo.json")
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nBenchmark written to {path.resolve()}")


if __name__ == "__main__":
    main()
