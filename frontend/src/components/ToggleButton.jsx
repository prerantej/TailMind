// src/components/ToggleButton.jsx
import React from "react";

export default function ToggleButton({
  icon,
  onClick,
  glow = false,
  size = 44,
  title = "",
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`
        flex items-center justify-center rounded-xl
        bg-[#18162A]/90 border border-white/5
        text-neutral-200 shadow-lg transition-all
        ${glow ? "animate-glowShadow" : ""}
        hover:scale-[1.03]
      `}
      style={{
        width: size,
        height: size,
      }}
    >
      {icon}
    </button>
  );
}
