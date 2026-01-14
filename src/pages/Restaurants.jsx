import React, { useState, useMemo } from "react";
import data from "/backend/data/kb.json";

export default function Restaurants() {
  // 1. On filtre uniquement les restaurants
  const restaurants = data.places.filter(p => p.type === "restaurant");

  // 2. Extraction automatique des districts et thèmes
  const districts = [...new Set(restaurants.map(r => r.district))];
  const themes = [...new Set(restaurants.flatMap(r => r.themes))];

  // 3. États
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [search, setSearch] = useState("");
  const [selectedTheme, setSelectedTheme] = useState("");

  // 4. Réinitialisation des filtres
  const resetFilters = () => {
    setSelectedDistrict("");
    setSelectedTheme("");
    setSearch("");
  };

  // 5. Filtrage dynamique
  const filteredRestaurants = useMemo(() => {
    let list = [...restaurants];

    if (search) {
      list = list.filter(r =>
        r.name.toLowerCase().includes(search.toLowerCase())
      );
    }

    if (selectedDistrict) {
      list = list.filter(r => r.district === selectedDistrict);
    }

    if (selectedTheme) {
      list = list.filter(r => r.themes.includes(selectedTheme));
    }

    return list;
  }, [search, selectedDistrict, selectedTheme, restaurants]);

  return (
    <section className="page restaurants-page">
      <h1>Recommandations Restaurants</h1>

      {/* Barre de recherche */}
      <input
        type="text"
        placeholder="Rechercher un restaurant..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="search-bar"
      />

      {/* Filtre district */}
      <div className="filters">
        <select
          value={selectedDistrict}
          onChange={e => setSelectedDistrict(e.target.value)}
        >
          <option value="">Tous les quartiers</option>
          {districts.map(d => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>

        {/* Bouton reset */}
        <button className="reset-btn" onClick={resetFilters}>
          Réinitialiser
        </button>
      </div>

      {/* Boutons de thèmes */}
      <div className="tags">
        {themes.map(t => {
          const label = t.charAt(0).toUpperCase() + t.slice(1); // majuscule
          return (
            <button
              key={t}
              className={`tag ${selectedTheme === t ? "active" : ""}`}
              onClick={() => setSelectedTheme(selectedTheme === t ? "" : t)}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Liste filtrée */}
      <div className="restaurant-list">
        {filteredRestaurants.map(r => (
          <div key={r.id} className="restaurant-card">

            {/* Carrousel d’images */}
            <div className="carousel">
              <img src={`/images/restaurants/${r.id}.jpg`} alt={r.name} />
            </div>

            <h3>{r.name}</h3>
            <p><strong>Quartier :</strong> {r.district}</p>
            <p><strong>Thèmes :</strong> {r.themes.join(", ")}</p>
            <p>{r.short_description}</p>

            <a href={r.url} target="_blank" rel="noreferrer">
              Voir plus
            </a>
          </div>
        ))}
      </div>
    </section>
  );
}