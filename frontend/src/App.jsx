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
 * App.jsx — refined aqua waves:
 * - per-line independent motion (CSS keyframes, different delays/durations)
 * - strokeWidth = 2 for minimal thin lines
 * - front layer blurred & subtle
 * - back layer has faint aqua glow (drop-shadow)
 *
 * Replace your current src/App.jsx with this file.
 */

function WaveSVGMany(props) {
  // many thin paths each with a class p1..p18 so CSS can animate them differently
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" {...props}>
      <rect width="100%" height="100%" fill="transparent" />
      <g fill="none" stroke="currentColor" strokeOpacity="0.95" strokeWidth="2">
        <path className="p1" d="M0 70 C160 10, 320 130, 480 50 C640 -10, 800 150, 960 80 C1120 10, 1280 200, 1600 120" />
    <path className="p2" d="M0 110 C160 40, 320 180, 480 140 C640 100, 800 220, 960 160 C1120 120, 1280 260, 1600 200" />
    <path className="p3" d="M0 150 C160 80, 320 220, 480 180 C640 140, 800 260, 960 200 C1120 160, 1280 300, 1600 240" />
    <path className="p4" d="M0 190 C160 120, 320 260, 480 220 C640 180, 800 300, 960 240 C1120 200, 1280 340, 1600 280" />
    <path className="p5" d="M0 230 C160 160, 320 300, 480 260 C640 220, 800 340, 960 280 C1120 240, 1280 380, 1600 320" />
    <path className="p6" d="M0 270 C160 200, 320 340, 480 300 C640 260, 800 380, 960 320 C1120 280, 1280 420, 1600 360" />
    <path className="p7" d="M0 310 C160 240, 320 380, 480 340 C640 300, 800 420, 960 360 C1120 320, 1280 460, 1600 400" />
    <path className="p8" d="M0 350 C160 280, 320 420, 480 380 C640 340, 800 460, 960 400 C1120 360, 1280 500, 1600 440" />
    <path className="p9" d="M0 390 C160 320, 320 460, 480 420 C640 380, 800 500, 960 440 C1120 400, 1280 540, 1600 480" />
    <path className="p10" d="M0 430 C160 360, 320 500, 480 460 C640 420, 800 540, 960 480 C1120 440, 1280 580, 1600 520" />
    <path className="p11" d="M0 470 C160 400, 320 540, 480 500 C640 460, 800 580, 960 520 C1120 480, 1280 620, 1600 560" />
    <path className="p12" d="M0 510 C160 440, 320 580, 480 540 C640 500, 800 620, 960 560 C1120 520, 1280 660, 1600 600" />
    <path className="p13" d="M0 550 C160 480, 320 620, 480 580 C640 540, 800 660, 960 600 C1120 560, 1280 700, 1600 640" />
    <path className="p14" d="M0 590 C160 520, 320 660, 480 620 C640 580, 800 700, 960 640 C1120 600, 1280 740, 1600 680" />
    <path className="p15" d="M0 630 C160 560, 320 700, 480 660 C640 620, 800 740, 960 680 C1120 640, 1280 780, 1600 720" />
    <path className="p16" d="M0 670 C160 600, 320 740, 480 700 C640 660, 800 780, 960 720 C1120 680, 1280 820, 1600 760" />
    <path className="p17" d="M0 710 C160 640, 320 780, 480 740 C640 700, 800 820, 960 760 C1120 720, 1280 860, 1600 800" />
    <path className="p18" d="M0 750 C160 680, 320 820, 480 780 C640 740, 800 860, 960 800 C1120 760, 1280 900, 1600 840" />

      </g>
    </svg>
  );
}

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
      if (e.key.toLowerCase() === "c") setChatOpen((v) => !v);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 relative" style={{ overflowX: "hidden" }}>
      {/* CSS for per-line motion, aqua tint, blur + glow */}
      <style>{`
        .aquamind-waves {
          position: fixed;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          overflow: hidden;
          background: transparent;
        }

        .aquamind-layer {
          position: absolute;
          left: 50%;
          top: 50%;
          width: 260%;
          height: 140%;
          transform: translate(-50%,-50%);
          will-change: transform;
        }

        /* back: glow, subtle */
        .aquamind-layer.back {
          opacity: 0.12;
          filter: drop-shadow(0 8px 18px rgba(14,165,233,0.06)) saturate(110%) blur(20px);
          color: #0b5f81; /* deep aqua */
        }
        /* mid: crisp */
        .aquamind-layer.mid {
          opacity: 0.015;
          filter: saturate(115%);
          color: #0ea5e9;
        }
        /* front: thin, blurred, subtle */
        .aquamind-layer.front {
          opacity: 0.1;
          filter: blur(10px) saturate(120%);
          color: #60a5fa;
        }

        /* Per-path motion — assign animations to classes p1..p18 with different durations/delays */
        /* small horizontal + vertical shifts for organic movement */
        .aquamind-layer svg .p1  { animation: move1 22s linear infinite; }
        .aquamind-layer svg .p2  { animation: move2 18s linear infinite; }
        .aquamind-layer svg .p3  { animation: move3 24s linear infinite; }
        .aquamind-layer svg .p4  { animation: move4 20s linear infinite; }
        .aquamind-layer svg .p5  { animation: move5 26s linear infinite; }
        .aquamind-layer svg .p6  { animation: move6 30s linear infinite; }
        .aquamind-layer svg .p7  { animation: move2 21s linear infinite; }
        .aquamind-layer svg .p8  { animation: move3 19s linear infinite; }
        .aquamind-layer svg .p9  { animation: move1 25s linear infinite; }
        .aquamind-layer svg .p10 { animation: move4 23s linear infinite; }
        .aquamind-layer svg .p11 { animation: move5 17s linear infinite; }
        .aquamind-layer svg .p12 { animation: move6 28s linear infinite; }
        .aquamind-layer svg .p13 { animation: move2 24s linear infinite; }
        .aquamind-layer svg .p14 { animation: move3 22s linear infinite; }
        .aquamind-layer svg .p15 { animation: move1 20s linear infinite; }
        .aquamind-layer svg .p16 { animation: move5 27s linear infinite; }
        .aquamind-layer svg .p17 { animation: move4 29s linear infinite; }
        .aquamind-layer svg .p18 { animation: move6 21s linear infinite; }

        /* slight stagger via animation-delay for more organic feel */
        .aquamind-layer svg .p1  { animation-delay: 0s; }
        .aquamind-layer svg .p2  { animation-delay: 0.9s; }
        .aquamind-layer svg .p3  { animation-delay: 1.7s; }
        .aquamind-layer svg .p4  { animation-delay: 2.3s; }
        .aquamind-layer svg .p5  { animation-delay: 3.1s; }
        .aquamind-layer svg .p6  { animation-delay: 4.4s; }
        .aquamind-layer svg .p7  { animation-delay: 0.5s; }
        .aquamind-layer svg .p8  { animation-delay: 1.2s; }
        .aquamind-layer svg .p9  { animation-delay: 2.0s; }
        .aquamind-layer svg .p10 { animation-delay: 2.7s; }
        .aquamind-layer svg .p11 { animation-delay: 3.6s; }
        .aquamind-layer svg .p12 { animation-delay: 4.8s; }
        .aquamind-layer svg .p13 { animation-delay: 0.2s; }
        .aquamind-layer svg .p14 { animation-delay: 1.0s; }
        .aquamind-layer svg .p15 { animation-delay: 1.9s; }
        .aquamind-layer svg .p16 { animation-delay: 2.5s; }
        .aquamind-layer svg .p17 { animation-delay: 3.2s; }
        .aquamind-layer svg .p18 { animation-delay: 4.0s; }

        /* keyframes: small randomized-looking transforms (horizontal + slight vertical) */
        @keyframes move1 {
          0%   { transform: translate(0px, 0px); }
          25%  { transform: translate(-18px, 6px); }
          50%  { transform: translate(-36px, -6px); }
          75%  { transform: translate(-18px, -3px); }
          100% { transform: translate(0px, 0px); }
        }
        @keyframes move2 {
          0%   { transform: translate(0px, 0px); }
          25%  { transform: translate(22px, -4px); }
          50%  { transform: translate(40px, 8px); }
          75%  { transform: translate(18px, 3px); }
          100% { transform: translate(0px, 0px); }
        }
        @keyframes move3 {
          0%   { transform: translate(0px, 0px); }
          25%  { transform: translate(-26px, -2px); }
          50%  { transform: translate(-50px, 10px); }
          75%  { transform: translate(-28px, 4px); }
          100% { transform: translate(0px, 0px); }
        }
        @keyframes move4 {
          0%   { transform: translate(0px, 0px); }
          25%  { transform: translate(16px, 6px); }
          50%  { transform: translate(32px, -8px); }
          75%  { transform: translate(12px, -2px); }
          100% { transform: translate(0px, 0px); }
        }
        @keyframes move5 {
          0%   { transform: translate(0px, 0px); }
          25%  { transform: translate(-12px, 8px); }
          50%  { transform: translate(-24px, -10px); }
          75%  { transform: translate(-10px, -4px); }
          100% { transform: translate(0px, 0px); }
        }
        @keyframes move6 {
          0%   { transform: translate(0px, 0px); }
          25%  { transform: translate(28px, -6px); }
          50%  { transform: translate(52px, 12px); }
          75%  { transform: translate(22px, 5px); }
          100% { transform: translate(0px, 0px); }
        }

        /* ensure animations are applied as transforms on the path elements (SVG) */
        .aquamind-layer svg path {
          transform-box: fill-box;
          transform-origin: center;
        }

        /* accessibility */
        @media (prefers-reduced-motion: reduce) {
          .aquamind-layer svg .p1,
          .aquamind-layer svg .p2,
          .aquamind-layer svg .p3,
          .aquamind-layer svg .p4,
          .aquamind-layer svg .p5,
          .aquamind-layer svg .p6,
          .aquamind-layer svg .p7,
          .aquamind-layer svg .p8,
          .aquamind-layer svg .p9,
          .aquamind-layer svg .p10,
          .aquamind-layer svg .p11,
          .aquamind-layer svg .p12,
          .aquamind-layer svg .p13,
          .aquamind-layer svg .p14,
          .aquamind-layer svg .p15,
          .aquamind-layer svg .p16,
          .aquamind-layer svg .p17,
          .aquamind-layer svg .p18 {
            animation: none !important;
            transform: translate(0,0) !important;
          }
        }
      `}</style>

      {/* three layers with different tint/filters */}
      <div className="aquamind-waves" aria-hidden="true">
        <div className="aquamind-layer back" style={{ zIndex: 0, color: "#084b60" }}>
          <WaveSVGMany style={{ width: "100%", height: "100%", display: "block" }} />
        </div>

        <div className="aquamind-layer mid" style={{ zIndex: 0, color: "#0ea5e9" }}>
          <WaveSVGMany style={{ width: "100%", height: "100%", display: "block" }} />
        </div>

        <div className="aquamind-layer front" style={{ zIndex: 0, color: "#60a5fa" }}>
          <WaveSVGMany style={{ width: "100%", height: "100%", display: "block" }} />
        </div>
      </div>

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
              <ChatBox emailId={selectedEmailId} onGenerateDraft={() => refreshInbox()} onToggleOpen={() => setChatOpen(false)} />
            </div>
          </aside>
        ) : (
          <aside className="sticky top-2 h-[95vh] flex items-start z-20">
            <div className="w-full flex items-start lg:items-center justify-center">
              <button
                onClick={() => setChatOpen(true)}
                aria-label="Open chat"
                className="chat-toggle glow mt-4 w-12 h-12 bg-neutral-900 border border-neutral-800 text-neutral-200 shadow-sm flex items-center justify-center"
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

      <div className="fixed bottom-6 right-6 lg:hidden z-30">
        <MobileFloatingWrapper emailId={selectedEmailId} onGenerateDraft={() => refreshInbox()} />
      </div>
    </div>
  );
}
