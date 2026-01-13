import React, { useState } from "react";

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState("");

  function submit(e) {
    e.preventDefault();
    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue("");
  }

  return (
    <form className="chat-input" onSubmit={submit}>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Écris ta question…"
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        Envoyer
      </button>
    </form>
  );
}
