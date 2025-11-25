// src/components/SidebarShell.jsx
import React from "react";
import { NavLink } from "react-router-dom";
import { InboxIcon, ChatBubbleLeftRightIcon, SparklesIcon, DocumentTextIcon } from "@heroicons/react/24/outline";

/**
 * Shadcn-style Sidebar (Option A)
 * This uses a simple structure modeled after shadcn patterns.
 * Replace icon set or component classes with shadcn components if you have them.
 */
const items = [
  { key: "inbox", label: "Inbox", to: "/inbox", Icon: InboxIcon },
  { key: "agent", label: "Agent", to: "/", Icon: ChatBubbleLeftRightIcon },
  { key: "prompt", label: "Prompt Brain", to: "/prompt-brain", Icon: SparklesIcon },
  { key: "drafts", label: "Drafts", to: "/drafts", Icon: DocumentTextIcon },
];

export default function SidebarShell({ onNavigate }) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4 h-full flex flex-col justify-between">
      <div>
        <div className="mb-6">
          <div className="text-2xl font-semibold mb-1">Ocean AI</div>
          <div className="text-xs text-neutral-400">Smart inbox & agent</div>
        </div>

        <nav className="space-y-1">
          {items.map((it) => (
            <NavLink
              key={it.key}
              to={it.to}
              className={({ isActive }) =>
                `group flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${
                  isActive ? "bg-neutral-800 text-neutral-50" : "hover:bg-neutral-850 text-neutral-300"
                }`
              }
            >
              <it.Icon className="w-5 h-5 text-neutral-400 group-hover:text-neutral-200" />
              <span>{it.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      <div>
        <button
          onClick={() => onNavigate && onNavigate("/")}
          className="w-full text-left px-3 py-2 rounded-lg bg-neutral-850 hover:bg-neutral-800 text-sm"
        >
          <div className="text-xs text-neutral-400">Status</div>
          <div className="text-sm">Connected</div>
        </button>
      </div>
    </div>
  );
}
