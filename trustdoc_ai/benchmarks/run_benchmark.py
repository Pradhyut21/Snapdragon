"""Benchmark the TrustDoc AI pipeline with real on-device ONNX Judge inference."""

from __future__ import annotations

import json
import time
from pathlib import Path

from trustdoc_ai.demo.run_demo import main as run_demo
from trustdoc_ai.db.audit_db import AuditDB


def main() -> None:
    started = time.perf_counter()
    run_demo()
    total_elapsed_ms = round((time.perf_counter() - started) * 1000, 3)

    db = AuditDB()
    db.connect("trustdoc_ai/demo/trustdoc_demo.db")
    recent_logs = db.get_ep_log_recent(100)
    judge_latencies = [
        item["latency_ms"]
        for item in recent_logs
        if item["agent_name"] == "Judge_Pass" and "ONNX" in item.get("model_name", "")
    ]

    judge_stats = {}
    if judge_latencies:
        import numpy as np
        judge_stats = {
            "model_name": "nli-MiniLM2-L6-H768-ONNX",
            "calls_count": len(judge_latencies),
            "mean_latency_ms": round(float(np.mean(judge_latencies)), 2),
            "median_latency_ms": round(float(np.median(judge_latencies)), 2),
            "min_latency_ms": round(float(np.min(judge_latencies)), 2),
            "max_latency_ms": round(float(np.max(judge_latencies)), 2),
            "p95_latency_ms": round(float(np.percentile(judge_latencies, 95)), 2),
        }

    output = {
        "benchmark_type": "locally measured CPU",
        "host_environment": "Windows 11 x64 (CPU execution fallback)",
        "deployment_target": "Snapdragon X Elite / X Plus (Hexagon NPU via QNN EP)",
        "pipeline_total_elapsed_ms": total_elapsed_ms,
        "judge_onnx_inference": judge_stats,
        "note": (
            "Measured with on-device ONNX Runtime Judge model (nli-MiniLM2-L6-H768-ONNX, Hugging Face). "
            "Transparent provider logging verified fallback to CPUExecutionProvider on x64 development host. "
            "Snapdragon NPU numbers will be appended once tested on physical ARM64 hardware or AI Hub cloud profiling."
        ),
    }
    path = Path("trustdoc_ai/benchmarks/latest_local_demo.json")
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\n[TrustDoc AI] Benchmark written to {path.resolve()}")
    if judge_stats:
        print(
            f"  Judge ONNX Mean Latency: {judge_stats['mean_latency_ms']} ms "
            f"({judge_stats['calls_count']} inferences)"
        )


if __name__ == "__main__":
    main()
