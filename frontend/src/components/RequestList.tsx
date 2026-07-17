import type { CapturedRequest } from "../types";

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-green-100 text-green-800",
  POST: "bg-blue-100 text-blue-800",
  PUT: "bg-yellow-100 text-yellow-800",
  PATCH: "bg-orange-100 text-orange-800",
  DELETE: "bg-red-100 text-red-800",
};

interface Props {
  requests: CapturedRequest[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function RequestList({ requests, selectedId, onSelect }: Props) {
  if (requests.length === 0) {
    return (
      <p className="p-4 text-gray-500 text-sm">
        Waiting for requests… send one to your bin URL.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-gray-200">
      {requests.map((r) => (
        <li
          key={r.id}
          onClick={() => onSelect(r.id)}
          className={`flex items-center gap-3 px-4 py-2 cursor-pointer hover:bg-gray-100 ${
            r.id === selectedId ? "bg-blue-50" : ""
          }`}
        >
          <span
            className={`text-xs font-mono font-semibold px-2 py-0.5 rounded ${
              METHOD_COLORS[r.method] ?? "bg-gray-100 text-gray-800"
            }`}
          >
            {r.method}
          </span>
          <span className="truncate font-mono text-sm">{r.path}</span>
          <span className="ml-auto text-xs text-gray-400">
            {new Date(r.received_at).toLocaleTimeString()}
          </span>
        </li>
      ))}
    </ul>
  );
}
