import React, { useState, useMemo } from "react";
import data from "/backend/data/kb.json";

const parks = data.places.filter(p => p.type === "park");

export default function Decouvertes() {
  const [selectedTheme, setSelectedTheme] = useState("all");

  // Filtrer par thème
  const filteredParks = useMemo(() => {
    if (selectedTheme === "all") {
      return parks;
    }
    return parks.filter((park) => park.themes.includes(selectedTheme));
  }, [selectedTheme]);

  // Extraire tous les thèmes uniques
  const allThemes = Array.from(
    new Set(parks.flatMap((park) => park.themes))
  ).sort();

  return (
    <div id="decouvrir">
      {/* Hero Section */}
      <div className="hero">
        <h1>Découvertes</h1>
        <p>Explorez les plus beaux parcs et espaces verts de Lyon</p>
      </div>

      {/* Statistiques - EN HAUT */}
      <div className="container" style={{ textAlign: "center", marginBottom: "40px" }}>
        <div className="grid2">
          <div>
            <h2 style={{ color: "#DC2626", fontSize: "36px", margin: "0" }}>
              {parks.length}
            </h2>
            <p style={{ margin: "8px 0 0 0", color: "#666" }}>Parcs et espaces verts</p>
          </div>
          <div>
            <h2 style={{ color: "#DC2626", fontSize: "36px", margin: "0" }}>
              {allThemes.length}
            </h2>
            <p style={{ margin: "8px 0 0 0", color: "#666" }}>Thèmes différents</p>
          </div>
        </div>
      </div>

      {/* Filtres - Tags */}
      <div className="container">
        <div className="tags">
          <button
            onClick={() => setSelectedTheme("all")}
            className={`tag ${selectedTheme === "all" ? "active" : ""}`}
          >
            Tous ({parks.length})
          </button>
          {allThemes.map((theme) => {
            const count = parks.filter((p) => p.themes.includes(theme)).length;
            return (
              <button
                key={theme}
                onClick={() => setSelectedTheme(theme)}
                className={`tag ${selectedTheme === theme ? "active" : ""}`}
              >
                {theme} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Contenu principal - Grid */}
      <div className="container">
        {filteredParks.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px 0" }}>
            <p>Aucun parc trouvé pour ce thème.</p>
          </div>
        ) : (
          <div className="grid3">
            {filteredParks.map((park) => (
              <a
                key={park.id}
                href={park.url}
                target="_blank"
                rel="noopener noreferrer"
                className="card-link"
              >
                <div className="feature-card is-visible">
                  {/* Image */}
                  <div className="feature-img">
                    <div
                      style={{
                        width: "100%",
                        height: "100%",
                        background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "white",
                        fontSize: "48px",
                      }}
                    >
                      📍
                    </div>
                  </div>

                  {/* Contenu */}
                  <div className="feature-content">
                    <h3>{park.name}</h3>
                    <p style={{ marginBottom: "10px" }}>{park.short_description}</p>
                    <p style={{ fontSize: "12px", color: "#999", marginBottom: "8px" }}>
                      {park.district}
                    </p>

                    {/* Thèmes */}
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                      {park.themes.slice(0, 2).map((theme) => (
                        <span
                          key={theme}
                          style={{
                            fontSize: "11px",
                            background: "#f3f4f6",
                            padding: "4px 8px",
                            borderRadius: "12px",
                            color: "#666",
                          }}
                        >
                          {theme}
                        </span>
                      ))}
                      {park.themes.length > 2 && (
                        <span
                          style={{
                            fontSize: "11px",
                            background: "#f3f4f6",
                            padding: "4px 8px",
                            borderRadius: "12px",
                            color: "#666",
                          }}
                        >
                          +{park.themes.length - 2}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}