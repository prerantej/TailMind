// src/pages/Welcome.jsx
import React from "react";

export default function Welcome() {
  return (
    <div className="h-[70vh] flex items-center justify-center">
      <div className="text-center max-w-2xl">
        <img
          src="/mnt/data/a221586b-b9dc-4843-924e-a5d02da2d88c.png"
          alt="Ocean AI"
          className="mx-auto mb-6 w-40 h-40 object-contain rounded-lg opacity-95"
        />
        <h1 className="text-4xl font-semibold mb-2">Ocean AI</h1>
        <p className="text-neutral-400 mb-6">
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
