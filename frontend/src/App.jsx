// src/App.jsx
import React, { useState, useEffect } from "react";
import { Routes, Route, useNavigate, NavLink } from "react-router-dom";
import SidebarShell from "./components/SidebarShell"; // kept if you want to reuse later
import Inbox from "./pages/Inbox";
import EmailDetail from "./pages/EmailDetail";
import PromptBrain from "./pages/PromptBrain";
import Drafts from "./pages/Drafts";
import Welcome from "./pages/Welcome";
import ChatBox, { MobileFloatingWrapper } from "./components/ChatBox";
// at top of file
import { Bot, Inbox as InboxIcon, MessageCircle, Brain, FileText } from "lucide-react";


/**
 * Updated App:
 * - Left sidebar inline here (Agent before Inbox)
 * - chatOpen defaults to false (closed on initial load)
 * - robot icon collapsed button, tooltip, hover glow, keyboard shortcut retained
 *
 * Local welcome image path (for reference): /mnt/data/edef30cc-dc55-4d6c-a6e0-9208ab71d7de.png
 */

export default function App() {
  // Chat closed by default now
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedEmailId, setSelectedEmailId] = useState(null);
  const [refreshInboxFlag, setRefreshInboxFlag] = useState(0);
  const refreshInbox = () => setRefreshInboxFlag((f) => f + 1);
  const navigate = useNavigate();

  // fixed grid columns: 380px chat when open, 48px when closed
  const gridTemplate = chatOpen ? "260px 1fr 380px" : "260px 1fr 48px";

  // keyboard shortcut to toggle chat (accessibility)
  useEffect(() => {
    function onKey(e) {
      if (e.key.toLowerCase() === "c") {
        setChatOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Inline sidebar so we can control ordering immediately:
  // Agent appears before Inbox (per your request)
  function LeftSidebar() {
    const navItems = [
      { key: "agent", label: "Agent", to: "/", Icon: MessageCircle },
      { key: "inbox", label: "Inbox", to: "/inbox", Icon: InboxIcon },
      { key: "prompt", label: "Prompt Brain", to: "/prompt-brain", Icon: Brain },
      { key: "drafts", label: "Drafts", to: "/drafts", Icon: FileText },    
    ];

    return (
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-5 h-full flex flex-col justify-between">
        <div>
          <div className="mb-6">
            <div className="text-2xl font-semibold">Ocean AI</div>
            <div className="text-xs text-neutral-400">Smart inbox & agent</div>
          </div>

          <nav className="space-y-1">
            {navItems.map((it) => (
              <NavLink
                key={it.key}
                to={it.to}
                className={({ isActive }) =>
                  `group flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${
                    isActive ? "bg-neutral-800 text-neutral-50" : "hover:bg-neutral-850 text-neutral-300"
                  }`
                }
                onClick={() => {
                  // ensure chat is closed when navigating (optional)
                  // setChatOpen(false);
                }}
              >
                {it.Icon ? <it.Icon className="w-5 h-5 text-neutral-400 group-hover:text-neutral-200" /> : null}
                <span>{it.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        <div>
          <div className="text-xs text-neutral-400 mb-1">Status</div>
          <div className="text-sm">Connected</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 relative" style={{ overflowX: "hidden" }}>
      <div
        className="max-w-[1400px] mx-auto px-4 py-6 grid gap-6"
        style={{ gridTemplateColumns: gridTemplate, transition: "grid-template-columns 200ms ease" }}
      >
        {/* Left: Inline sidebar (Agent before Inbox) */}
        <aside className="sticky top-2 h-[95vh]">
          <LeftSidebar />
        </aside>

        {/* Center: main routes */}
        <main className="min-h-[80vh] relative">
          <div className="space-y-6">
            <Routes>
              <Route path="/" element={<Welcome />} />
              <Route
                path="/inbox"
                element={
                  <Inbox
                    onSelectEmail={(id) => {
                      setSelectedEmailId(id);
                      navigate(`/email/${id}`);
                    }}
                    refreshFlag={refreshInboxFlag}
                  />
                }
              />
              <Route path="/email/:id" element={<EmailDetail emailId={selectedEmailId} />} />
              <Route path="/prompt-brain" element={<PromptBrain />} />
              <Route path="/drafts" element={<Drafts onOpenDraft={(id) => navigate(`/email/${id}`)} />} />
              <Route path="*" element={<Welcome />} />
            </Routes>
          </div>
        </main>

        {/* Right column: when open, show full ChatBox; when closed, show narrow column with centered robot button */}
        {chatOpen ? (
          <aside className="sticky top-2 h-[95vh]">
            <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4 h-full shadow-sm">
              <ChatBox
                emailId={selectedEmailId}
                onGenerateDraft={() => refreshInbox()}
                onToggleOpen={() => setChatOpen(false)}
              />
            </div>
          </aside>
        ) : (
          <aside className="sticky top-2 h-[95vh] flex items-start">
            {/* Narrow collapsed column; center the robot button so it never overflows */}
            <div className="w-full flex items-start lg:items-center justify-center">
              <button
                onClick={() => setChatOpen(true)}
                aria-label="Open chat"
                className="mt-4 w-12 h-12 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-200 shadow-sm
                           flex items-center justify-center hover:scale-[1.03] transition-transform duration-150
                           focus:outline-none focus:ring-2 focus:ring-indigo-500/30 relative group"
              >
                <Bot className="w-6 h-6 text-neutral-200" />
                {/* Tooltip (pure CSS) */}
                <span className="pointer-events-none absolute -top-10 left-1/2 transform -translate-x-1/2 scale-0 group-hover:scale-100 transition-transform duration-150 ease-out bg-neutral-800 border border-neutral-700 text-xs text-neutral-200 px-2 py-1 rounded-md whitespace-nowrap">
                  Open chat
                </span>
              </button>
            </div>
          </aside>
        )}
      </div>

      {/* Mobile: floating chat button/drawer */}
      <div className="fixed bottom-6 right-6 lg:hidden z-50">
        <MobileFloatingWrapper emailId={selectedEmailId} onGenerateDraft={() => refreshInbox()} />
      </div>
    </div>
  );
}
