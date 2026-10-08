import hashlib
import re
from dataclasses import dataclass
from typing import Protocol

KNOWN_DRUGS = ["metformin", "lisinopril", "atorvastatin", "amoxicillin", "insulin", "aspirin"]


@dataclass(frozen=True)
class ProviderResult:
    output: dict
    latency_ms: int
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    request_id: str | None = None


class EvaluationProvider(Protocol):
    name: str

    def evaluate(self, text: str, model: str, prompt: str = "") -> ProviderResult: ...


class DeterministicProvider:
    """Stable, free provider used by local demos and CI."""

    name = "deterministic"

    def evaluate(self, text: str, model: str, prompt: str = "") -> ProviderResult:
        medications = [drug for drug in KNOWN_DRUGS if re.search(rf"\b{drug}\b", text.lower())]
        if model == "rules-v2":
            medications = sorted(set(medications))
        digest = hashlib.sha256(f"{model}:{prompt}:{text}".encode()).hexdigest()
        return ProviderResult(
            output={"medications": medications},
            latency_ms=18 + int(digest[:2], 16) % 65,
            input_tokens=max(1, len(text.split())),
            output_tokens=max(1, len(medications) * 2),
            request_id=f"local_{digest[:12]}",
        )


def get_provider(name: str) -> EvaluationProvider:
    providers: dict[str, EvaluationProvider] = {"deterministic": DeterministicProvider()}
    if name not in providers:
        raise ValueError(f"Unsupported provider: {name}")
    return providers[name]


def score_entity_extraction(actual: dict, expected: dict) -> dict[str, float | bool]:
    actual_items = {str(x).casefold() for x in actual.get("medications", [])}
    expected_items = {str(x).casefold() for x in expected.get("medications", [])}
    true_positive = len(actual_items & expected_items)
    precision = true_positive / len(actual_items) if actual_items else float(not expected_items)
    recall = true_positive / len(expected_items) if expected_items else float(not actual_items)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"exact_match": actual == expected, "schema_valid": isinstance(actual.get("medications"), list), "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def percentile(values: list[int], quantile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int((len(ordered) - 1) * quantile + 0.5)))]


def evaluate_quality_gate(*, pass_rate: float, mean_f1: float, p95_latency_ms: int) -> dict:
    checks = [
        {"name": "Pass rate ≥ 80%", "passed": pass_rate >= 0.8},
        {"name": "Mean F1 ≥ 90%", "passed": mean_f1 >= 0.9},
        {"name": "p95 latency ≤ 100 ms", "passed": p95_latency_ms <= 100},
    ]
    return {"passed": all(check["passed"] for check in checks), "checks": checks}
