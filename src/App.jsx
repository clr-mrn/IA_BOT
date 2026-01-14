import React, { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";

import Home from "./pages/Home";
import Restaurants from "./pages/Restaurants";
import Culture from "./pages/Culture";
import Decouvertes from "./pages/Decouvertes";

import ChatWidget from "./components/chat/ChatWidget";

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);

  // Expose une fonction globale pour ouvrir le chat depuis n’importe où
  useEffect(() => {
    window.openChat = () => setChatOpen(true);
  }, []);

  return (
    <>
      {/* ROUTES */}
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/restaurants" element={<Restaurants />} />
          <Route path="/culture" element={<Culture />} />
          <Route path="/decouvertes" element={<Decouvertes />} />
        </Route>
      </Routes>

      {/* CHAT WIDGET */}
      {chatOpen && (
        <ChatWidget onClose={() => setChatOpen(false)} />
      )}
    </>
  );
}