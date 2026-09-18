# Demo Walkthrough

The included demo is designed to be reviewable without private files, cloud services, or a deployed web app.

## Scenario

Two documents describe the same purchase order but disagree on one field:

- `trustdoc_ai/demo/docs/invoice.txt`: `Payment Due Date: 2026-10-15`
- `trustdoc_ai/demo/docs/purchase_order.txt`: `Payment Due Date: 2026-11-15`

## Run

```powershell
python -m trustdoc_ai demo
```

Equivalent legacy command:

```powershell
python -m trustdoc_ai.demo.run_demo
```

## Expected Output Excerpt

```text
CONTRADICTED (0.86): Payment Due Date is 2026-10-15.
Judge: The debate found direct support in one document and a different value for the same field in another document.

CONTRADICTED (0.86): Payment Due Date is 2026-11-15.
Judge: The debate found direct support in one document and a different value for the same field in another document.

Human review items: 2
```

## Generated Artifacts

The demo creates local runtime artifacts that are intentionally git-ignored:

- `trustdoc_ai/demo/output/report.json`
- `trustdoc_ai/demo/trustdoc_demo.db`

The JSON report includes:

- source documents;
- extracted claims;
- retrieved evidence snippets;
- prosecutor argument;
- defender argument;
- judge verdict and rationale;
- execution-provider log references;
- human-review queue items.

## Why This Demo Matters

The contradiction is not just a single label. The output shows the reasoning path and stores the transcript, which is the core differentiator from single-pass document checkers.
