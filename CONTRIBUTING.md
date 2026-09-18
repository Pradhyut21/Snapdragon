# Contributing

TrustDoc AI is organized so judges and contributors can map code to the architecture quickly.

## Development Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python setup.py
python -m pytest tests
```

For lightweight development without the full ML/UI stack, the current tests run with the standard library plus pytest.

## Before Opening a PR

```powershell
python -m pytest tests
python -m trustdoc_ai demo
python -m trustdoc_ai benchmark
```

## Code Rules

- Keep execution-provider reporting explicit.
- Use `OnnxRunner` for ONNX model calls so provider fallback is logged.
- Store debate transcripts as first-class artifacts.
- Do not add benchmark numbers without source metadata.
- Do not commit generated DBs, reports, model caches, or private documents.
