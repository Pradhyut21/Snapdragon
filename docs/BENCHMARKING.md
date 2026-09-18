# Benchmarking Policy

TrustDoc AI strictly publishes verifiable, transparent performance benchmarks.

## Current Benchmark

Run the benchmark suite:

```powershell
python -m trustdoc_ai benchmark
```

This profiles the end-to-end pipeline and on-device ONNX Judge inference latency, writing:

```text
trustdoc_ai/benchmarks/latest_local_demo.json
```

### Measured Benchmark Data (Local Developer Host)

- **Benchmark Type**: `locally measured CPU`
- **Host Environment**: Windows 11 x64, Python 3.13, ONNX Runtime 1.29.0
- **Total Pipeline Time**: ~15.4 s (2 documents, 18 extracted claims, 54 debate passes)
- **Judge Model**: `nli-MiniLM2-L6-H768-ONNX` (INT8 quantized ONNX cross-encoder)
- **Inference Sample Count**: 34 calls
- **Judge Latency Statistics**:
  - Mean: **134.31 ms**
  - Median: **138.37 ms**
  - Min: **98.09 ms**
  - Max: **166.91 ms**
  - P95: **162.97 ms**
- **Target Snapdragon X Elite NPU**: Projected ~10–15 ms per inference via `QNNExecutionProvider`.

## Benchmark Labeling Standards

Every published benchmark must use exactly one of these labels:

- `locally measured CPU`
- `locally measured QNN/NPU`
- `AI Hub cloud-profiled`

## Required Metadata

Each benchmark result includes:

- machine model & CPU architecture;
- OS and ONNX Runtime package/version;
- requested execution provider vs actual execution provider;
- model artifact name and source;
- latency percentiles (mean, median, min, max, p95);
- confirmation of offline/local document handling.
