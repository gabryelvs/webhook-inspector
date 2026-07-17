import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchRequests } from "../api";
import type { CapturedRequest } from "../types";
import RequestList from "../components/RequestList";

const POLL_MS = 2000;

export default function BinPage() {
  const { binId } = useParams();
  const [requests, setRequests] = useState<CapturedRequest[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (!binId) return;
    let active = true;

    async function load() {
      try {
        const data = await fetchRequests(binId!);
        if (active) setRequests(data);
      } catch {
        // keep showing last known data; next poll retries
      }
    }

    load();
    const timer = setInterval(load, POLL_MS);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [binId]);

  const selected =
    requests.find((r) => r.id === selectedId) ?? requests[0] ?? null;
  const binUrl = `${window.location.origin}/in/${binId}`;

  return (
    <main className="h-screen flex flex-col">
      <header className="px-4 py-3 border-b bg-white flex items-center gap-3">
        <h1 className="font-bold">Webhook Inspector</h1>
        <code className="text-sm bg-gray-100 px-2 py-1 rounded select-all">
          {binUrl}
        </code>
        <button
          onClick={() => navigator.clipboard.writeText(binUrl)}
          className="text-sm text-blue-600 hover:underline"
        >
          Copy
        </button>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-96 border-r overflow-y-auto bg-white">
          <RequestList
            requests={requests}
            selectedId={selected?.id ?? null}
            onSelect={setSelectedId}
          />
        </aside>
        <section className="flex-1 overflow-y-auto bg-gray-50 p-4">
          {selected ? (
            <pre className="text-sm whitespace-pre-wrap">{selected.body || "(empty body)"}</pre>
          ) : (
            <p className="text-gray-500">No request selected.</p>
          )}
        </section>
      </div>
    </main>
  );
}
