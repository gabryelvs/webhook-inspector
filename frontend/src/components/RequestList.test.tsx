import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import RequestList from "./RequestList";
import type { CapturedRequest } from "../types";

function makeRequest(overrides: Partial<CapturedRequest> = {}): CapturedRequest {
  return {
    id: "req1",
    bin_id: "bin1",
    method: "POST",
    path: "/hook",
    headers: {},
    query: {},
    body: "",
    content_type: null,
    source_ip: null,
    truncated: false,
    received_at: "2026-07-15T12:00:00Z",
    ...overrides,
  };
}

describe("RequestList", () => {
  it("shows empty state when no requests", () => {
    render(<RequestList requests={[]} selectedId={null} onSelect={() => {}} />);
    expect(screen.getByText(/waiting for requests/i)).toBeInTheDocument();
  });

  it("renders method and path per row", () => {
    render(
      <RequestList
        requests={[makeRequest(), makeRequest({ id: "req2", method: "GET", path: "/ping" })]}
        selectedId={null}
        onSelect={() => {}}
      />
    );
    expect(screen.getByText("POST")).toBeInTheDocument();
    expect(screen.getByText("/ping")).toBeInTheDocument();
  });

  it("calls onSelect with request id on click", () => {
    const onSelect = vi.fn();
    render(
      <RequestList requests={[makeRequest()]} selectedId={null} onSelect={onSelect} />
    );
    fireEvent.click(screen.getByText("/hook"));
    expect(onSelect).toHaveBeenCalledWith("req1");
  });
});
