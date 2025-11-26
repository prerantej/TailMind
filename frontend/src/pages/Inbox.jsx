// src/pages/Inbox.jsx
import React, { useEffect, useState } from "react";
import { api, formatDate } from "../lib/api";
import { useNavigate } from "react-router-dom";

/**
 * Inbox using shadcn-style primitives (Card-like layout, Checkbox, Badge)
 * Category color mapping:
 *  - Important => red
 *  - To-Do => yellow
 *  - Newsletter => green
 *  - Spam => gray
 */
function categoryClasses(category) {
  const cat = (category || "").toLowerCase().trim();
  switch (cat) {
    case "important":
      return "bg-red-600 text-white";
    case "to-do":
    case "to_do":
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
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchInbox();
    // eslint-disable-next-line
  }, [refreshFlag]);

  async function fetchInbox() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/inbox");
      console.log("📧 Inbox response:", res.data);
      
      // Handle both response formats: {emails: [...]} or direct array
      const emailList = res.data.emails || res.data || [];
      setEmails(emailList);
      
      if (emailList.length === 0) {
        console.log("⚠️ No emails found in database");
      }
    } catch (e) {
      console.error("❌ Error fetching inbox:", e);
      setError(e.response?.data?.detail || e.message || "Failed to load emails");
      setEmails([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadMockInbox() {
    setLoading(true);
    setError(null);
    try {
      console.log("📥 Loading mock emails...");
      const res = await api.post("/inbox/load");
      console.log("✅ Mock load response:", res.data);
      
      // Wait a moment for processing to complete
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Refresh inbox
      await fetchInbox();
    } catch (e) {
      console.error("❌ Error loading mock emails:", e);
      setError(e.response?.data?.detail || e.message || "Failed to load mock emails");
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
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Inbox</h3>
        <div className="flex gap-2">
          <button 
            onClick={loadMockInbox} 
            disabled={loading}
            className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Loading..." : "Load Mock"}
          </button>
          <button 
            onClick={fetchInbox} 
            disabled={loading}
            className="px-3 py-1 border border-neutral-800 hover:bg-neutral-900 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-800 rounded-lg text-red-400 text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Email List */}
      <div className="overflow-auto space-y-3 max-h-[80vh]">
        {loading && (
          <div className="text-sm text-neutral-400 flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-neutral-400 border-t-transparent"></div>
            Loading emails...
          </div>
        )}
        
        {!loading && emails.length === 0 && !error && (
          <div className="text-center py-8">
            <p className="text-neutral-500 mb-4">📭 No emails in inbox</p>
            <p className="text-sm text-neutral-600">Click "Load Mock" to populate with sample emails</p>
          </div>
        )}

        {!loading && emails.map((e) => (
          <div 
            key={e.id} 
            className="p-3 rounded-xl border border-neutral-800 hover:border-neutral-700 hover:shadow-sm bg-neutral-900/50 flex gap-3 transition-all cursor-pointer"
            onClick={() => openEmail(e)}
          >
            <div className="flex-shrink-0 pt-1">
              <input
                type="checkbox"
                checked={!!selectedIds[e.id]}
                onChange={(evt) => {
                  evt.stopPropagation();
                  toggleSelect(e.id);
                }}
                onClick={(evt) => evt.stopPropagation()}
                className="w-4 h-4 rounded bg-neutral-800 border-neutral-700 cursor-pointer"
                aria-label={`Select email ${e.subject}`}
              />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-start mb-2">
                <div className="min-w-0 flex-1">
                  <div className="font-medium truncate text-neutral-100">{e.subject}</div>
                  <div className="text-xs text-neutral-400 truncate">{e.sender}</div>
                </div>
                <div className="text-xs text-neutral-500 ml-3 flex-shrink-0">
                  {formatDate(e.timestamp)}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {e.category && (
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${categoryClasses(e.category)}`}>
                      {e.category}
                    </span>
                  )}
                  
                  {e.tasks && (() => {
                    try {
                      const tasks = typeof e.tasks === 'string' ? JSON.parse(e.tasks) : e.tasks;
                      if (Array.isArray(tasks) && tasks.length > 0) {
                        return (
                          <span className="inline-block px-2 py-0.5 rounded-full text-xs bg-blue-600 text-white">
                            {tasks.length} task{tasks.length > 1 ? 's' : ''}
                          </span>
                        );
                      }
                    } catch {}
                    return null;
                  })()}
                </div>
                
                {e.draft && (
                  <span className="text-xs text-neutral-500">📝 Draft ready</span>
                )}
              </div>

              {/* Preview of email body */}
              <div className="mt-2 text-xs text-neutral-500 line-clamp-2">
                {e.body}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}