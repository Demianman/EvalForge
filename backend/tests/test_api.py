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


def test_rag_document_ingestion_is_idempotent_and_evaluation_is_cited(client):
    project = client.post("/api/projects", json={"name": "RAG Quality", "description": ""}).json()
    content = (
        "Metformin is commonly used to manage type 2 diabetes and should be reviewed with renal function. "
        "Blood pressure treatment may include lisinopril with appropriate monitoring for potassium and kidney function. "
        "Synthetic clinical guidance is educational only and is not medical advice."
    )
    payload = {"project_id": project["id"], "title": "Synthetic medication guide", "source_uri": "fixture://medication-guide", "content": content, "chunk_size": 20, "chunk_overlap": 4}
    first = client.post("/api/rag/documents", json=payload)
    second = client.post("/api/rag/documents", json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]
    assert len(client.get(f'/api/rag/documents?project_id={project["id"]}').json()) == 1

    chunks = client.get(f'/api/rag/documents/{first.json()["id"]}/chunks').json()
    assert len(chunks) >= 2
    expected = next(chunk["id"] for chunk in chunks if "Metformin" in chunk["content"])
    evaluation = client.post("/api/rag/evaluations", json={
        "project_id": project["id"],
        "name": "Hybrid retrieval candidate",
        "queries": [{"question": "What medication is used for type 2 diabetes?", "expected_chunk_ids": [expected]}],
        "baseline": {"method": "vector", "top_k": 1},
        "candidate": {"method": "hybrid", "top_k": 2},
    })
    assert evaluation.status_code == 201
    body = evaluation.json()
    assert body["summary"]["candidate_recall_at_k"] == 1
    assert body["summary"]["quality_gate_passed"] is True
    assert body["results"][0]["candidate"]["citations"][0]["source_uri"] == "fixture://medication-guide"
    assert client.get(f'/api/rag/evaluations/{body["id"]}').json()["summary"] == body["summary"]


def test_rag_evaluation_rejects_cross_project_expected_chunks(client):
    first_project = client.post("/api/projects", json={"name": "First", "description": ""}).json()
    second_project = client.post("/api/projects", json={"name": "Second", "description": ""}).json()
    document = client.post("/api/rag/documents", json={"project_id": first_project["id"], "title": "Fixture", "content": "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty", "chunk_size": 20, "chunk_overlap": 0}).json()
    chunk_id = client.get(f'/api/rag/documents/{document["id"]}/chunks').json()[0]["id"]
    response = client.post("/api/rag/evaluations", json={"project_id": second_project["id"], "name": "Invalid", "queries": [{"question": "What is present?", "expected_chunk_ids": [chunk_id]}], "baseline": {"method": "vector", "top_k": 1}, "candidate": {"method": "hybrid", "top_k": 1}})
    assert response.status_code == 409 or response.status_code == 422
