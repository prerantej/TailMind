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
import Aurora from "./components/Aurora";
import ToggleButton from "./components/ToggleButton";
import { Bot } from "lucide-react";

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedEmailId, setSelectedEmailId] = useState(null);
  const [refreshInboxFlag, setRefreshInboxFlag] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const refreshInbox = () => setRefreshInboxFlag((f) => f + 1);
  const navigate = useNavigate();

  // Grid columns
  const leftCol = sidebarCollapsed ? "48px" : "260px";
  const rightCol = chatOpen ? "380px" : "48px";
  const gridTemplate = `${leftCol} 1fr ${rightCol}`;

  // Keyboard shortcut for chat
  useEffect(() => {
    function onKey(e) {
      if (e.key.toLowerCase() === "c" && !['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
        e.preventDefault();
        setChatOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 relative overflow-hidden">
      {/* Aurora Effect */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <Aurora
          colorStops={["#7cff67", "#b19eef", "#5227ff"]}
          blend={0.5}
          amplitude={1.0}
          speed={0.5}
        />
      </div>

      {/* Main Content */}
      <div
        className="max-w-[1400px] mx-auto px-4 py-6 grid gap-6 relative"
        style={{
          gridTemplateColumns: gridTemplate,
          transition: "grid-template-columns 200ms ease",
          zIndex: 10
        }}
      >
        {/* Sidebar */}
        <aside className="sticky top-2 h-[95vh] z-20">
          <SidebarShell
            initialCollapsed={false}
            onToggle={(c) => setSidebarCollapsed(c)}
          />
        </aside>

        {/* Main Content Area */}
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

              <Route
                path="/email/:id"
                element={<EmailDetail emailId={selectedEmailId} />}
              />

              <Route
                path="/drafts"
                element={<Drafts onOpenDraft={(id) => navigate(`/draft/${id}`)} />}
              />

              <Route path="/draft/:id" element={<DraftDetail />} />

              <Route path="/prompt-brain" element={<PromptBrain />} />

              <Route path="*" element={<Welcome />} />
            </Routes>
          </div>
        </main>

        {/* Chat Area */}
        {chatOpen ? (
          <aside className="sticky top-2 h-[95vh] z-20">
            <div className="bg-neutral-900/90 backdrop-blur-sm border border-neutral-800 rounded-2xl p-4 h-full shadow-lg">
              <ChatBox
                emailId={selectedEmailId}
                onGenerateDraft={() => refreshInbox()}
                onToggleOpen={() => setChatOpen(false)}
                isOpen={chatOpen}
              />
            </div>
          </aside>
        ) : (
          <aside className="sticky top-2 h-[95vh] flex items-start z-20">
            <div className="w-full flex items-start lg:items-center justify-center">
              <ToggleButton
                icon={<Bot className="w-6 h-6 text-neutral-200" />}
                onClick={() => setChatOpen(true)}
                glow={true} // glow when closed
                title="Open chat (c)"
                size={48}
              />
            </div>
          </aside>
        )}
      </div>

      {/* Mobile Chat Button */}
      <div className="fixed bottom-6 right-6 lg:hidden z-30">
        <MobileFloatingWrapper
          emailId={selectedEmailId}
          onGenerateDraft={() => refreshInbox()}
        />
      </div>
    </div>
  );
}
