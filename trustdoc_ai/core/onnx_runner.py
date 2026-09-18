"""ONNX Runtime session wrapper with transparent QNN provider handling."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from trustdoc_ai.core.hardware_detect import HardwareProfile, get_hardware_profile
from trustdoc_ai.core.utils import new_id, utc_now
from trustdoc_ai.db.audit_db import AuditDB


class OnnxRunner:
    """Run an ONNX model and log the provider that ONNX Runtime actually used.

    This wrapper is intentionally small and explicit because provider reporting
    is a judging-sensitive part of TrustDoc AI. Agents should not instantiate
    raw `onnxruntime.InferenceSession` objects directly; they should use this
    class so CPU fallback is visible in the audit trail.
    """

    def __init__(
        self,
        model_path: str,
        db: AuditDB,
        agent_name: str,
        model_name: str,
        hardware: HardwareProfile | None = None,
    ) -> None:
        self.model_path = str(Path(model_path).resolve())
        self.db = db
        self.agent_name = agent_name
        self.model_name = model_name
        self.hardware = hardware or get_hardware_profile()
        self.requested_provider = (
            "QNNExecutionProvider"
            if self.hardware.qnn_ep_available
            else "CPUExecutionProvider"
        )
        self.session = self._create_session()
        providers = self.session.get_providers()
        self.actual_provider = providers[0] if providers else "unknown"

    def _create_session(self) -> Any:
        try:
            import onnxruntime as ort  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install onnxruntime or onnxruntime-qnn before loading ONNX models") from exc

        providers = [self.requested_provider]
        if self.requested_provider != "CPUExecutionProvider":
            # CPU is listed second so a QNN initialization failure remains
            # visible via `actual_provider` after session creation.
            providers.append("CPUExecutionProvider")
        return ort.InferenceSession(self.model_path, providers=providers)

    def run(self, feeds: dict[str, Any]) -> tuple[list[Any], str]:
        started = time.perf_counter()
        outputs = self.session.run(None, feeds)
        latency_ms = (time.perf_counter() - started) * 1000
        log_id = new_id("ep")
        self.db.insert_ep_log(
            log_id=log_id,
            timestamp=utc_now(),
            agent_name=self.agent_name,
            model_name=self.model_name,
            requested_provider=self.requested_provider,
            actual_provider=self.actual_provider,
            latency_ms=round(latency_ms, 3),
        )
        return outputs, log_id
