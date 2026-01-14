import React from "react";
import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="nav">
      <div className="nav-inner">
        <div className="brand">LYON-ASSIST</div>

        <nav className="nav-tabs">
          <NavLink to="/" end>Accueil</NavLink>
          <NavLink to="/restaurants">Restaurants</NavLink>
          <NavLink to="/culture">Culture</NavLink>
          <NavLink to="/decouvertes">Découvertes</NavLink>
        </nav>
      </div>
    </header>
  );
}
