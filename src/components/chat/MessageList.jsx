import React from "react";

export default function MessageList({ messages }) {
  return (
    <div className="messages">
      {messages.map((m, idx) => (
        <div key={idx} className={`msg ${m.role}`}>
          <div className="bubble">{m.content}</div>
        </div>
      ))}
    </div>
  );
}
