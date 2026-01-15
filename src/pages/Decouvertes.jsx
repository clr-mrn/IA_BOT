import React, { useState, useMemo } from "react";
import data from "/backend/data/kb.json";
import defaultParkImg from "../assets/images/parc_defaut.jpg";

const parks = data.places.filter(p => p.type === "park");

export default function Decouvertes() {
  const [selectedTheme, setSelectedTheme] = useState("all");
  const [search, setSearch] = useState("");

  // Filtrer par thème + recherche
  const filteredParks = useMemo(() => {
    let list = [...parks];

    if (search.trim() !== "") {
      list = list.filter((park) =>
        park.name.toLowerCase().includes(search.toLowerCase())
      );
    }

    if (selectedTheme !== "all") {
      list = list.filter((park) => park.themes.includes(selectedTheme));
    }

    return list;
  }, [selectedTheme, search]);

  const allThemes = Array.from(
    new Set(parks.flatMap((park) => park.themes))
  ).sort();

  return (
    <div id="decouvrir">
      {/* Hero Section */}
        <h1 style={{ textAlign: "center" }}>Découvertes</h1>
        <p style={{ textAlign: "center" }}>Explorez les plus beaux parcs et espaces verts de Lyon</p>

              {/* Barre de recherche */}
      <div className="container">
        <input
          type="text"
          placeholder="Rechercher un parc..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-bar"
        />
      </div>

      {/* Statistiques */}
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

      {/* Contenu principal */}
      <div className="container">
        {filteredParks.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px 0" }}>
            <p>Aucun parc trouvé.</p>
          </div>
        ) : (
          <div className="grid3">
            {filteredParks.map((park) => (
                <div key={park.id} className="feature-card is-visible">
                    {/* Image */}
                    <div className="feature-img">
                        <img
                            src={park.image_url || park.image || defaultParkImg}
                            alt={park.name}
                            loading="lazy"
                            onError={(e) => {
                                e.currentTarget.src = defaultParkImg;
                            }}
                            style={{
                                width: "100%",
                                height: "100%",
                                objectFit: "cover"
                            }}
                        />
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

      {/* Bouton "Voir plus" */}
      {park.url ? (
        <a
          href={park.url}
          target="_blank"
          rel="noreferrer"
          className="card-link"
          style={{ marginTop: 12 }}
        >
          Voir plus
        </a>
      ) : (
        <span className="card-link disabled" style={{ marginTop: 12 }}>
          Lien indisponible
        </span>
      )}
    </div>
  </div>
))}

          </div>
        )}
      </div>
    </div>
  );
}