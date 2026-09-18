"""Command line interface for TrustDoc AI."""

from __future__ import annotations

import argparse
import json

from trustdoc_ai.benchmarks.run_benchmark import main as benchmark_main
from trustdoc_ai.core.hardware_detect import detect_hardware
from trustdoc_ai.demo.run_demo import main as demo_main
from trustdoc_ai.scripts.download_models import main as download_models_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trustdoc-ai",
        description="Run TrustDoc AI demos, checks, and setup helpers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("demo", help="Run the planted-contradiction demo")
    subparsers.add_parser("benchmark", help="Benchmark the current local demo")
    subparsers.add_parser("download-models", help="Prepare/check model cache")
    subparsers.add_parser("hardware", help="Print hardware and QNN availability")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        demo_main()
    elif args.command == "benchmark":
        benchmark_main()
    elif args.command == "download-models":
        download_models_main()
    elif args.command == "hardware":
        profile = detect_hardware()
        print(json.dumps(profile.__dict__, indent=2))
    else:
        raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
