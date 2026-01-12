import React from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";

import Home from "./pages/Home";
import Decouvrir from "./pages/Decouvrir";
import Itineraires from "./pages/Itineraires";
import InfosPratiques from "./pages/InfosPratiques";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/decouvrir" element={<Decouvrir />} />
        <Route path="/itineraires" element={<Itineraires />} />
        <Route path="/infos" element={<InfosPratiques />} />
      </Route>
    </Routes>
  );
}
