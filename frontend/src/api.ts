import type { Bin, CapturedRequest } from "./types";

export async function createBin(): Promise<Bin> {
  const res = await fetch("/api/bins", { method: "POST" });
  if (!res.ok) throw new Error(`createBin failed: ${res.status}`);
  return res.json();
}

export async function fetchRequests(binId: string): Promise<CapturedRequest[]> {
  const res = await fetch(`/api/bins/${binId}/requests`);
  if (!res.ok) throw new Error(`fetchRequests failed: ${res.status}`);
  return res.json();
}
