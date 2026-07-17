import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createBin } from "../api";

export default function HomePage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleCreate() {
    setLoading(true);
    setError(null);
    try {
      const bin = await createBin();
      navigate(`/b/${bin.id}`);
    } catch {
      setError("Could not create bin. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-4 bg-gray-50">
      <h1 className="text-3xl font-bold">Webhook Inspector</h1>
      <p className="text-gray-600">
        Create a bin, point your webhooks at it, watch requests arrive.
      </p>
      <button
        onClick={handleCreate}
        disabled={loading}
        className="px-6 py-3 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? "Creating…" : "Create a bin"}
      </button>
      {error && <p className="text-red-600">{error}</p>}
    </main>
  );
}
