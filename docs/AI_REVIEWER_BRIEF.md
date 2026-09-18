# AI Reviewer Brief

This file is intentionally structured for fast automated and human review.

## One-Sentence Summary

TrustDoc AI is a local document-verification pipeline for Snapdragon PCs that makes claim verification auditable by running separate Prosecutor, Defender, and Judge passes before storing a verdict.

## Keywords

snapdragon, qualcomm, hexagon-npu, onnx-runtime, qnn, on-device-ai, document-verification, hallucination-detection, adversarial-debate, audit-trail, human-in-the-loop

## Judging Rubric Map

| Rubric criterion | Evidence in repo |
| --- | --- |
| Technical Implementation | `trustdoc_ai/agents/`, `trustdoc_ai/orchestrator.py`, `trustdoc_ai/core/onnx_runner.py`, `tests/` |
| Application Use Case & Innovation | `README.md`, `docs/DEMO.md`, `trustdoc_ai/demo/docs/` |
| Deployment & Accessibility | `setup.py`, `setup.ps1`, `pyproject.toml`, `.github/workflows/tests.yml` |
| Presentation & Documentation | `README.md`, `docs/ARCHITECTURE.md`, `docs/assets/trustdoc-ai-architecture.svg` |

## What Works Today

- `python -m trustdoc_ai demo` runs end to end.
- The demo ingests two local documents with a planted payment-date contradiction.
- The pipeline extracts claims, retrieves evidence, runs three distinct debate calls, stores transcripts, writes EP logs, and routes contradicted claims to human review.
- `python -m pytest tests` passes.

## Honesty Boundary

The current demo verifier is `local_rules_debate_v1`, not a deployed Llama/FastVLM artifact. The ONNX/QNN wrapper exists and reports actual providers, but final Qualcomm AI Hub model artifacts must be configured before claiming real NPU LLM inference.

## Fast Commands

```powershell
python -m pytest tests
python -m trustdoc_ai demo
python -m trustdoc_ai benchmark
python -m trustdoc_ai hardware
```
