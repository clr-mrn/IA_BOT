import React, { useEffect, useState } from "react";
import ChatWidget from "./ChatWidget";
import "./chat.css";

export default function ChatLauncher() {
  const [open, setOpen] = useState(false);

  // Option : fermer avec la touche ESC
  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === "Escape") setOpen(false);
    }
    if (open) window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  return (
    <>
      {/* Overlay (utile surtout sur mobile) */}
      <div
        className={`chat-overlay ${open ? "is-open" : ""}`}
        onClick={() => setOpen(false)}
      />

      <div className={`chat-panel ${open ? "is-open" : ""}`}>
        <ChatWidget onClose={() => setOpen(false)} />
      </div>

      <button
        className={`chat-fab ${open ? "is-open" : ""}`}
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Fermer le chatbot" : "Ouvrir le chatbot"}
      >
        {open ? "✕" : "💬"}
      </button>
    </>
  );
}
