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
- **Total Pipeline Time**: 15.17 s (Full ingestion, parsing, retrieval, and 54 debate passes)
- **Claims Evaluated**: 18 claims (9 from invoice.txt, 9 from purchase_order.txt)
- **Total Debate Passes**: 54 passes (18 Prosecutor + 18 Defender + 18 Judge passes)
- **Judge ONNX Inferences**: 18 calls (1 per claim via `OnnxRunner` with EP logging)
- **Judge Latency Statistics**:
  - Mean: **78.44 ms**
  - Median: **76.96 ms**
  - Min: **60.64 ms**
  - Max: **98.65 ms**
  - P95: **91.80 ms**

In accordance with this policy, no speculative numbers are published in the results. Real NPU figures will be added upon physical hardware testing or AI Hub cloud profiling.

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
