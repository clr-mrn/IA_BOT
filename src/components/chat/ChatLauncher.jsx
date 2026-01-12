import React from "react";
import { useState } from "react";
import ChatWidget from "./ChatWidget";
import "./chat.css";

export default function ChatLauncher() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {open && <ChatWidget onClose={() => setOpen(false)} />}

      <button className="chat-launcher" onClick={() => setOpen(!open)}>
        💬
      </button>
    </>
  );
}
