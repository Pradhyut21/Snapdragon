# TrustDoc AI Submission Notes

This file tracks submission progress and reviewer assets for the Qualcomm Snapdragon AI Lab Build & Present Challenge.

## Completed Engineering & Assets

- [x] **Adversarial Judge AI Model**: Integrated on-device quantized ONNX NLI model (`nli-MiniLM2-L6-H768-ONNX`) via `OnnxRunner` in `trustdoc_ai/agents/verifier.py`.
- [x] **Model Download & Cache**: Automated fetch/cache script in `trustdoc_ai/scripts/download_models.py` (`python -m trustdoc_ai download-models`).
- [x] **EP Logging Transparency**: Verified `ep_indicator_log` tracking of requested provider vs actual provider and live latency.
- [x] **UI Prototype Visuals**: High-fidelity desktop UI and audit trail screenshots created in `docs/assets/` and embedded in `README.md`.
- [x] **Measured Benchmarks**: Benchmarked local pipeline and ONNX Judge latency (~134 ms on CPU) saved in `latest_local_demo.json` and documented in `README.md`.
- [x] **Challenge Attribution**: Finalized explicit attribution in `README.md` confirming standalone authorship.
- [x] **Test Suite**: Verified all 6 pytest unit tests passing.

## Remaining Reviewer Polish (Manual Steps)

- Record a short screen-capture demo GIF or video showing `python -m trustdoc_ai demo` or the desktop UI.
- Apply GitHub repository metadata on github.com:
  - **About Description**: `On-device document verification for Snapdragon PCs with auditable adversarial claim debate and transparent QNN/NPU execution logging.`
  - **Topics**: `snapdragon, qualcomm, hexagon-npu, onnx-runtime, qnn, on-device-ai, hallucination-detection, document-verification`
  - **Social Preview**: `docs/assets/trustdoc-ui-prototype.jpg`
- Run AI Hub cloud profiling on Snapdragon X Elite hardware if available to append real NPU numbers to `docs/BENCHMARKING.md`.
