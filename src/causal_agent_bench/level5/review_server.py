"""Dependency-free local human-review HTTP application.

The service is intentionally local-only by default.  It stores submitted
judgments in an append-only JSONL ledger and never labels fixtures as genuine.
"""

from __future__ import annotations

import html
import json
import secrets
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from pydantic import ValidationError

from causal_agent_bench.level5.core import utc_now
from causal_agent_bench.level5.review import (
    Adjudication,
    DurableReviewStore,
    Judgment,
    LocalDevelopmentIdentityProvider,
    ReviewerRole,
)

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


def _page(title: str, body: str) -> bytes:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
body{{font:16px system-ui;max-width:72rem;margin:2rem auto;padding:0 1rem}}
nav,a{{margin-right:1rem}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #bbb;padding:.45rem;text-align:left}}
label{{display:block;margin:.5rem 0}} input,textarea,select{{max-width:40rem;width:100%}}
.warning{{border-left:4px solid #b45309;padding:.6rem;background:#fff7ed}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1rem}}
</style>
</head>
<body>
<nav><a href="/">Dashboard</a><a href="/coverage">Coverage</a></nav>
{body}
</body>
</html>""".encode()


def make_durable_handler(
    store: DurableReviewStore,
    *,
    identity_provider: LocalDevelopmentIdentityProvider | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Create the session-authenticated, CSRF-protected review application."""

    identity = identity_provider or LocalDevelopmentIdentityProvider()
    max_request_bytes = 64 * 1024

    class DurableReviewHandler(BaseHTTPRequestHandler):
        server_version = "CABReviewOS/2.0"

        def _security_headers(self, *, content_type: str, length: int) -> None:
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
                "base-uri 'none'; frame-ancestors 'none'",
            )

        def _respond(
            self,
            status: int,
            data: bytes,
            *,
            content_type: str = "text/html; charset=utf-8",
            cookie: str | None = None,
        ) -> None:
            self.send_response(status)
            self._security_headers(content_type=content_type, length=len(data))
            if cookie:
                self.send_header("Set-Cookie", cookie)
            self.end_headers()
            self.wfile.write(data)

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            self._respond(
                status,
                json.dumps(payload, sort_keys=True).encode(),
                content_type="application/json",
            )

        def _form(self) -> dict[str, str]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise ValueError("invalid content length") from exc
            if length < 1 or length > max_request_bytes:
                raise ValueError("request size is outside the allowed range")
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("application/x-www-form-urlencoded"):
                raise ValueError("form content type is required")
            parsed = parse_qs(
                self.rfile.read(length).decode("utf-8"),
                keep_blank_values=True,
                max_num_fields=32,
            )
            return {key: values[-1] for key, values in parsed.items()}

        def _cookie_token(self) -> str:
            cookie = SimpleCookie(self.headers.get("Cookie", ""))
            morsel = cookie.get("cab_review_session")
            if morsel is None:
                raise PermissionError("review session cookie is missing")
            return morsel.value

        def _session(
            self,
            *,
            csrf: str | None = None,
            roles: set[ReviewerRole] | None = None,
        ) -> dict[str, Any]:
            return store.authenticate(
                self._cookie_token(),
                csrf_token=csrf,
                allowed_roles=roles,
            )

        @staticmethod
        def _csrf_field(value: str) -> str:
            return (
                '<input type="hidden" name="csrf_token" '
                f'value="{html.escape(value, quote=True)}">'
            )

        def _login_page(self, error: str = "") -> bytes:
            error_html = (
                f'<p class="warning">{html.escape(error)}</p>' if error else ""
            )
            return _page(
                "CAB reviewer login",
                f"""
<h1>CAB Human Review OS</h1>
<p class="warning">The bundled identity adapter is local-development-only and
can create fixture evidence only. Production identity assurance requires an
external provider.</p>
{error_html}
<form method="post" action="/login">
<label>User ID <input name="user_id" required maxlength="128"></label>
<label>Identity assertion <input name="assertion" type="password" required
autocomplete="off"></label>
<button type="submit">Sign in</button>
</form>
""",
            )

        def _dashboard_page(self, session: dict[str, Any]) -> tuple[bytes, str]:
            user_id = str(session["user_id"])
            role = ReviewerRole(str(session["role"]))
            csrf = secrets.token_urlsafe(24)
            # Rotate the browser CSRF token by creating a short replacement
            # session; only the hash is stored. This also prevents a forged role
            # header from authorising any operation.
            store.logout(self._cookie_token())
            replacement = store.create_session(user_id)
            replacement_cookie = (
                "cab_review_session="
                f"{replacement.token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600"
            )
            csrf = replacement.csrf_token
            if not bool(session["qualified"]) and role is not ReviewerRole.ADMINISTRATOR:
                body = f"""
<h2>Qualification and consent</h2>
<p>Qualification requires direct human work without AI or proxy assistance.
Fixture users remain fixture-only after qualification.</p>
<form method="post" action="/qualify">
{self._csrf_field(csrf)}
<label><input type="checkbox" name="consented" value="true" required>
I consent to the documented review protocol.</label>
<label><input type="checkbox" name="human_attestation" value="true" required>
I attest that I am the direct human reviewer.</label>
<label><input type="checkbox" name="no_proxy" value="true" required>
I will not use AI or proxy assistance.</label>
<button type="submit">Complete qualification</button>
</form>"""
            elif role is ReviewerRole.REVIEWER:
                rows = store.assignments_for(user_id)
                cards = []
                for row in rows:
                    assignment_id = html.escape(str(row["assignment_id"]), quote=True)
                    item = html.escape(str(row["item_id"]))
                    state = html.escape(str(row["state"]))
                    cards.append(
                        f"""
<section>
<h2>{item}</h2><p>State: {state}</p>
<form method="post" action="/submit">
{self._csrf_field(csrf)}
<input type="hidden" name="assignment_id" value="{assignment_id}">
<input type="hidden" name="item_id" value="{html.escape(str(row['item_id']), quote=True)}">
<label>Valid <select name="valid"><option>true</option><option>false</option></select></label>
<label>Manipulation passed <select name="manipulation_passed"><option>true</option><option>false</option></select></label>
<label>Invariant <select name="invariant"><option>true</option><option>false</option></select></label>
<label>Solvable <select name="solvable"><option>true</option><option>false</option></select></label>
<label>Confidence <input name="confidence" type="number" min="0" max="1" step=".01" value=".8"></label>
<label>Time seconds <input name="time_seconds" type="number" min=".01" step=".01" value="1"></label>
<label>Notes <textarea name="notes" maxlength="4000"></textarea></label>
<button type="submit" formaction="/draft">Save draft</button>
<button type="submit">Submit immutable judgment</button>
<button type="submit" formaction="/conflict" formnovalidate>Declare conflict</button>
</form>
</section>"""
                    )
                body = "".join(cards) or "<p>No assignments.</p>"
            elif role is ReviewerRole.ADJUDICATOR:
                coverage = store.dashboard()["coverage"]
                option_rows = "".join(
                    f"<option>{html.escape(str(row['item_id']))}</option>"
                    for row in coverage
                )
                body = f"""
<h2>Adjudication</h2>
<form method="post" action="/adjudicate">
{self._csrf_field(csrf)}
<label>Item <select name="item_id">{option_rows}</select></label>
<label>Decision <select name="decision"><option>true</option><option>false</option></select></label>
<label>Rationale <textarea name="rationale" required maxlength="4000"></textarea></label>
<button type="submit">Submit immutable adjudication</button>
</form>"""
            else:
                dashboard = store.dashboard()
                coverage_rows = "".join(
                    "<tr>"
                    f"<td>{html.escape(str(row['item_id']))}</td>"
                    f"<td>{int(row['assignment_count'])}</td>"
                    f"<td>{int(row['submitted_count'])}</td>"
                    "</tr>"
                    for row in dashboard["coverage"]
                )
                workload_rows = "".join(
                    "<tr>"
                    f"<td>{html.escape(str(row['reviewer_id']))}</td>"
                    f"<td>{int(row['assigned'])}</td>"
                    f"<td>{int(row['submitted'])}</td>"
                    "</tr>"
                    for row in dashboard["workload"]
                )
                body = f"""
<div class="grid">
<section><h2>Coverage</h2><table><tr><th>Item</th><th>Assigned</th><th>Submitted</th></tr>
{coverage_rows}</table></section>
<section><h2>Workload</h2><table><tr><th>Reviewer</th><th>Assigned</th><th>Submitted</th></tr>
{workload_rows}</table></section>
</div>
<p>Agreement diagnostics: {html.escape(json.dumps(dashboard['agreement'], sort_keys=True))}</p>
<p>Genuine C10 remains fail-closed until genuine qualified review is present.</p>"""
            return (
                _page(
                    "CAB review dashboard",
                    f"""
<h1>Review dashboard</h1>
<p>User: {html.escape(user_id)} · role: {html.escape(role.value)}</p>
{body}
<form method="post" action="/logout">{self._csrf_field(csrf)}
<button type="submit">Log out</button></form>
""",
                ),
                replacement_cookie,
            )

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/health":
                self._json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "durable": True,
                        "session_auth": True,
                        "csrf": True,
                        "scientific_state": "HUMAN_VALIDATION_REQUIRED",
                    },
                )
                return
            if path == "/v1/status":
                self._json(HTTPStatus.OK, store.dashboard())
                return
            if path == "/v1/export/public":
                try:
                    self._session(roles={ReviewerRole.ADMINISTRATOR})
                except PermissionError as exc:
                    self._json(HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
                    return
                self._json(HTTPStatus.OK, store.export_public())
                return
            if path not in {"/", "/login", "/coverage"}:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            try:
                active_session = self._session()
            except PermissionError:
                self._respond(HTTPStatus.OK, self._login_page())
                return
            data, replacement_cookie = self._dashboard_page(active_session)
            self._respond(HTTPStatus.OK, data, cookie=replacement_cookie)

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            try:
                form = self._form()
                if path == "/login":
                    identity.resolve(form.get("user_id", ""), form.get("assertion", ""))
                    login_session = store.create_session(form["user_id"])
                    cookie = (
                        "cab_review_session="
                        f"{login_session.token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600"
                    )
                    self.send_response(HTTPStatus.SEE_OTHER)
                    self.send_header("Location", "/")
                    self.send_header("Set-Cookie", cookie)
                    self.send_header("Content-Length", "0")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    return
                csrf = form.get("csrf_token", "")
                if path == "/logout":
                    logout_session = self._session(csrf=csrf)
                    store.logout(self._cookie_token())
                    del logout_session
                    self.send_response(HTTPStatus.SEE_OTHER)
                    self.send_header("Location", "/login")
                    self.send_header(
                        "Set-Cookie",
                        "cab_review_session=; HttpOnly; SameSite=Strict; "
                        "Path=/; Max-Age=0",
                    )
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                active_session = self._session(csrf=csrf)
                if path == "/qualify":
                    store.qualify_user(
                        str(active_session["user_id"]),
                        consented=form.get("consented") == "true",
                        human_attestation=form.get("human_attestation") == "true",
                        proxy_or_ai_assistance=form.get("no_proxy") != "true",
                    )
                elif path == "/conflict":
                    store.declare_conflict(
                        self._cookie_token(),
                        csrf,
                        form["assignment_id"],
                    )
                elif path == "/draft":
                    store.autosave_draft(
                        self._cookie_token(),
                        csrf,
                        form["assignment_id"],
                        {
                            "valid": form.get("valid") == "true",
                            "manipulation_passed": form.get("manipulation_passed") == "true",
                            "invariant": form.get("invariant") == "true",
                            "solvable": form.get("solvable") == "true",
                            "confidence": form.get("confidence"),
                            "time_seconds": form.get("time_seconds"),
                            "notes": form.get("notes", ""),
                        },
                    )
                elif path == "/submit":
                    judgment = Judgment(
                        judgment_id=f"judgment.{secrets.token_hex(12)}",
                        assignment_id=form["assignment_id"],
                        item_id=form["item_id"],
                        reviewer_id=str(active_session["user_id"]),
                        valid=form["valid"] == "true",
                        manipulation_passed=form["manipulation_passed"] == "true",
                        invariant=form["invariant"] == "true",
                        solvable=form["solvable"] == "true",
                        confidence=float(form["confidence"]),
                        time_seconds=float(form["time_seconds"]),
                        notes=form.get("notes", ""),
                        submitted_at=utc_now(),
                        evidence_scope=str(active_session["evidence_scope"]),
                    )
                    store.submit_judgment(self._cookie_token(), csrf, judgment)
                elif path == "/adjudicate":
                    adjudication = Adjudication(
                        adjudication_id=f"adjudication.{secrets.token_hex(12)}",
                        item_id=form["item_id"],
                        adjudicator_id=str(active_session["user_id"]),
                        decision=form["decision"] == "true",
                        rationale=form["rationale"],
                        submitted_at=utc_now(),
                        evidence_scope=str(active_session["evidence_scope"]),
                    )
                    store.adjudicate(self._cookie_token(), csrf, adjudication)
                else:
                    self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return
                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header("Location", "/")
                self.send_header("Content-Length", "0")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
            except (KeyError, ValueError, ValidationError) as exc:
                self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except PermissionError as exc:
                self._json(HTTPStatus.FORBIDDEN, {"error": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:
            del format, args

    return DurableReviewHandler


def serve_review_app(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    data_dir: str | Path = ".cab/review",
) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("non-local review binding requires an explicit deployment design")
    data_dir = Path(data_dir)
    store = DurableReviewStore(data_dir / "review.sqlite3")
    server = ThreadingHTTPServer((host, port), make_durable_handler(store))
    try:
        server.serve_forever()
    finally:
        server.server_close()


__all__ = [
    "ReviewLedger",
    "make_durable_handler",
    "make_handler",
    "serve_review_app",
]
