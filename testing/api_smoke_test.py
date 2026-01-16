"""API Smoke Test Script

Calls selected endpoints in the Knowunity Agent Olympics 2026 API.

Notes
-----
This script intentionally **does not** call:
- any `/admin/*` endpoints
- any `/evaluate/*` endpoints

It only calls the remaining "public" endpoints:
- `GET /`, `GET /health`
- `GET /students`, `GET /students/{student_id}/topics`
- `GET /subjects`, `GET /topics`
- `POST /interact/start`, `POST /interact`

Auth:
- `POST /interact/*` requires header `x-api-key`.

Provide the API key via environment variable (usually via a .env file in the repo root):
  - KNOWUNITY_X_API_KEY=...

Usage
-----
  python3 api_smoke_test.py

Optional:
  KNOWUNITY_BASE_URL=https://knowunity-agent-olympics-2026-api.vercel.app
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


def _load_dotenv(path: str = ".env") -> None:
    """Tiny .env loader (avoids external deps).

    Supports simple KEY=VALUE lines; ignores blanks and comments.
    """

    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)


@dataclass
class CallResult:
    name: str
    method: str
    path: str
    status: Optional[int]
    ok: bool
    response_preview: str
    response_json: Optional[Any] = None


class ApiClient:
    def __init__(self, base_url: str, x_api_key: str, timeout_s: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

        # Public endpoints
        self.x_api_key = x_api_key

        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def request(
        self,
        *,
        name: str,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> CallResult:
        url = self._url(path)
        try:
            r = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_body,
                params=params,
                timeout=self.timeout_s,
            )
            resp_json: Optional[Any] = None
            ctype = (r.headers.get("content-type") or "").lower()
            if "application/json" in ctype:
                try:
                    resp_json = r.json()
                except Exception:
                    resp_json = None

            # Keep preview short for logging, but preserve full JSON separately for dependent calls.
            preview = r.text
            if len(preview) > 500:
                preview = preview[:500] + "..."
            return CallResult(
                name=name,
                method=method,
                path=path,
                status=r.status_code,
                ok=r.ok,
                response_preview=preview,
                response_json=resp_json,
            )
        except Exception as e:
            return CallResult(name=name, method=method, path=path, status=None, ok=False, response_preview=str(e), response_json=None)

    def public_headers(self) -> Dict[str, str]:
        return {"x-api-key": self.x_api_key, "content-type": "application/json"}


def _j(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def main() -> int:
    _load_dotenv()
    base_url = os.getenv("KNOWUNITY_BASE_URL", "https://knowunity-agent-olympics-2026-api.vercel.app")
    x_api_key = os.getenv("KNOWUNITY_X_API_KEY", "").strip()

    if not x_api_key:
        print("Missing env vars. Create a .env file with:")
        print("  KNOWUNITY_X_API_KEY=...")
        return 2

    client = ApiClient(base_url=base_url, x_api_key=x_api_key)
    results: list[CallResult] = []

    # --- Basic endpoints ---
    results.append(client.request(name="root", method="GET", path="/"))
    results.append(client.request(name="health", method="GET", path="/health"))

    # --- Public data endpoints ---
    students = client.request(name="list_students", method="GET", path="/students")
    results.append(students)
    subjects = client.request(name="list_subjects", method="GET", path="/subjects")
    results.append(subjects)
    topics = client.request(name="list_topics", method="GET", path="/topics")
    results.append(topics)

    # For dependent calls we try to extract IDs.
    student_id = None
    topic_id = None
    if students.ok:
        try:
            data = students.response_json
            if isinstance(data, dict) and data.get("students"):
                student_id = data["students"][0].get("id")
        except Exception:
            pass
    if topics.ok:
        try:
            data = topics.response_json
            if isinstance(data, dict) and data.get("topics"):
                topic_id = data["topics"][0].get("id")
        except Exception:
            pass

    dummy_uuid = "00000000-0000-0000-0000-000000000000"
    results.append(
        client.request(
            name="get_student_topics",
            method="GET",
            path=f"/students/{student_id or dummy_uuid}/topics",
        )
    )

    # --- Interact endpoints (require x-api-key) ---
    conversation_id = None
    start = client.request(
        name="interact_start",
        method="POST",
        path="/interact/start",
        headers=client.public_headers(),
        json_body={"student_id": student_id or dummy_uuid, "topic_id": topic_id or dummy_uuid},
    )
    results.append(start)
    if start.ok:
        try:
            conversation_id = (start.response_json or {}).get("conversation_id")
        except Exception:
            pass

    results.append(
        client.request(
            name="interact",
            method="POST",
            path="/interact",
            headers=client.public_headers(),
            json_body={
                "conversation_id": conversation_id or dummy_uuid,
                "tutor_message": "Hi! This is an API smoke test.",
            },
        )
    )

    # --- Print summary ---
    max_name = max(len(r.name) for r in results)
    max_mp = max(len(f"{r.method} {r.path}") for r in results)
    ok_count = 0
    print("\n=== API Smoke Test Results ===")
    for r in results:
        ok = "OK" if r.ok else "FAIL"
        if r.ok:
            ok_count += 1
        status = str(r.status) if r.status is not None else "-"
        print(f"{ok:4}  {status:>3}  {r.name:<{max_name}}  {r.method} {r.path:<{max_mp-len(r.method)-1}}  {r.response_preview}")
    print(f"\nSuccess: {ok_count}/{len(results)} calls")

    # Return non-zero if anything failed
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
