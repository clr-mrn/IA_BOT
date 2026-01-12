import React from "react";

export default function ChatWidget({ onClose }) {
  return (
    <div className="chat-widget">
      <header className="chat-header">
        <strong>Assistant Tourisme Lyon</strong>
        <button onClick={onClose}>✖</button>
      </header>

      <div className="chat-body">
        <p className="bot">Bonjour 👋 Posez votre question sur Lyon.</p>
      </div>

      <form className="chat-input">
        <input placeholder="Ex: Que faire à Lyon en 2 jours ?" />
        <button type="submit">Envoyer</button>
      </form>
    </div>
  );
}
