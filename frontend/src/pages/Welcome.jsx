// src/pages/Welcome.jsx
import React from "react";

export default function Welcome() {
  return (
    <div className="h-[70vh] flex items-center justify-center">
      <div className="text-center max-w-2xl">
        
        <h1 className="text-5xl font-semibold mb-2">TailMind</h1>
        <p className="text-neutral-400 mb-6 gap-3">
          Smart inbox, AI agent & prompt brain — manage emails, generate drafts, and extract tasks quickly.
        </p>

        <div className="flex justify-center gap-3">
          <a href="/inbox" className="px-4 py-2 bg-indigo-600 rounded-md text-white text-sm">Open Inbox</a>
          <a href="/prompt-brain" className="px-4 py-2 border border-neutral-800 rounded-md text-sm text-neutral-200">Edit Prompts</a>
        </div>
      </div>
    </div>
  );
}
