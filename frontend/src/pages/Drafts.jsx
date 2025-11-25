// src/pages/Drafts.jsx
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatDate } from "../lib/api";

/**
 * Drafts page (list of saved drafts)
 * Opens draft via onOpenDraft(draftId)
 */
export default function Drafts({ onOpenDraft }) {
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDrafts();
  }, []);

  async function fetchDrafts() {
    setLoading(true);
    try {
      const res = await api.get("/drafts");
      setDrafts(res.data || []);
    } catch (e) {
      console.error(e);
      setDrafts([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Drafts</h3>
        <div className="text-sm text-neutral-400">{drafts.length} drafts</div>
      </div>

      <div className="space-y-3">
        {loading && <div className="text-sm text-neutral-400">Loading...</div>}
        {!loading && drafts.length === 0 && <div className="text-sm text-neutral-500">No drafts saved yet.</div>}
        {drafts.map((d) => (
          <div
            key={d.id}
            className="p-3 rounded-xl border border-transparent hover:border-neutral-800 hover:shadow-sm flex justify-between items-center"
          >
            <div>
              <div className="font-medium">{d.subject || "(No Subject)"}</div>
              <div className="text-xs text-neutral-500">{formatDate(d.created_at)}</div>
            </div>

            <div>
              <button onClick={() => onOpenDraft && onOpenDraft(d.id)} className="px-3 py-1 rounded-md border text-sm">
                Open
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
