> **For reviewers:** TrustDoc AI is an on-device document verification system for Snapdragon-powered Windows PCs.
> Its intended differentiator is a separately logged Prosecutor / Defender / Judge debate before a claim is flagged, so the verdict is auditable instead of a single opaque classifier pass.
> The current repository implements a runnable local 7-stage pipeline demo, including document parsing, retrieval, claim extraction, distinct Prosecutor / Defender / Judge calls, audit persistence, HITL routing, and tests.
> Target hardware is Snapdragon X Elite / X Plus with Hexagon NPU via ONNX Runtime QNN Execution Provider, with honest CPU fallback on x64.
> Demo video/GIF: not recorded yet, but the local demo runs with `python -m trustdoc_ai.demo.run_demo`; see [NOTES.md](NOTES.md) for remaining reviewer polish.

# TrustDoc AI

[![Tests](https://img.shields.io/badge/tests-pytest-blue)](#presentation--documentation)
[![Target](https://img.shields.io/badge/target-Snapdragon%20X%20Elite%20%2F%20X%20Plus-green)](#deployment--accessibility)
[![Runtime](https://img.shields.io/badge/runtime-ONNX%20Runtime%20%2B%20QNN-orange)](#technical-implementation)
[![Demo](https://img.shields.io/badge/demo-local%20contradiction%20pipeline-purple)](docs/DEMO.md)

TrustDoc AI is being built for the Qualcomm Snapdragon AI Lab Build & Present Challenge. It ingests local documents, extracts checkable claims, retrieves evidence across the document set, runs an adversarial debate over each claim, routes risky verdicts to review, and stores an auditable trail on disk.

![TrustDoc AI architecture](docs/assets/trustdoc-ai-architecture.svg)

Reviewer shortcuts:

- [AI reviewer brief](docs/AI_REVIEWER_BRIEF.md)
- [Demo walkthrough](docs/DEMO.md)
- [Architecture deep dive](docs/ARCHITECTURE.md)
- [Benchmarking policy](docs/BENCHMARKING.md)
- [Submission checklist](docs/SUBMISSION_CHECKLIST.md)

## Technical Implementation

### Current implementation status

| Area | Status | Where to inspect |
| --- | --- | --- |
| Hardware detection | Implemented | [`trustdoc_ai/core/hardware_detect.py`](trustdoc_ai/core/hardware_detect.py) |
| ONNX/QNN session wrapper | Implemented, ready for model artifacts | [`trustdoc_ai/core/onnx_runner.py`](trustdoc_ai/core/onnx_runner.py) |
| QNN / CPU install selection | Implemented | [`setup.py`](setup.py), [`requirements.txt`](requirements.txt) |
| SQLite audit trail | Implemented | [`trustdoc_ai/db/audit_db.py`](trustdoc_ai/db/audit_db.py), [`trustdoc_ai/db/schema.sql`](trustdoc_ai/db/schema.sql) |
| Document parsing | Implemented for TXT/MD/PDF/DOCX/XLSX | [`trustdoc_ai/agents/doc_intel.py`](trustdoc_ai/agents/doc_intel.py) |
| Retrieval | Implemented as local bag-of-words vector search | [`trustdoc_ai/agents/retrieval.py`](trustdoc_ai/agents/retrieval.py) |
| Claim extraction | Implemented with conservative local rules | [`trustdoc_ai/agents/claim_extractor.py`](trustdoc_ai/agents/claim_extractor.py) |
| Adversarial debate verifier | Implemented with three separate local deterministic calls | [`trustdoc_ai/agents/verifier.py`](trustdoc_ai/agents/verifier.py) |
| Debate transcript storage | Implemented | [`trustdoc_ai/orchestrator.py`](trustdoc_ai/orchestrator.py) |
| Per-inference execution-provider logs | Implemented | [`trustdoc_ai/agents/verifier.py`](trustdoc_ai/agents/verifier.py) |
| HITL routing | Implemented | [`trustdoc_ai/orchestrator.py`](trustdoc_ai/orchestrator.py) |
| Demo document set | Implemented | [`trustdoc_ai/demo/docs/`](trustdoc_ai/demo/docs/) |
| Root pytest suite | Implemented | [`tests/`](tests/) |
| PySide UI | Implemented with CLI fallback | [`trustdoc_ai/ui/main_window.py`](trustdoc_ai/ui/main_window.py) |
| Recorded GIF/video and real NPU LLM benchmarks | Not available yet | Tracked in [`NOTES.md`](NOTES.md) |

### Architecture

The 7-stage pipeline is:

1. **Doc-Intel Agent**: parse PDF/image/DOCX/XLSX into structured text and layout.
2. **Vision Agent**: read scanned tables, stamps, and signatures.
3. **Embedding & Retrieval Agent**: chunk documents, create local embeddings, and query a local vector index.
4. **Claim Extraction Agent**: extract discrete factual claims.
5. **Adversarial Debate Verifier**: run three distinct, loggable inference calls: Prosecutor, Defender, and Judge.
6. **Schema Mapper Agent**: normalize verified facts into structured JSON.
7. **Orchestrator + HITL Router**: write the report and route low-confidence or contradicted claims to review.

The demo verifier currently uses `local_rules_debate_v1`, a deterministic local verifier, because no ONNX LLM artifact is configured in this repository. The three debate roles are still separate function calls with separate EP log entries. This is a working end-to-end pipeline, but it should not be described as Llama/QNN model inference until real AI Hub artifacts are wired in.

### Execution-provider transparency

TrustDoc AI does not silently claim NPU execution. Hardware detection checks both `QNNExecutionProvider` registration and the presence of `QnnHtp.dll`. Every debate pass writes an `ep_indicator_log` row with `requested_provider`, `actual_provider`, and `latency_ms`. In the current demo, `actual_provider` is `CPUExecutionProvider` because the verifier is the local deterministic implementation, not an ONNX LLM artifact.

### Tests

Run the lightweight implemented tests with:

```powershell
python -m pytest tests
```

Run the full local smoke path with:

```powershell
python -m pytest tests
python -m trustdoc_ai demo
python -m trustdoc_ai benchmark
python -m trustdoc_ai download-models
```

The tests cover:

- architecture normalization and QNN availability checks;
- SQLite migration behavior;
- debate transcript persistence;
- execution-provider log persistence;
- end-to-end demo contradiction detection.

## Application Use Case & Innovation

Typical document-checking tools can collapse verification into one model pass. TrustDoc AI's intended innovation is to make verification adversarial and inspectable: a Prosecutor argues the claim is unsupported or contradicted, a Defender argues it is supported by retrieved evidence, and a Judge reads the evidence plus both arguments before producing `SUPPORTED`, `CONTRADICTED`, or `UNSUPPORTED`.

Why this matters: document verification failures are often not simple classification misses; they are reasoning misses. A debate transcript gives the user and reviewer a concrete artifact to inspect, and it gives downstream human review a reasoned starting point instead of a naked label.

### Concrete contradiction example

The included demo document set contains this planted mismatch:

| Document | Claim |
| --- | --- |
| [`invoice.txt`](trustdoc_ai/demo/docs/invoice.txt) | `Payment Due Date: 2026-10-15` |
| [`purchase_order.txt`](trustdoc_ai/demo/docs/purchase_order.txt) | `Payment Due Date: 2026-11-15` |

Run it with:

```powershell
python -m trustdoc_ai.demo.run_demo
```

Expected result excerpt:

```text
CONTRADICTED (0.86): Payment Due Date is 2026-10-15.
Judge: The debate found direct support in one document and a different value for the same field in another document.
```

The full JSON report is written to `trustdoc_ai/demo/output/report.json`, and the audit database is written to `trustdoc_ai/demo/trustdoc_demo.db`.

### Why not just use ChatGPT or a cloud LLM?

The target use cases involve documents that may contain contracts, invoices, identity records, compliance files, or internal financial details. Running locally on Snapdragon hardware keeps documents on disk, avoids cloud upload review paths, and can reduce latency once NPU acceleration is verified. This repository currently publishes only local demo timings, not final CPU-vs-NPU LLM latency numbers.

## Deployment & Accessibility

### System requirements

- Windows 11 on Snapdragon X Elite / X Plus for NPU acceleration.
- Windows x64 is supported for CPU fallback development.
- Python 3.11 or 3.12 is recommended. Python 3.13 may work for the currently implemented tests, but some ML wheels may lag.
- Qualcomm AI Hub credentials are required before model download/export work can be completed.

### Quick Start

Clone the repository, create a virtual environment, and run setup:

```powershell
git clone <your-repo-url>
cd Snapdragon
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python setup.py
python -m pytest tests
python -m trustdoc_ai demo
```

Or use the PowerShell wrapper:

```powershell
.\setup.ps1
```

The CLI also supports:

```powershell
python -m trustdoc_ai hardware
python -m trustdoc_ai download-models
python -m trustdoc_ai benchmark
```

On Windows ARM64, `setup.py` installs `onnxruntime-qnn==1.19.0`. On Windows x64, it installs `onnxruntime==1.19.0` and warns that QNN/NPU acceleration is unavailable.

### Model setup status

`python setup.py --download-models` calls `trustdoc_ai/scripts/download_models.py`. The script creates/checks the local model cache and reports whether `qai_hub` and `qai_hub_models` are installed. It does not download unverified model artifacts or invent Qualcomm AI Hub model names.

Qualcomm references used for the intended integration path:

- [Qualcomm AI Hub Apps](https://github.com/qualcomm/ai-hub-apps), which publishes sample apps for deploying AI Hub models on local devices.
- [Qualcomm AI Hub Models](https://github.com/qualcomm/ai-hub-models), which provides optimized model packages and AI Hub model workflows.

### Benchmarks

Run the current local demo benchmark with:

```powershell
python -m trustdoc_ai.benchmarks.run_benchmark
```

This writes `trustdoc_ai/benchmarks/latest_local_demo.json`. It is labeled as `locally measured CPU/local-rules demo`; it is not an NPU or ONNX LLM benchmark.

Future model benchmark tables must label each number as one of:

- `locally measured CPU`;
- `locally measured QNN/NPU`;
- `AI Hub cloud-profiled`.

Numbers should not be added to this README until they are produced by a repeatable script and saved with environment details.

## Presentation & Documentation

### Repository structure

```text
trustdoc_ai/
  core/                 Hardware detection and future runtime selection
  db/                   SQLite audit schema, migrations, and CRUD helper
  agents/               Pipeline agents: parsing, retrieval, claims, debate, schema
  benchmarks/           Local benchmark script and generated benchmark output
  demo/                 Sample contradiction documents and demo runner
  models/cache/         Local model/tokenizer cache location
  scripts/              Model cache/setup helpers
  ui/                   PySide6 desktop UI with CLI fallback
tests/                  Root pytest suite for implemented behavior
docs/
  ARCHITECTURE.md       Deeper architecture and implementation notes
  assets/               README images
```

### GitHub repository metadata to set manually

GitHub About description:

```text
On-device document verification for Snapdragon PCs with auditable adversarial claim debate and transparent QNN/NPU execution logging.
```

Recommended topics:

```text
snapdragon, qualcomm, hexagon-npu, onnx-runtime, qnn, on-device-ai, hallucination-detection, document-verification
```

Set the social preview image to `docs/assets/trustdoc-ai-architecture.svg` or to a real app screenshot once the UI exists.

### License

This repository includes an MIT license in [`LICENSE`](LICENSE).

### Challenge rule note

This repository currently appears to be a standalone implementation. If code is reused from ProductTruth, VERITAS, or another prior project, add a short attribution note here before submission describing what was reused and what was significantly modified.
