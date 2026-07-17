import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RequestDetail from "./RequestDetail";
import type { CapturedRequest } from "../types";

const req: CapturedRequest = {
  id: "req1",
  bin_id: "bin1",
  method: "POST",
  path: "/hook",
  headers: { "content-type": "application/json", "x-sig": "abc123" },
  query: { source: "stripe" },
  body: '{"event":"payment.succeeded"}',
  content_type: "application/json",
  source_ip: "1.2.3.4",
  truncated: false,
  received_at: "2026-07-15T12:00:00Z",
};

describe("RequestDetail", () => {
  it("shows headers tab by default", () => {
    render(<RequestDetail request={req} />);
    expect(screen.getByText("x-sig")).toBeInTheDocument();
    expect(screen.getByText("abc123")).toBeInTheDocument();
  });

  it("pretty-prints JSON body on body tab", () => {
    render(<RequestDetail request={req} />);
    fireEvent.click(screen.getByRole("button", { name: "Body" }));
    expect(screen.getByText(/"event": "payment.succeeded"/)).toBeInTheDocument();
  });

  it("shows query params on query tab", () => {
    render(<RequestDetail request={req} />);
    fireEvent.click(screen.getByRole("button", { name: "Query" }));
    expect(screen.getByText("source")).toBeInTheDocument();
    expect(screen.getByText("stripe")).toBeInTheDocument();
  });

  it("shows truncation warning when body truncated", () => {
    render(<RequestDetail request={{ ...req, truncated: true }} />);
    fireEvent.click(screen.getByRole("button", { name: "Body" }));
    expect(screen.getByText(/truncated/i)).toBeInTheDocument();
  });
});
