import React, { useEffect, useRef, useState } from "react";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import { sendChatMessage } from "../../api/chatApi";

const SUGGESTIONS = [
  "Que faire à Lyon en 2 jours ?",
  "Des idées de balades près des quais ?",
  "Un bouchon sympa dans le Vieux-Lyon ?"
];


export default function ChatWidget({ onClose }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Bonjour 👋 Je suis l’assistant Tourisme Lyon. Pose-moi une question !"
    }
  ]);
  const [typing, setTyping] = useState(false);
  const [inputDisabled, setInputDisabled] = useState(false);

  const scrollRef = useRef(null);

  // Scroll auto à chaque nouveau message
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, typing]);

  async function handleSend(text) {
    const userMsg = { role: "user", content: text };

    setMessages((prev) => [...prev, userMsg]);
    setTyping(true);
    setInputDisabled(true);

    try {
      const data = await sendChatMessage(text);
      const reply = (data?.answer && String(data.answer).trim()) || "Je n’ai pas de réponse.";

      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Oups, je n’arrive pas à contacter le serveur. Vérifie que le backend tourne sur http://localhost:8000.",
        },
      ]);
    } finally {
      setTyping(false);
      setInputDisabled(false);
    }
  }

  return (
    <div className="chat-widget" role="dialog" aria-label="Chatbot Lyon Assist">
      <header className="chat-header">
        <div className="chat-title">
          <div className="chat-avatar" aria-hidden="true">🦁</div>
          <div>
            <div className="chat-name">Lyon Assist</div>
            <div className="chat-status">
              <span className="chat-dot" /> En ligne (démo)
            </div>
          </div>
        </div>

        <button className="chat-close" onClick={onClose} aria-label="Fermer">
          ✕
        </button>
      </header>

      <div className="chat-body" ref={scrollRef}>
        <MessageList messages={messages} />

        {typing && (
          <div className="msg assistant">
            <div className="bubble typing">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}

        <div className="suggestions">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              className="chip"
              onClick={() => handleSend(s)}
              disabled={inputDisabled}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <ChatInput onSend={handleSend} disabled={inputDisabled} />
    </div>
  );
}
