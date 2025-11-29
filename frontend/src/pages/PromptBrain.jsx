// src/pages/PromptBrain.jsx
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import ShinyText from "@/components/ShinyText";

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
    <div className="bg-neutral-900/70 border border-neutral-800 rounded-2xl p-4 backdrop-blur-sm">
      <div className="mb-6 p-4 bg-neutral-900 border border-neutral-800 rounded-xl">
        {/* <h2 className="text-lg font-semibold text-neutral-100 mb-2">Prompt Brain</h2>
        <p className="text-sm text-neutral-400 leading-relaxed">
          These prompts act as the <span className="text-neutral-300 font-medium">“brain”</span> of your AI email agent.
          You can customize how TailMind understands, analyzes, and responds to your emails.
          Updating a prompt immediately changes how the agent categorizes messages,
          extracts tasks, and writes replies — making the system adapt to <span className="text-neutral-300 font-medium">your personal workflow</span>.
        </p> */}

        <ShinyText 
          text="Prompt Brain" 
          disabled={false} 
          speed={3} 
          className='text-lg font-extrabold mb-2 ' 
        />
        <ShinyText 
          text="These prompts act as the “brain” of your AI email agent.
          You can customize how TailMind understands, analyzes, and responds to your emails.
          Updating a prompt immediately changes how the agent categorizes messages,
          extracts tasks, and writes replies — making the system adapt to your personal workflow" 
          disabled={false} 
          speed={6} 
          className='text-sm' 
        />
      </div>

      {["Categorization", "Action Extraction", "Auto Reply"].map((k) => (
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
