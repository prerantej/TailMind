// src/components/ChatBox.jsx
import React, { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import ToggleButton from "./ToggleButton";

/**
 * ChatBox (desktop) with an internal top-right toggle button.
 * Props:
 *  - emailId
 *  - onGenerateDraft (callback to refresh parent when a draft is saved)
 *  - onToggleOpen (callback to collapse the panel — parent can toggle)
 *  - isOpen (optional boolean; if provided, component will use this as source of truth)
 */
export default function ChatBox({ emailId, onGenerateDraft, onToggleOpen, isOpen }) {
  const [currentEmail, setCurrentEmail] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [draftEditorOpen, setDraftEditorOpen] = useState(false);
  const [draftSubject, setDraftSubject] = useState("");
  const [draftBody, setDraftBody] = useState("");
  const [draftEmailId, setDraftEmailId] = useState(null);
  const scrollRef = useRef();

  // Local open fallback if parent doesn't control state
  const [localOpen, setLocalOpen] = useState(true);
  const openState = typeof isOpen === "boolean" ? isOpen : localOpen;

  useEffect(() => {
    setMessages([]);
    setInput("");
    setCurrentEmail(null);

    if (!emailId) return;
    (async () => {
      try {
        const res = await api.get(`/email/${emailId}`);
        const emailObj = res.data?.email ?? res.data;
        setCurrentEmail(emailObj || null);
      } catch (err) {
        console.error("Failed to load email in ChatBox", err);
        setCurrentEmail(null);
      }
    })();
  }, [emailId]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, draftEditorOpen]);

  function handleToggleClick() {
    // If parent provided a callback, call it (toggle intent)
    if (onToggleOpen) onToggleOpen();
    // Update local fallback state so component behaves standalone
    setLocalOpen((v) => !v);
  }

  async function sendQuery() {
    if (!input.trim()) return;
    const userText = input.trim();
    setMessages((m) => [...m, { role: "user", text: userText }]);
    setInput("");
    setLoading(true);

    try {
      const payload = {
        email_id: emailId || null,
        email_subject: currentEmail?.subject || null,
        email_body: currentEmail?.body || null,
        query: userText,
      };
      const res = await api.post("/agent/chat", payload);
      const reply = res.data?.reply || "No reply.";
      setMessages((m) => [...m, { role: "assistant", text: reply }]);
    } catch (err) {
      console.error(err);
      setMessages((m) => [...m, { role: "assistant", text: "Error: could not reach agent." }]);
    } finally {
      setLoading(false);
    }
  }

  async function generateDraft() {
    if (!emailId) {
      alert("Select an email first to generate a draft for it.");
      return;
    }
    setLoading(true);
    try {
      const res = await api.post("/agent/draft", {
        email_id: emailId,
        email_subject: currentEmail?.subject,
        email_body: currentEmail?.body,
        tone: "friendly",
        save: false, // explicit preview-only
      });
      const draft = res.data?.draft;
      if (draft) {
        setDraftEmailId(draft.email_id || emailId);
        setDraftSubject(draft.subject || "");
        setDraftBody(draft.body || "");
        setDraftEditorOpen(true);
        setMessages((m) => [...m, { role: "assistant", text: `Draft generated — preview and save when ready.` }]);
      } else {
        setMessages((m) => [...m, { role: "assistant", text: "Draft generation failed." }]);
      }
    } catch (e) {
      console.error(e);
      setMessages((m) => [...m, { role: "assistant", text: "Error generating draft." }]);
    } finally {
      setLoading(false);
    }
  }

  async function saveDraft() {
    if (!draftEmailId) {
      alert("No draft to save.");
      return;
    }
    setLoading(true);
    try {
      const payload = { email_id: draftEmailId, subject: draftSubject, body: draftBody };
      const res = await api.post("/draft/save", payload);
      if (res.data?.status === "saved") {
        const saved = res.data.draft;
        setMessages((m) => [...m, { role: "assistant", text: `Draft saved (id=${saved.id}).` }]);
        setDraftEditorOpen(false);
        if (onGenerateDraft) onGenerateDraft();
      } else {
        setMessages((m) => [...m, { role: "assistant", text: "Failed to save draft." }]);
      }
    } catch (e) {
      console.error(e);
      setMessages((m) => [...m, { role: "assistant", text: "Error saving draft." }]);
    } finally {
      setLoading(false);
    }
  }

  function closeDraftEditor() {
    setDraftEditorOpen(false);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header: title + toggle button in top-right */}
      <div className="mb-3 flex items-start justify-between">
        <div>
          <div className="text-lg font-semibold mb-1">Agent Chat</div>
          <div className="text-sm text-neutral-400">
            {currentEmail ? `Context: ${currentEmail.subject}` : "Ask about selected email or the inbox"}
          </div>
        </div>

        {/* Toggle button */}
        <div className="ml-4">
          <ToggleButton
            icon={<span className="text-xl select-none">{openState ? ">" : "<"}</span>}
            onClick={handleToggleClick}
            glow={!openState} // glow when collapsed
            title={openState ? "Collapse chat" : "Open chat"}
            size={44}
          />
        </div>
      </div>

      {/* Message area */}
      <div ref={scrollRef} className="flex-1 overflow-auto mb-3 space-y-2 pr-2">
        {messages.length === 0 && <div className="text-sm text-neutral-400">No messages yet. Ask the agent anything.</div>}
        {messages.map((m, i) => (
          <div key={i} className={`mb-2 ${m.role === "user" ? "flex justify-end" : "flex justify-start"}`}>
            <div className={`inline-block p-2 rounded-md max-w-[80%] ${m.role === "user" ? "bg-indigo-600 text-white" : "bg-neutral-800 text-neutral-200"}`}>
              {m.text}
            </div>
          </div>
        ))}
      </div>

      {/* Input row */}
      <div className="flex gap-2 items-center">
        <button onClick={generateDraft} disabled={loading} className="px-3 py-2 rounded-3xl bg-custom-green text-xs">
          Generate Draft
        </button>

        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendQuery()}
          placeholder={emailId ? "Ask about selected email..." : "Ask about inbox..."}
          className="flex-1 px-4 py-2 rounded-full bg-neutral-900 border border-neutral-800 text-sm"
        />

        <button onClick={sendQuery} disabled={loading} className="px-4 py-2 rounded-full bg-indigo-600 text-white text-sm">
          {loading ? "…" : "Send"}
        </button>
      </div>

      {/* Draft Editor Dialog */}
      {draftEditorOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4 w-full max-w-2xl">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-semibold">Draft Preview</h3>
              <button onClick={closeDraftEditor} className="text-sm text-neutral-400">Close</button>
            </div>

            <div className="mb-3">
              <label className="block text-sm text-neutral-400 mb-1">Subject</label>
              <input value={draftSubject} onChange={(e) => setDraftSubject(e.target.value)} className="w-full px-3 py-2 rounded-md bg-neutral-950 border border-neutral-800 text-sm" />
            </div>

            <div className="mb-3">
              <label className="block text-sm text-neutral-400 mb-1">Body</label>
              <textarea rows={10} value={draftBody} onChange={(e) => setDraftBody(e.target.value)} className="w-full px-3 py-2 rounded-md bg-neutral-950 border border-neutral-800 text-sm whitespace-pre-wrap" />
            </div>

            <div className="flex justify-end gap-2">
              <button onClick={closeDraftEditor} className="px-3 py-2 border rounded-md">Cancel</button>
              <button onClick={saveDraft} className="px-3 py-2 bg-indigo-600 text-white rounded-md">{loading ? "Saving..." : "Save Draft"}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------- Mobile floating drawer ---------- */

function MobileChatStandalone({ emailId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMessages([]);
    setInput("");
  }, [emailId]);

  async function sendQuery() {
    if (!input.trim()) return;
    const text = input.trim();
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.post("/agent/chat", { email_id: emailId || null, query: text });
      const reply = res.data?.reply || "No reply.";
      setMessages((m) => [...m, { role: "assistant", text: reply }]);
    } catch (e) {
      console.error(e);
      setMessages((m) => [...m, { role: "assistant", text: "Error: could not reach agent." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-auto mb-3 space-y-2 pr-2">
        {messages.length === 0 && <div className="text-sm text-neutral-400">No messages yet.</div>}
        {messages.map((m, i) => (
          <div key={i} className={`mb-2 ${m.role === "user" ? "flex justify-end" : "flex justify-start"}`}>
            <div className={`inline-block p-2 rounded-md max-w-[80%] ${m.role === "user" ? "bg-indigo-600 text-white" : "bg-neutral-800 text-neutral-200"}`}>
              {m.text}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 items-center">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendQuery()}
          placeholder={emailId ? "Ask about selected email..." : "Ask about inbox..."}
          className="flex-1 px-4 py-2 rounded-full bg-neutral-900 border border-neutral-800 text-sm"
        />
        <button onClick={sendQuery} disabled={loading} className="px-4 py-2 rounded-full bg-indigo-600 text-white text-sm">
          {loading ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}

export function MobileFloatingWrapper({ emailId, onGenerateDraft }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="p-3 rounded-full bg-indigo-600 shadow-lg text-white"
        aria-label="Open chat"
      >
        Chat
      </button>

      {open && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-end">
          <div className="w-full bg-neutral-900 border-t border-neutral-800 rounded-t-2xl p-4 h-3/4">
            <div className="flex justify-between items-center mb-3">
              <div className="text-lg font-semibold">Agent Chat</div>
              <button onClick={() => setOpen(false)} className="text-sm text-neutral-400">Close</button>
            </div>

            <div className="h-full overflow-auto">
              <MobileChatStandalone emailId={emailId} />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
