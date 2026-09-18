# Submission Checklist

Use this before pushing/submitting the GitHub repository.

## Repo Must Pass

```powershell
python -m pytest tests
python -m trustdoc_ai demo
python -m trustdoc_ai benchmark
python -m trustdoc_ai download-models
```

## GitHub Page

- Add About description:
  `On-device document verification for Snapdragon PCs with auditable adversarial claim debate and transparent QNN/NPU execution logging.`
- Add topics:
  `snapdragon`, `qualcomm`, `hexagon-npu`, `onnx-runtime`, `qnn`, `on-device-ai`, `hallucination-detection`, `document-verification`
- Set social preview image to `docs/assets/trustdoc-ai-architecture.svg` or a real app screenshot.
- Confirm README renders the architecture image.
- Confirm GitHub Actions passes after push.

## Demo Assets

- Record a GIF or short video of `python -m trustdoc_ai demo` or the PySide UI.
- Add the video/GIF link to the top reviewer block in `README.md`.
- Do not edit benchmark tables to imply NPU acceleration until real NPU results exist.

## Honesty Guardrails

- Do not claim Llama/FastVLM is running until model artifacts are configured.
- Do not claim QNN/NPU execution unless `actual_provider` shows `QNNExecutionProvider`.
- Do not include generated `.db`, report JSON, cache, or model files in Git.
