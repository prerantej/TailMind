// src/pages/Drafts.jsx
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatDate } from "../lib/api";

export default function Drafts({ onOpenDraft }) {
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDrafts();
  }, []);

  async function fetchDrafts() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/drafts");
      console.log("📝 Drafts response:", res.data);
      
      // Handle response format: {drafts: [...], count: ...}
      const draftsList = res.data.drafts || res.data || [];
      
      // Ensure it's an array
      if (Array.isArray(draftsList)) {
        setDrafts(draftsList);
      } else {
        console.error("Expected array but got:", typeof draftsList, draftsList);
        setDrafts([]);
        setError("Invalid response format from server");
      }
    } catch (e) {
      console.error("❌ Error fetching drafts:", e);
      setError(e.response?.data?.detail || e.message || "Failed to load drafts");
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
    <div className="bg-neutral-900/70 border border-neutral-800 rounded-2xl p-4 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Drafts</h3>

        <div className="text-sm text-neutral-400">
          {drafts.length} draft{drafts.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-800 rounded-lg text-red-400 text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Delete Selected Button */}
      {selectedIds.length > 0 && (
        <button
          onClick={deleteSelected}
          className="mb-3 px-3 py-1 rounded-md border text-sm text-red-400 border-red-500/30 hover:bg-red-900/20 transition-colors"
          style={{ borderWidth: "1px" }}
        >
          Delete Selected ({selectedIds.length})
        </button>
      )}

      <div className="space-y-3">
        {loading && (
          <div className="text-sm text-neutral-400 flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-neutral-400 border-t-transparent"></div>
            Loading drafts...
          </div>
        )}

        {!loading && drafts.length === 0 && !error && (
          <div className="text-center py-8">
            <p className="text-neutral-500 mb-2">📝 No drafts saved yet</p>
            <p className="text-sm text-neutral-600">Generate a draft from the chat to get started</p>
          </div>
        )}

        {!loading && Array.isArray(drafts) && drafts.map((d) => (
          <div
            key={d.id}
            className="p-3 rounded-xl border border-neutral-800 hover:border-neutral-700 hover:shadow-sm bg-neutral-900/50 flex justify-between items-center transition-all"
          >
            <div className="flex items-start gap-3 flex-1">
              <div className="pt-1">
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedIds.includes(d.id)}
                  onChange={() => toggleSelect(d.id)}
                  className="w-4 h-4 rounded bg-neutral-800 border-neutral-700 cursor-pointer"
                  aria-label={`Select draft: ${d.subject || 'No subject'}`}
                />
              </div>

              <div className="flex-1 min-w-0">
                <div className="font-medium truncate text-neutral-100">
                  {d.subject || "(No Subject)"}
                </div>
                <div className="text-xs text-neutral-500 mt-1">
                  {d.created_at ? formatDate(d.created_at) : 'Recently created'}
                </div>
                {d.original_subject && (
                  <div className="text-xs text-neutral-600 mt-1 truncate">
                    Re: {d.original_subject}
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-2 items-center ml-3">
              <button
                onClick={() => onOpenDraft && onOpenDraft(d.id)}
                className="px-3 py-1 rounded-md border text-sm border-neutral-700 hover:bg-neutral-800 transition-colors"
                style={{ borderWidth: "1px" }}
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