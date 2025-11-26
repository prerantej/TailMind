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
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!id) return;
    fetchDraft();
  }, [id]);

  async function fetchDraft() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/draft/${id}`);
      console.log("📝 Draft detail response:", res.data);
      
      // Handle response format: {draft: {...}, email: {...}}
      setDraft(res.data?.draft || null);
      setEmail(res.data?.email || null);
    } catch (e) {
      console.error("❌ Failed to load draft:", e);
      setError(e.response?.data?.detail || e.message || "Failed to load draft");
      setDraft(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    const ok = window.confirm("Delete this draft? This action cannot be undone.");
    if (!ok) return;
    
    try {
      const res = await api.delete(`/draft/${id}`);
      console.log("🗑️ Delete response:", res.data);
      
      if (res.status === 200 && res.data?.status === "deleted") {
        // Navigate back to drafts list
        navigate("/drafts");
      } else {
        alert("Failed to delete draft.");
      }
    } catch (e) {
      console.error("❌ Failed to delete draft:", e);
      alert("Failed to delete draft. See console for details.");
    }
  }

  if (loading) {
    return (
      <div className="text-sm text-neutral-400 flex items-center gap-2">
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-neutral-400 border-t-transparent"></div>
        Loading draft...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
        <div className="p-3 bg-red-900/20 border border-red-800 rounded-lg text-red-400 text-sm">
          ⚠️ {error}
        </div>
        <button 
          onClick={() => navigate("/drafts")} 
          className="mt-4 px-3 py-1 border border-neutral-800 rounded-md text-sm hover:bg-neutral-900"
        >
          Back to Drafts
        </button>
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
        <div className="text-sm text-neutral-500 mb-4">Draft not found.</div>
        <button 
          onClick={() => navigate("/drafts")} 
          className="px-3 py-1 border border-neutral-800 rounded-md text-sm hover:bg-neutral-900"
        >
          Back to Drafts
        </button>
      </div>
    );
  }

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h2 className="text-xl font-semibold text-neutral-100 mb-1">
            {draft.subject || "(No Subject)"}
          </h2>
          <div className="text-xs text-neutral-500">
            {draft.created_at ? formatDate(draft.created_at) : 'Recently created'}
          </div>
        </div>
        
        <div className="flex gap-2">
          <button 
            onClick={() => navigate("/drafts")} 
            className="px-3 py-1 border border-neutral-800 rounded-md text-sm hover:bg-neutral-900 transition-colors"
          >
            Back
          </button>
          <button 
            onClick={handleDelete} 
            className="px-3 py-1 border border-red-800 rounded-md text-sm text-red-400 hover:bg-red-900/20 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Draft Body */}
      <div className="mb-6 p-4 bg-neutral-950 border border-neutral-800 rounded-lg">
        <div className="text-sm text-neutral-300 whitespace-pre-wrap leading-relaxed">
          {draft.body || '(No content)'}
        </div>
      </div>

      {/* Original Email Context */}
      {email && (
        <div className="p-4 border border-neutral-800 rounded-lg bg-neutral-950">
          <div className="text-xs text-neutral-400 mb-3 font-medium">
            📧 Original Email (Context)
          </div>
          
          <div className="mb-3">
            <div className="text-xs text-neutral-500">From</div>
            <div className="text-sm text-neutral-300">{email.sender}</div>
          </div>
          
          <div className="mb-3">
            <div className="text-xs text-neutral-500">Subject</div>
            <div className="font-medium text-neutral-100">{email.subject}</div>
          </div>
          
          <div className="text-xs text-neutral-500 mb-1">Message</div>
          <div className="text-sm text-neutral-300 whitespace-pre-wrap leading-relaxed">
            {email.body}
          </div>
        </div>
      )}
    </div>
  );
}