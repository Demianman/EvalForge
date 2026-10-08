import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ReviewPage from "./page";
import { api } from "@/lib/api";

vi.mock("next/navigation", () => ({ useParams: () => ({ resultId: "17" }) }));
vi.mock("@/lib/api", () => ({ api: vi.fn() }));

const result = {
  id: 17,
  run_id: 4,
  test_case_id: 2,
  input: "Start metformin 500 mg daily",
  expected_output: { medications: ["metformin"] },
  actual_output: { medications: ["metformin"] },
  passed: true,
  score: 1,
  metric_details: { exact_match: true, schema_valid: true, precision: 1, recall: 1, f1: 1 },
  latency_ms: 3,
  cost_usd: 0,
  input_tokens: 0,
  output_tokens: 0,
  provider_request_id: "local_17",
  attempt_count: 1,
  review: null,
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><ReviewPage /></QueryClientProvider>);
}

describe("review workflow", () => {
  beforeEach(() => vi.mocked(api).mockReset());

  it("loads a result and submits a human review", async () => {
    vi.mocked(api)
      .mockResolvedValueOnce(result)
      .mockResolvedValueOnce({ decision: "rejected", comment: "Missing dose normalization" })
      .mockResolvedValueOnce({ ...result, review: { decision: "rejected", comment: "Missing dose normalization" } });

    renderPage();
    expect(await screen.findByText("Start metformin 500 mg daily")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Mark regression"));
    fireEvent.change(screen.getByLabelText("Comment"), { target: { value: "Missing dose normalization" } });
    fireEvent.click(screen.getByRole("button", { name: "Save review" }));

    await waitFor(() => expect(api).toHaveBeenCalledWith(
      "/results/17/review",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ decision: "rejected", comment: "Missing dose normalization" }),
      }),
    ));
  });

  it("shows an API error and rolls back the optimistic review", async () => {
    vi.mocked(api)
      .mockResolvedValueOnce(result)
      .mockRejectedValueOnce(new Error("Review service unavailable"))
      .mockResolvedValueOnce(result);

    renderPage();
    await screen.findByText("Start metformin 500 mg daily");
    fireEvent.click(screen.getByRole("button", { name: "Save review" }));

    expect(await screen.findByText("Review service unavailable")).toBeInTheDocument();
    expect(screen.queryByText("Review saved")).not.toBeInTheDocument();
  });
});
