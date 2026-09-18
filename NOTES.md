# TrustDoc AI Submission Notes

This file tracks items that should be completed by a human before submitting the GitHub repository for judging. These are intentionally kept out of the README as finished claims until they exist.

## Required Reviewer Assets

- Record a short screen-capture demo GIF or video showing the app running end to end.
- Record the actual debate transcript and final verdict in a screen-capture walkthrough.
- Replace the README's demo note with the real embedded GIF or video link.
- Set the GitHub About description and topics listed in the README.
- Set the GitHub social preview image to a screenshot or the architecture image.

## Required Engineering Work

- Replace `local_rules_debate_v1` with real ONNX Runtime model wrappers once verified AI Hub artifacts are selected.
- Add a real Llama/FastVLM model export/download path to `trustdoc_ai/scripts/download_models.py`.
- Add integration tests for PDF/DOCX/XLSX parsing on fixture files.
- Add UI tests once PySide6 is installed in CI.

## Benchmarks

Do not add benchmark numbers until they are measured or AI Hub profiled. Each benchmark must say whether it is:

- locally measured CPU;
- locally measured QNN/NPU;
- AI Hub cloud-profiled.

## Git History

The current workspace at `D:\Snapdragon` is not a Git repository. Before publishing, initialize Git and make incremental commits that reflect the actual development order. Do not fabricate old dates or misleading history.
