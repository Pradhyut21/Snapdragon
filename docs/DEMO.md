# Demo Walkthrough

The included demo is designed to be reviewable without private files, cloud services, or a deployed web app.

![TrustDoc AI Desktop Prototype](assets/trustdoc-ui-prototype.jpg)
*TrustDoc AI running the adversarial debate verifier on conflicting documents.*

## Scenario

Two documents describe the same purchase order but disagree on one key field:

- `trustdoc_ai/demo/docs/invoice.txt`: `Payment Due Date: 2026-10-15`
- `trustdoc_ai/demo/docs/purchase_order.txt`: `Payment Due Date: 2026-11-15`

## Run

Execute the pipeline via the CLI:

```powershell
python -m trustdoc_ai demo
```

Equivalent direct runner command:

```powershell
python -m trustdoc_ai.demo.run_demo
```

## Expected Output Excerpt

```text
CONTRADICTED (0.86): Payment Due Date is 2026-10-15.
Judge: The ONNX Judge (nli-MiniLM2-L6-H768-ONNX) verified cross-document contradiction: direct support in one document conflicts with a different value in another.

CONTRADICTED (0.86): Payment Due Date is 2026-11-15.
Judge: The ONNX Judge (nli-MiniLM2-L6-H768-ONNX) verified cross-document contradiction: direct support in one document conflicts with a different value in another.

Human review items: 2
```

## Generated Artifacts

The demo creates local runtime artifacts that are intentionally git-ignored:

- `trustdoc_ai/demo/output/report.json`: Comprehensive report containing all document metadata, extracted claims, full debate transcripts, and provider telemetry.
- `trustdoc_ai/demo/trustdoc_demo.db`: SQLite database storing runs, documents, claims, transcripts, and per-inference `ep_indicator_log` records.

![TrustDoc AI Audit Log Inspector](assets/trustdoc-audit-trail.jpg)
*Audit trail inspector displaying SQLite persistence and transparent execution provider telemetry.*

## Why This Demo Matters

The contradiction is not just an opaque single-pass label. The output:
1. Shows distinct Prosecutor and Defender arguments grounded in retrieved document context;
2. Executes an on-device ONNX NLI model for the Judge decision;
3. Logs transparent execution-provider telemetry per inference;
4. Automatically routes low-confidence and contradicted verdicts into a Human-in-the-Loop (HITL) queue.
