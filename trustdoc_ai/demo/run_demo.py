"""Run the sample TrustDoc AI contradiction demo."""

from __future__ import annotations

from pathlib import Path

from trustdoc_ai.orchestrator import TrustDocOrchestrator


def main() -> None:
    docs_dir = Path("trustdoc_ai/demo/docs")
    paths = [
        str(docs_dir / "invoice.txt"),
        str(docs_dir / "purchase_order.txt"),
    ]
    result = TrustDocOrchestrator().run(paths)
    print(f"Run ID: {result.run_id}")
    print(f"Report: {result.report_path}")
    print(f"Audit DB: {result.db_path}")
    print(f"Provider: {result.provider}")
    print("\nVerdicts:")
    for item in result.verdicts:
        verification = item["verification"]
        print(
            f"- {verification['verdict']} "
            f"({verification['confidence_score']:.2f}): "
            f"{item['claim']['text']}"
        )
        print(f"  Judge: {verification['judge_rationale']}")
    if result.hitl_queue:
        print(f"\nHuman review items: {len(result.hitl_queue)}")
    return result


if __name__ == "__main__":
    main()
