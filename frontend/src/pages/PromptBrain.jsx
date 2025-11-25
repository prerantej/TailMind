// src/pages/PromptBrain.jsx
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function PromptBrain() {
  const [prompts, setPrompts] = useState({});

  useEffect(() => {
    fetchPrompts();
  }, []);

  async function fetchPrompts() {
    try {
      const res = await api.get("/prompts");
      setPrompts(res.data || {});
    } catch (e) {
      console.error(e);
      setPrompts({});
    }
  }

  async function savePrompt(key) {
    try {
      const text = prompts[key] || "";
      await api.post("/prompts/update", null, { params: { key, text } });
      alert("Saved");
    } catch (e) {
      console.error(e);
      alert("Save failed");
    }
  }

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
      {["categorization", "action_extraction", "auto_reply"].map((k) => (
        <div key={k} className="mb-4">
          <label className="block text-sm font-medium text-neutral-300 mb-2">{k.replace("_", " ")}</label>
          <textarea
            rows={4}
            className="w-full bg-neutral-950 border border-neutral-800 rounded-lg p-3 text-sm text-neutral-100 focus:outline-none"
            value={prompts[k] || ""}
            onChange={(e) => setPrompts({ ...prompts, [k]: e.target.value })}
          />
          <div className="mt-2 flex justify-end">
            <button
              onClick={() => savePrompt(k)}
              className="px-3 py-1 rounded-md bg-indigo-600 text-white text-sm"
            >
              Save
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
