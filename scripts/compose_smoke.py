"""Black-box smoke test for the complete Docker Compose stack."""

from __future__ import annotations

import json
import time
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen


API = "http://127.0.0.1:8000"
FRONTEND = "http://127.0.0.1:3000"


def wait_for(url: str, timeout: int = 180) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=5) as response:
                if 200 <= response.status < 400:
                    return
        # Containers can accept a TCP connection a moment before the server is
        # ready, then reset it while migrations/startup finish. Treat that as
        # transient during the bounded readiness window.
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
        time.sleep(2)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def request(opener, method: str, path: str, payload: dict | None = None):
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = Request(f"{API}{path}", data=body, headers=headers, method=method)
    with opener.open(req, timeout=10) as response:
        data = response.read()
        return json.loads(data) if data else None


def main() -> None:
    wait_for(f"{API}/health")
    wait_for(FRONTEND)

    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    user = request(
        opener,
        "POST",
        "/api/auth/login",
        {"email": "demo@evalforge.dev", "password": "demo1234"},
    )
    assert user["email"] == "demo@evalforge.dev"

    projects = request(opener, "GET", "/api/projects")
    assert projects and projects[0]["name"] == "Clinical NLP Quality"
    datasets = request(opener, "GET", f"/api/datasets?project_id={projects[0]['id']}")
    assert datasets["total"] >= 1
    dataset = datasets["items"][0]
    assert dataset["case_count"] >= 1

    run = request(
        opener,
        "POST",
        "/api/experiments",
        {
            "dataset_id": dataset["id"],
            "name": "Compose smoke evaluation",
            "provider": "deterministic",
            "model": "rules-v2",
            "prompt_version": "compose-smoke-v1",
            "prompt": "Extract medications as JSON",
        },
    )

    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        detail = request(opener, "GET", f"/api/experiments/{run['id']}")
        status = detail["run"]["status"]
        if status == "completed":
            assert detail["summary"]["total"] == dataset["case_count"]
            assert detail["run"]["progress_completed"] == dataset["case_count"]
            assert detail["summary"]["quality_gate"]["passed"] is True
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "database": "postgresql",
                        "queue": "redis-rq",
                        "worker_run_id": run["id"],
                        "evaluated_cases": detail["summary"]["total"],
                        "frontend": "reachable",
                    },
                    indent=2,
                )
            )
            return
        if status in {"failed", "cancelled"}:
            raise RuntimeError(f"Worker run ended with status={status}: {detail['run']['error']}")
        time.sleep(2)
    raise RuntimeError(f"Timed out waiting for worker run {run['id']}")


if __name__ == "__main__":
    main()
