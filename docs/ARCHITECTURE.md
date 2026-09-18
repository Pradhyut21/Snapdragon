# TrustDoc AI Architecture

This document records the architecture and implementation boundaries in this repository.

## Design Goal

TrustDoc AI is designed as a local-only document verification pipeline for Snapdragon-powered Windows PCs. The important product behavior is not just a final verdict; it is the auditable path to that verdict, including retrieved evidence, distinct adversarial model calls, execution-provider logs, and human-review routing.

## Pipeline

1. **Doc-Intel Agent**
   Parses PDF, image, DOCX, and XLSX inputs into structured text plus layout metadata.

2. **Vision Agent**
   Handles scanned tables, stamps, signatures, and image-only pages.

3. **Embedding & Retrieval Agent**
   Chunks extracted text, computes local embeddings, and retrieves evidence snippets from a local vector index.

4. **Claim Extraction Agent**
   Produces discrete factual claims that can be checked against retrieved evidence.

5. **Adversarial Debate Verifier**
   Runs three separate inference calls with distinct roles:
   - Prosecutor: argue unsupported or contradicted.
   - Defender: argue supported.
   - Judge: decide `SUPPORTED`, `CONTRADICTED`, or `UNSUPPORTED` with confidence and rationale.

6. **Schema Mapper Agent**
   Converts extracted and verified data into a validated JSON result.

7. **Orchestrator + HITL Router**
   Stores the final report and escalates low-confidence or contradicted claims to a human queue.

## Implemented Layers

### Hardware Detection

[`trustdoc_ai/core/hardware_detect.py`](../trustdoc_ai/core/hardware_detect.py) detects:

- normalized architecture: `arm64`, `x64`, or `unknown`;
- installed ONNX Runtime version;
- whether `QNNExecutionProvider` is registered;
- whether `QnnHtp.dll` is present in common Qualcomm SDK locations, the working directory, or `PATH`.

The code requires both provider registration and DLL presence before reporting QNN availability.

### ONNX Runtime Wrapper

[`trustdoc_ai/core/onnx_runner.py`](../trustdoc_ai/core/onnx_runner.py) centralizes ONNX Runtime session creation. It requests `QNNExecutionProvider` only when hardware detection verifies QNN availability, keeps `CPUExecutionProvider` as an explicit fallback, reads `session.get_providers()` after initialization, and writes the actual provider plus latency into the audit trail.

### Dependency Selection

[`setup.py`](../setup.py) selects the ONNX Runtime package by architecture:

- Windows ARM64: `onnxruntime-qnn==1.19.0`;
- Windows x64: `onnxruntime==1.19.0` with an explicit CPU fallback warning.

The common dependency list is pinned in [`requirements.txt`](../requirements.txt).

### Agents

The current pipeline implements:

- `DocIntelAgent`: TXT/MD/PDF/DOCX/XLSX parsing.
- `VisionAgent`: lightweight layout signal extraction.
- `RetrievalAgent`: local bag-of-words evidence search.
- `ClaimExtractionAgent`: conservative field/sentence claim extraction.
- `DebateVerifier`: three separate Prosecutor, Defender, and Judge calls.
- `SchemaMapperAgent`: stable JSON result mapping.
- `TrustDocOrchestrator`: DB writes, report generation, and HITL routing.

The debate verifier currently uses `local_rules_debate_v1`, not a Llama ONNX artifact.

### Audit Storage

[`trustdoc_ai/db/schema.sql`](../trustdoc_ai/db/schema.sql) and [`trustdoc_ai/db/audit_db.py`](../trustdoc_ai/db/audit_db.py) define and access the local audit trail:

- pipeline runs;
- ingested documents;
- claims;
- debate transcripts;
- schema errors;
- human review queue;
- execution-provider indicator logs;
- final document results.

Connections enable WAL mode and foreign keys on open.

## Execution-Provider Logging Contract

Every model wrapper writes one `ep_indicator_log` row per inference call:

- `agent_name`: the logical caller, such as `Prosecutor_Pass`;
- `model_name`: the concrete model artifact;
- `requested_provider`: usually `QNNExecutionProvider` on Snapdragon ARM64;
- `actual_provider`: the provider actually used by the initialized ONNX Runtime session;
- `latency_ms`: measured wall-clock inference latency.

This contract is intentionally part of the database schema before model execution is implemented, because it is central to the project's honesty guardrail.

## Missing Before Final Snapdragon/NPU Submission

Before this repo can honestly claim full Snapdragon NPU LLM execution, it still needs:

- demo GIF/video;
- verified Qualcomm AI Hub model choices;
- concrete ONNX Runtime wrappers for those artifacts;
- FastVLM scanned-page integration;
- real measured/profiled CPU-vs-NPU model latency numbers.
