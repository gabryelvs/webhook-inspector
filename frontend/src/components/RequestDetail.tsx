import { useState } from "react";
import type { CapturedRequest } from "../types";

type Tab = "headers" | "body" | "query" | "raw";
const TABS: { id: Tab; label: string }[] = [
  { id: "headers", label: "Headers" },
  { id: "body", label: "Body" },
  { id: "query", label: "Query" },
  { id: "raw", label: "Raw" },
];

function prettyBody(body: string): string {
  if (!body) return "(empty body)";
  try {
    return JSON.stringify(JSON.parse(body), null, 2);
  } catch {
    return body;
  }
}

function KeyValueTable({ data }: { data: Record<string, string> }) {
  const entries = Object.entries(data);
  if (entries.length === 0) return <p className="text-gray-500 text-sm">(none)</p>;
  return (
    <table className="text-sm w-full">
      <tbody>
        {entries.map(([k, v]) => (
          <tr key={k} className="border-b border-gray-100">
            <td className="py-1 pr-4 font-mono text-gray-600 align-top">{k}</td>
            <td className="py-1 font-mono break-all">{v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function RequestDetail({ request }: { request: CapturedRequest }) {
  const [tab, setTab] = useState<Tab>("headers");

  return (
    <div className="bg-white rounded-lg border">
      <div className="px-4 py-2 border-b text-sm text-gray-600">
        <span className="font-mono font-semibold">{request.method}</span>{" "}
        <span className="font-mono">{request.path}</span>
        {request.source_ip && <span className="ml-3">from {request.source_ip}</span>}
        <span className="ml-3">{new Date(request.received_at).toLocaleString()}</span>
      </div>
      <nav className="flex gap-1 px-2 pt-2 border-b">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 text-sm rounded-t ${
              tab === t.id
                ? "bg-gray-100 font-medium border border-b-0"
                : "text-gray-500 hover:text-gray-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <div className="p-4 overflow-x-auto">
        {tab === "headers" && <KeyValueTable data={request.headers} />}
        {tab === "query" && <KeyValueTable data={request.query} />}
        {tab === "body" && (
          <>
            {request.truncated && (
              <p className="mb-2 text-xs text-amber-700 bg-amber-50 px-2 py-1 rounded">
                Body truncated at 1 MB.
              </p>
            )}
            <pre className="text-sm font-mono whitespace-pre-wrap">
              {prettyBody(request.body)}
            </pre>
          </>
        )}
        {tab === "raw" && (
          <pre className="text-sm font-mono whitespace-pre-wrap">
            {JSON.stringify(request, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
