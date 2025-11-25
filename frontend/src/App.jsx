// src/App.jsx
import React, { useState, useEffect } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import SidebarShell from "./components/SidebarShell";
import Inbox from "./pages/Inbox";
import EmailDetail from "./pages/EmailDetail";
import PromptBrain from "./pages/PromptBrain";
import DraftDetail from "./pages/DraftDetail";
import Drafts from "./pages/Drafts";
import Welcome from "./pages/Welcome";
import ChatBox, { MobileFloatingWrapper } from "./components/ChatBox";
import { Bot } from "lucide-react";

/**
 * App - main
 *
 * Now supports responsive collapsing of the left sidebar via SidebarShell.onToggle(collapsed).
 * When the sidebar collapses, App updates gridTemplate so center content shifts left.
 */
export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedEmailId, setSelectedEmailId] = useState(null);
  const [refreshInboxFlag, setRefreshInboxFlag] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false); // track collapse state
  const refreshInbox = () => setRefreshInboxFlag((f) => f + 1);
  const navigate = useNavigate();

  // compute grid columns according to chatOpen and sidebarCollapsed
  // left column = 260px when expanded, 48px when collapsed (matches collapse button)
  // right column = 380px when chatOpen, 48px when closed
  const leftCol = sidebarCollapsed ? "48px" : "260px";
  const rightCol = chatOpen ? "380px" : "48px";
  const gridTemplate = `${leftCol} 1fr ${rightCol}`;

  // keyboard shortcut to toggle chat
  useEffect(() => {
    function onKey(e) {
      if (e.key.toLowerCase() === "c") {
        setChatOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 relative" style={{ overflowX: "hidden" }}>
      <div
        className="max-w-[1400px] mx-auto px-4 py-6 grid gap-6"
        style={{ gridTemplateColumns: gridTemplate, transition: "grid-template-columns 200ms ease" }}
      >
        {/* Left sidebar (collapsible) */}
        <aside className="sticky top-2 h-[95vh]">
          <SidebarShell initialCollapsed={false} onToggle={(collapsed) => setSidebarCollapsed(collapsed)} />
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

              <Route path="/drafts" element={<Drafts onOpenDraft={(id) => navigate(`/draft/${id}`)} />} />

              <Route path="/draft/:id" element={<DraftDetail />} />

              <Route path="/prompt-brain" element={<PromptBrain />} />

              <Route path="*" element={<Welcome />} />
            </Routes>
          </div>
        </main>

        {/* Right column: chat or collapsed button */}
        {chatOpen ? (
          <aside className="sticky top-2 h-[95vh]">
            <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4 h-full shadow-sm">
              <ChatBox emailId={selectedEmailId} onGenerateDraft={() => refreshInbox()} onToggleOpen={() => setChatOpen(false)} />
            </div>
          </aside>
        ) : (
          <aside className="sticky top-2 h-[95vh] flex items-start">
            <div className="w-full flex items-start lg:items-center justify-center">
              <button
                onClick={() => setChatOpen(true)}
                aria-label="Open chat"
                className="mt-4 w-12 h-12 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-200 shadow-sm flex items-center justify-center hover:scale-[1.03] transition-transform duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 relative group"
                style={{ borderWidth: "1px" }}
              >
                <Bot className="w-6 h-6 text-neutral-200" />
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
