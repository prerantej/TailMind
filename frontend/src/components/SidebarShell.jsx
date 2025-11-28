// src/components/SidebarShell.jsx
import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { InboxIcon, ChatBubbleLeftRightIcon, SparklesIcon, DocumentTextIcon } from "@heroicons/react/24/outline";

/**
 * SidebarShell
 *
 * Props:
 *  - initialCollapsed (boolean) optional
 *  - onToggle(collapsed: boolean) optional callback (App uses to update grid)
 *
 * Behavior:
 *  - Expanded: full sidebar with top-right triple-bar button (≡)
 *  - Collapsed: small fixed circular button (≡) at top-left (like chat)
 */
const items = [
  { key: "agent", label: "Agent", to: "/", Icon: ChatBubbleLeftRightIcon },
  { key: "inbox", label: "Inbox", to: "/inbox", Icon: InboxIcon },
  { key: "prompt", label: "Prompt Brain", to: "/prompt-brain", Icon: SparklesIcon },
  { key: "drafts", label: "Drafts", to: "/drafts", Icon: DocumentTextIcon },
];

export default function SidebarShell({ initialCollapsed = false, onToggle = null }) {
  const [collapsed, setCollapsed] = useState(initialCollapsed);

  useEffect(() => {
    if (typeof onToggle === "function") onToggle(collapsed);
  }, [collapsed, onToggle]);

  function toggle() {
    setCollapsed((c) => !c);
  }

  // Collapsed view: fixed round button (behaves like chat button)
  if (collapsed) {
    return (
      <div className="fixed top-6 left-6 z-50 lg:relative lg:top-0 lg:left-0">
        <button
          onClick={toggle}
          aria-label="Open sidebar"
          title="Open sidebar"
          className="w-12 h-12 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-200 shadow-sm flex items-center justify-center hover:scale-[1.03] transition-transform duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
          style={{ borderWidth: "1px" }}
        >
          <span className="text-lg">≡</span>
        </button>
      </div>
    );
  }

  // Expanded view: full sidebar with top-right triple-bar button
  return (
    <aside className="bg-neutral-900/70 border border-neutral-800 rounded-2xl p-5 h-full flex flex-col justify-between relative">
      {/* top-right toggle */}
      <div className="absolute top-3 right-3">
        <button
          onClick={toggle}
          aria-label="Collapse sidebar"
          title="Collapse sidebar"
          className="inline-flex items-center justify-center w-9 h-9 rounded-3xl bg-neutral-800 border border-neutral-700 text-neutral-200 hover:bg-neutral-780 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
          style={{ borderWidth: "1px" }}
        >
          <span className="text-lg transform">≡</span>
        </button>
      </div>

      <div>
        <div className="mb-6">
          {/* Title now navigates to the Agent (home) route */}
          <NavLink to="/" className="group inline-block no-underline">
            <div className="text-2xl font-semibold cursor-pointer group-hover:opacity-95 transition-opacity">
              TailMind
            </div>
            <div className="text-xs text-neutral-400">Smart inbox & agent</div>
          </NavLink>
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
        {/* Status button: added glowing green dot */}
        <button
          onClick={() => {}}
          className="w-full text-left px-3 py-2 rounded-lg bg-neutral-850 hover:bg-neutral-800 text-sm flex items-center gap-3"
          aria-hidden
          style={{ borderWidth: "1px" }}
        >
          <div className="flex flex-col w-full">
            <div className="text-xs text-neutral-400">Status</div>
            <div className="text-sm flex items-center gap-3">
              {/* Green dot with pulse + subtle ring to emulate glow */}
              <span>Connected</span>
              <span
                aria-hidden
                className="inline-block w-1 h-1 rounded-full animate-pulse"
                style={{
                  backgroundColor: "#7cff67",
                  boxShadow: "0 0 10px rgba(124, 255, 103, 0.45)",
                }}
              />
            </div>
          </div>
        </button>
      </div>
    </aside>
  );
}
