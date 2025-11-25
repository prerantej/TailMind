// src/pages/Drafts.jsx
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatDate } from "../lib/api";

export default function Drafts({ onOpenDraft }) {
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);

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

  function toggleSelect(id) {
    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id]
    );
  }

  async function deleteSelected() {
    if (selectedIds.length === 0) return;

    const ok = window.confirm(
      `Delete ${selectedIds.length} draft(s)? This cannot be undone.`
    );
    if (!ok) return;

    try {
      await api.delete("/drafts/batch-delete", {
        data: { ids: selectedIds },
      });
      // Remove locally
      setDrafts((prev) => prev.filter((d) => !selectedIds.includes(d.id)));
      setSelectedIds([]);
    } catch (e) {
      console.error("Batch delete failed", e);
      alert("Failed to delete drafts.");
    }
  }

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Drafts</h3>

        <div className="text-sm text-neutral-400">
          {drafts.length} drafts
        </div>
      </div>

      {/* Delete Selected Button */}
      {selectedIds.length > 0 && (
        <button
          onClick={deleteSelected}
          className="mb-3 px-3 py-1 rounded-md border text-sm text-red-400 border-red-500/30 hover:bg-red-900/20"
          style={{ borderWidth: "1px" }}   // thinner border
        >
          Delete Selected ({selectedIds.length})
        </button>
      )}

      <div className="space-y-3">
        {loading && (
          <div className="text-sm text-neutral-400">Loading...</div>
        )}

        {!loading && drafts.length === 0 && (
          <div className="text-sm text-neutral-500">
            No drafts saved yet.
          </div>
        )}

        {drafts.map((d) => (
          <div
            key={d.id}
            className="p-3 rounded-xl border border-transparent hover:border-neutral-800 hover:shadow-sm flex justify-between items-center"
          >
            <div className="flex items-start gap-3">
              <div>
              {/* Checkbox */}
              <input
                type="checkbox"
                checked={selectedIds.includes(d.id)}
                onChange={() => toggleSelect(d.id)}
                className="w-4 h-4 accent-indigo-500"
              />
              </div>

              <div>
                <div className="font-medium">
                  {d.subject || "(No Subject)"}
                </div>
                <div className="text-xs text-neutral-500">
                  {formatDate(d.created_at)}
                </div>
              </div>
            </div>

            <div className="flex gap-2 items-center">
              <button
                onClick={() => onOpenDraft && onOpenDraft(d.id)}
                className="px-3 py-1 rounded-md border text-sm border-neutral-700 hover:bg-neutral-800"
                style={{ borderWidth: "1px" }}   // thinner border
              >
                Open
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
