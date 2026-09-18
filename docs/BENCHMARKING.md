# Benchmarking Policy

TrustDoc AI should never publish unverifiable performance claims.

## Current Benchmark

Run:

```powershell
python -m trustdoc_ai benchmark
```

This measures the current local deterministic demo pipeline and writes:

```text
trustdoc_ai/benchmarks/latest_local_demo.json
```

The benchmark type is labeled:

```text
locally measured CPU/local-rules demo
```

It is not an NPU benchmark and does not measure ONNX LLM inference.

## Future Benchmark Labels

Every published number must use exactly one of these labels:

- `locally measured CPU`
- `locally measured QNN/NPU`
- `AI Hub cloud-profiled`

## Required Metadata

Each benchmark result should include:

- machine model;
- CPU architecture;
- Windows version;
- ONNX Runtime package/version;
- requested execution provider;
- actual execution provider;
- model artifact name and source;
- median latency and sample count;
- whether documents stayed local.
