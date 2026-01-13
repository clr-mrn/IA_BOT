import React from "react";

export default function Hero({ title, subtitle }) {
  return (
    <section className="hero">
      <h1 style={{ fontWeight: 800, letterSpacing: "0.5px" }}>{title}</h1>
      <p>{subtitle}</p>

      <div className="ctaRow">
        <a className="btn" href="/decouvrir">Découvrir la ville</a>
        <span className="hint">💬 Posez vos questions via le chatbot</span>
      </div>
    </section>
  );
}
