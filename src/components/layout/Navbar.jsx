import React from "react";
import { NavLink, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();

  const scrollToSection = (id) => {
    navigate("/"); // reste sur Home
    setTimeout(() => {
      const section = document.getElementById(id);
      if (section) {
        section.scrollIntoView({ behavior: "smooth" });
      }
    }, 50);
  };

  return (
    <header className="nav">
      <div className="nav-inner">
        <div className="brand">LYON-ASSIST</div>

        <nav className="nav-tabs">
          <NavLink to="/" end onClick={() => scrollToSection("hero")}>
            Accueil
          </NavLink>

          <NavLink to="/" onClick={() => scrollToSection("decouvrir")}>
            Découvrir
          </NavLink>

          <NavLink to="/" onClick={() => scrollToSection("itineraires")}>
            Itinéraires
          </NavLink>

          <NavLink to="/" onClick={() => scrollToSection("infos")}>
            Infos pratiques
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
