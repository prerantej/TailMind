// src/pages/DraftDetail.jsx
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { formatDate } from "../lib/api";

export default function DraftDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [draft, setDraft] = useState(null);
  const [email, setEmail] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetchDraft();
  }, [id]);

  async function fetchDraft() {
    setLoading(true);
    try {
      const res = await api.get(`/draft/${id}`);
      setDraft(res.data?.draft ?? null);
      setEmail(res.data?.email ?? null);
    } catch (e) {
      console.error("Failed to load draft", e);
      setDraft(null);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="text-sm text-neutral-400">Loading draft...</div>;
  if (!draft) return <div className="text-sm text-neutral-500">Draft not found.</div>;

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold">{draft.subject || "(No Subject)"}</h2>
          <div className="text-xs text-neutral-500">{formatDate(draft.created_at)}</div>
        </div>
        <div className="flex gap-2">
          {/* Optionally: go back to drafts list */}
          <button onClick={() => navigate(-1)} className="px-3 py-1 border rounded-md text-sm">Back</button>
          {/* Optionally: open the draft in the draft editor / chatbox — customize as needed */}
        </div>
      </div>

      <div className="prose max-w-none text-sm whitespace-pre-wrap">{draft.body}</div>

      {email && (
        <div className="mt-6 p-4 border border-neutral-800 rounded-md bg-neutral-950">
          <div className="text-xs text-neutral-400 mb-2">Original email (context)</div>
          <div className="font-medium">{email.subject}</div>
          <div className="text-sm text-neutral-300 mt-2 whitespace-pre-wrap">{email.body}</div>
        </div>
      )}
    </div>
  );
}
