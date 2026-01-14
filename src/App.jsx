import React from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";

import Home from "./pages/Home";
import Restaurants from "./pages/Restaurants";
import Culture from "./pages/Culture";
import Decouvertes from "./pages/Decouvertes";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/restaurants" element={<Restaurants />} />
        <Route path="/culture" element={<Culture />} />
        <Route path="/decouvertes" element={<Decouvertes />} />
      </Route>
    </Routes>
  );
}