def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_end_to_end_evaluation_and_review(client):
    project = client.post("/api/projects", json={"name": "Quality", "description": ""}).json()
    dataset = client.post("/api/datasets", json={"project_id": project["id"], "name": "Meds", "description": ""}).json()
    case = client.post(f'/api/datasets/{dataset["id"]}/cases', json={"input": "Start metformin", "expected_output": {"medications": ["metformin"]}, "tags": ["demo"]})
    assert case.status_code == 201
    run = client.post("/api/experiments", json={"dataset_id": dataset["id"], "name": "v1", "model": "rules-v1"})
    assert run.status_code == 201
    result = client.get(f'/api/experiments/{run.json()["id"]}/results').json()["items"][0]
    assert result["passed"] is True
    assert result["metric_details"]["f1"] == 1
    assert result["provider_request_id"].startswith("local_")
    detail = client.get(f'/api/experiments/{run.json()["id"]}').json()
    assert detail["summary"]["quality_gate"]["passed"] is True
    assert detail["summary"]["p95_latency_ms"] > 0
    assert detail["run"]["progress_completed"] == 1
    assert detail["run"]["progress_total"] == 1
    review = client.put(f'/api/results/{result["id"]}/review', json={"decision": "accepted", "comment": "Correct"})
    assert review.json()["decision"] == "accepted"


def test_import_rejects_invalid_json(client):
    project = client.post("/api/projects", json={"name": "Quality", "description": ""}).json()
    dataset = client.post("/api/datasets", json={"project_id": project["id"], "name": "Meds", "description": ""}).json()
    response = client.post(f'/api/datasets/{dataset["id"]}/import', files={"file": ("bad.json", b"{}", "application/json")})
    assert response.status_code == 422


def test_validation_errors_use_structured_envelope(client):
    response = client.post("/api/projects", json={"name": "", "description": ""})

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "Request validation failed"
    assert payload["error"]["details"][0]["field"] == "name"


def test_openapi_contract_has_typed_success_responses(client):
    schema = client.get("/openapi.json").json()
    missing = []
    for path, methods in schema["paths"].items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            success = next(
                (response for code, response in operation["responses"].items() if code.startswith("2")),
                None,
            )
            if success is None:
                missing.append(f"{method.upper()} {path}: no success response")
                continue
            if "204" not in operation["responses"] and not success.get("content", {}).get("application/json", {}).get("schema"):
                missing.append(f"{method.upper()} {path}: no JSON response schema")
    assert missing == []
