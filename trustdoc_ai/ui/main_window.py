"""Minimal PySide6 UI for running the local demo."""

from __future__ import annotations

import sys

from trustdoc_ai.demo.run_demo import main as run_cli_demo
from trustdoc_ai.orchestrator import TrustDocOrchestrator


def main() -> None:
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget
    except ImportError:
        print("PySide6 is not installed; running the CLI demo instead.\n")
        run_cli_demo()
        return

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("TrustDoc AI")
            self.output = QTextEdit()
            self.output.setReadOnly(True)
            button = QPushButton("Run sample contradiction demo")
            button.clicked.connect(self.run_demo)
            layout = QVBoxLayout()
            layout.addWidget(button)
            layout.addWidget(self.output)
            root = QWidget()
            root.setLayout(layout)
            self.setCentralWidget(root)
            self.resize(900, 650)

        def run_demo(self) -> None:
            result = TrustDocOrchestrator().run(
                [
                    "trustdoc_ai/demo/docs/invoice.txt",
                    "trustdoc_ai/demo/docs/purchase_order.txt",
                ]
            )
            lines = [
                f"Run ID: {result.run_id}",
                f"Report: {result.report_path}",
                f"Audit DB: {result.db_path}",
                f"Provider: {result.provider}",
                "",
            ]
            for item in result.verdicts:
                verification = item["verification"]
                lines.append(
                    f"{verification['verdict']} ({verification['confidence_score']:.2f}) "
                    f"- {item['claim']['text']}"
                )
                lines.append(f"  Prosecutor: {verification['prosecutor_argument']}")
                lines.append(f"  Defender: {verification['defender_argument']}")
                lines.append(f"  Judge: {verification['judge_rationale']}")
                lines.append("")
            self.output.setPlainText("\n".join(lines))

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
