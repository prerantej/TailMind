// src/pages/Welcome.jsx
import React from "react";
import { Link } from "react-router-dom";

export default function Welcome() {
  return (
    <div className="h-[70vh] flex items-center justify-center">
      <div className="text-center max-w-2xl">
        
        <h1 className="text-5xl font-semibold mb-2">TailMind</h1>
        <p className="text-neutral-400 mb-6 gap-3">
          Smart inbox, AI agent & prompt brain — manage emails, generate drafts, and extract tasks quickly.
        </p>

        <div className="flex justify-center gap-3">
          <Link 
            to="/inbox" 
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-md text-white text-sm transition-colors"
          >
            Open Inbox
          </Link>
          <Link 
            to="/prompt-brain" 
            className="px-4 py-2 border border-neutral-800 hover:bg-neutral-900 rounded-md text-sm text-neutral-200 transition-colors"
          >
            Edit Prompts
          </Link>
        </div>
      </div>
    </div>
  );
}