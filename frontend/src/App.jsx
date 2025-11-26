// src/App.jsx - Fix for chat toggle
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

// ... Keep all your WaveSVGMany component and styles ...

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedEmailId, setSelectedEmailId] = useState(null);
  const [refreshInboxFlag, setRefreshInboxFlag] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const refreshInbox = () => setRefreshInboxFlag((f) => f + 1);
  const navigate = useNavigate();

  // columns
  const leftCol = sidebarCollapsed ? "48px" : "260px";
  const rightCol = chatOpen ? "380px" : "48px";
  const gridTemplate = `${leftCol} 1fr ${rightCol}`;

  useEffect(() => {
    function onKey(e) {
      // Only toggle if 'c' key is pressed and not in an input/textarea
      if (e.key.toLowerCase() === "c" && 
          !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
        e.preventDefault();
        setChatOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 relative" style={{ overflowX: "hidden" }}>
      {/* ... Keep all your wave SVG styles and components ... */}
      
      {/* main app grid above waves */}
      <div
        className="max-w-[1400px] mx-auto px-4 py-6 grid gap-6 relative"
        style={{ gridTemplateColumns: gridTemplate, transition: "grid-template-columns 200ms ease", zIndex: 10 }}
      >
        <aside className="sticky top-2 h-[95vh] z-20">
          <SidebarShell initialCollapsed={false} onToggle={(c) => setSidebarCollapsed(c)} />
        </aside>

        <main className="min-h-[80vh] relative z-20">
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

        {/* Right chat area */}
        {chatOpen ? (
          <aside className="sticky top-2 h-[95vh] z-20">
            <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4 h-full shadow-sm">
              <ChatBox 
                emailId={selectedEmailId} 
                onGenerateDraft={() => refreshInbox()} 
                onToggleOpen={() => setChatOpen(false)} 
              />
            </div>
          </aside>
        ) : (
          <aside className="sticky top-2 h-[95vh] flex items-start z-20">
            <div className="w-full flex items-start lg:items-center justify-center">
              <button
                onClick={() => setChatOpen(true)}
                aria-label="Open chat (Press 'c')"
                className="chat-toggle glow mt-4 w-12 h-12 bg-neutral-900 border border-neutral-800 text-neutral-200 shadow-sm flex items-center justify-center rounded-xl group relative"
                style={{ borderWidth: "1px" }}
              >
                <Bot className="w-6 h-6 text-neutral-200" />
                <span className="pointer-events-none absolute -top-10 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-150 ease-out bg-neutral-800 border border-neutral-700 text-xs text-neutral-200 px-2 py-1 rounded-md whitespace-nowrap">
                  Open chat (c)
                </span>
              </button>
            </div>
          </aside>
        )}
      </div>

      <div className="fixed bottom-6 right-6 lg:hidden z-30">
        <MobileFloatingWrapper emailId={selectedEmailId} onGenerateDraft={() => refreshInbox()} />
      </div>
    </div>
  );
}