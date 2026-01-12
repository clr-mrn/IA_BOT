import React from "react";
import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="nav">
      <div className="nav-inner">
        <div className="brand">LYON-ASSIST</div>

        <nav className="nav-tabs">
          <NavLink to="/" end>Accueil</NavLink>
          <NavLink to="/decouvrir">Découvrir</NavLink>
          <NavLink to="/itineraires">Itinéraires</NavLink>
          <NavLink to="/infos">Infos pratiques</NavLink>
        </nav>
      </div>
    </header>
  );
}
