// src/pages/Inbox.jsx
import React, { useEffect, useState } from "react";
import { api, formatDate } from "../lib/api";
import { useNavigate } from "react-router-dom";

/**
 * Inbox using shadcn-style primitives (Card-like layout, Checkbox, Badge)
 * Category color mapping:
 *  - important => red
 *  - to_do => yellow
 *  - newsletter => green
 *  - spam => gray
 */
function categoryClasses(category) {
  switch ((category || "").toLowerCase()) {
    case "important":
      return "bg-red-600 text-white";
    case "to_do":
    case "to-do":
    case "todo":
      return "bg-yellow-500 text-neutral-900";
    case "newsletter":
      return "bg-green-600 text-white";
    case "spam":
      return "bg-neutral-600 text-white";
    default:
      return "bg-neutral-800 text-neutral-200";
  }
}

export default function Inbox({ onSelectEmail, refreshFlag }) {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    fetchInbox();
    // eslint-disable-next-line
  }, [refreshFlag]);

  async function fetchInbox() {
    setLoading(true);
    try {
      const res = await api.get("/inbox");
      setEmails(res.data || []);
    } catch (e) {
      console.error(e);
      setEmails([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadMockInbox() {
    setLoading(true);
    try {
      await api.post("/inbox/load");
      await fetchInbox();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  function toggleSelect(id) {
    setSelectedIds((prev) => {
      const copy = { ...prev };
      if (copy[id]) delete copy[id];
      else copy[id] = true;
      return copy;
    });
  }

  function openEmail(e) {
    onSelectEmail && onSelectEmail(e.id);
    navigate(`/email/${e.id}`);
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Inbox</h3>
        <div className="flex gap-2">
          <button onClick={loadMockInbox} className="px-3 py-1 bg-indigo-600 text-white rounded-md text-sm">Load Mock</button>
          <button onClick={fetchInbox} className="px-3 py-1 border border-neutral-800 rounded-md text-sm">Refresh</button>
        </div>
      </div>

      <div className="overflow-auto space-y-3 max-h-[80vh]">
        {loading && <div className="text-sm text-neutral-400">Loading...</div>}
        {!loading && emails.length === 0 && <div className="text-sm text-neutral-500">No emails. Click Load Mock.</div>}

        {emails.map((e) => (
          <div key={e.id} className="p-3 rounded-xl border border-transparent hover:border-neutral-800 hover:shadow-sm flex gap-3">
            <div className="flex-shrink-0">
              <input
                type="checkbox"
                checked={!!selectedIds[e.id]}
                onChange={() => toggleSelect(e.id)}
                className="w-4 h-4 rounded bg-neutral-800 border-neutral-700"
                aria-label={`Select email ${e.subject}`}
              />
            </div>

            <div className="flex-1 min-w-0" onClick={() => openEmail(e)} role="button" tabIndex={0}>
              <div className="flex justify-between items-start">
                <div className="min-w-0">
                  <div className="font-medium truncate">{e.subject}</div>
                  <div className="text-xs text-neutral-400 truncate">{e.sender}</div>
                </div>
                <div className="text-xs text-neutral-500 ml-3">{formatDate(e.timestamp)}</div>
              </div>

              <div className="mt-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs ${categoryClasses(e.category)}`}>
                    {e.category || "Uncategorized"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
