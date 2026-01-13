import React, { useEffect, useRef, useState } from "react";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";

const SUGGESTIONS = [
  "Que faire à Lyon en 2 jours ?",
  "Des idées de balades près des quais ?",
  "Un bouchon sympa dans le Vieux-Lyon ?"
];

function mockBotAnswer(userText) {
  const t = userText.toLowerCase();

  if (t.includes("2 jours") || t.includes("deux jours")) {
    return "Idée 2 jours : Jour 1 (Vieux-Lyon, traboules, Fourvière). Jour 2 (Tête d’Or, Croix-Rousse, Confluence). Tu veux un itinéraire détaillé ?";
  }
  if (t.includes("bouchon") || t.includes("restaurant")) {
    return "Pour un bouchon : vise le Vieux-Lyon ou Presqu’île. Dis-moi ton budget et le quartier, je te propose 2-3 options.";
  }
  if (t.includes("balade") || t.includes("quais") || t.includes("promenade")) {
    return "Balade sympa : quais du Rhône au coucher du soleil + arrêt à la Guillotière / Bellecour. Tu préfères plutôt nature ou ville ?";
  }
  return "Je peux t’aider à organiser ta visite : quartiers, itinéraires, restos, transports. Tu cherches quoi exactement ?";
}

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

  function handleSend(text) {
    const userMsg = { role: "user", content: text };

    setMessages((prev) => [...prev, userMsg]);
    setTyping(true);
    setInputDisabled(true);

    // Simule une réponse (sans backend)
    setTimeout(() => {
      const reply = mockBotAnswer(text);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
      setTyping(false);
      setInputDisabled(false);
    }, 900);
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
