// src/pages/Welcome.jsx
import React from "react";
import { Link } from "react-router-dom";
import BlurText from "../components/BlurText";


const handleAnimationComplete = () => {
  console.log('Animation completed!');
};

export default function Welcome() {
  return (
    <div className="min-h-[80vh] w-full flex items-center justify-center px-4">
      <div className="flex flex-col items-center text-center max-w-3xl">

        {/* Title */}
        <BlurText
          text="TailMind"
          delay={150}
          animateBy="words"
          direction="top"
          onAnimationComplete={handleAnimationComplete}
          className="text-7xl md:text-8xl font-bold mb-8"
        />

        {/* Subtitle */}
        <BlurText
          text="Smart inbox, AI agent & prompt brain - manage emails, generate drafts, and extract tasks quickly."
          delay={150}
          animateBy="words"
          direction="top"
          onAnimationComplete={handleAnimationComplete}
          className="text-lg md:text-2xl text-neutral-300 mb-10 leading-relaxed "
        />

        {/* Buttons */}
        <div className="flex justify-center gap-4">
          <Link
            to="/inbox"
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-md text-white text-sm transition-colors"
          >
            Open Inbox
          </Link>

          <Link
            to="/prompt-brain"
            className="px-6 py-2 border border-neutral-700 bg-neutral-900 hover:bg-neutral-800 rounded-md text-sm text-neutral-200 transition-colors"
          >
            Edit Prompts
          </Link>
        </div>

      </div>
    </div>

  );
}