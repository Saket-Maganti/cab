"""Dependency-free local human-review HTTP application.

The service is intentionally local-only by default.  It stores submitted
judgments in an append-only JSONL ledger and never labels fixtures as genuine.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from causal_agent_bench.level5.review import Judgment

INDEX_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>CAB Human Review OS</title></head>
<body>
<main>
<h1>CAB Human Review OS</h1>
<p>Local review service. Submitted judgments are immutable and audited.</p>
<p>Use the versioned JSON API at <code>POST /v1/judgments</code>.</p>
</main>
</body>
</html>
"""


class ReviewLedger:
    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "judgments.jsonl"
        self.audit_path = self.data_dir / "audit.jsonl"
        self._ids = {
            row["judgment_id"]
            for row in self._read_lines(self.path)
            if isinstance(row.get("judgment_id"), str)
        }

    @staticmethod
    def _read_lines(path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def submit(self, judgment: Judgment) -> None:
        if judgment.judgment_id in self._ids:
            raise ValueError("submitted judgments are immutable")
        payload = judgment.model_dump(mode="json")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "event": "JUDGMENT_SUBMITTED",
                        "judgment_id": judgment.judgment_id,
                        "assignment_id": judgment.assignment_id,
                        "evidence_scope": judgment.evidence_scope,
                        "immutable": True,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
        self._ids.add(judgment.judgment_id)

    def status(self) -> dict[str, Any]:
        rows = self._read_lines(self.path)
        return {
            "judgment_count": len(rows),
            "genuine_count": sum(
                row.get("evidence_scope") == "GENUINE_HUMAN" for row in rows
            ),
            "fixture_count": sum(row.get("evidence_scope") == "FIXTURE_ONLY" for row in rows),
            "scientific_state": "HUMAN_VALIDATION_REQUIRED",
        }


def make_handler(ledger: ReviewLedger) -> type[BaseHTTPRequestHandler]:
    class ReviewHandler(BaseHTTPRequestHandler):
        server_version = "CABReviewOS/1.0"

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path == "/":
                data = INDEX_HTML.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.send_header(
                    "Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'"
                )
                self.end_headers()
                self.wfile.write(data)
            elif self.path == "/health":
                self._json(HTTPStatus.OK, {"status": "ok", "local_first": True})
            elif self.path == "/v1/status":
                self._json(HTTPStatus.OK, ledger.status())
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/v1/judgments":
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            if self.headers.get("X-CAB-Role") != "reviewer":
                self._json(HTTPStatus.FORBIDDEN, {"error": "reviewer role required"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid content length"})
                return
            if length < 1 or length > 1_000_000:
                self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "payload size"})
                return
            try:
                payload = json.loads(self.rfile.read(length))
                judgment = Judgment.model_validate(payload)
                ledger.submit(judgment)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            self._json(
                HTTPStatus.CREATED,
                {"accepted": True, "judgment_id": judgment.judgment_id, "immutable": True},
            )

        def log_message(self, format: str, *args: Any) -> None:
            del format, args

    return ReviewHandler


def serve_review_app(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    data_dir: str | Path = ".cab/review",
) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("non-local review binding requires an explicit deployment design")
    ledger = ReviewLedger(data_dir)
    server = ThreadingHTTPServer((host, port), make_handler(ledger))
    try:
        server.serve_forever()
    finally:
        server.server_close()


__all__ = ["ReviewLedger", "make_handler", "serve_review_app"]
