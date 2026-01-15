import React, { useState, useMemo } from "react";
import data from "/backend/data/kb.json";
import defaultRestaurantImg from "../assets/images/restaurant_defaut.jpg";

export default function Restaurants() {
  const restaurants = data.places.filter(p => p.type === "restaurant");

  const districts = [...new Set(restaurants.map(r => r.district))];
  const themes = [...new Set(restaurants.flatMap(r => r.themes))];

  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [search, setSearch] = useState("");
  const [selectedTheme, setSelectedTheme] = useState("");

  const resetFilters = () => {
    setSelectedDistrict("");
    setSelectedTheme("");
    setSearch("");
  };

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

      <input
        type="text"
        placeholder="Rechercher un restaurant..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="search-bar"
      />

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

        <button className="reset-btn" onClick={resetFilters}>
          Réinitialiser
        </button>
      </div>

      <div className="tags">
        {themes.map(t => {
          const label = t.charAt(0).toUpperCase() + t.slice(1);
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

      <div className="restaurant-list">
        {filteredRestaurants.map(r => (
          <div key={r.id} className="restaurant-card">

            <div className="carousel">
                <img
                    src={r.image_url || defaultRestaurantImg}
                    alt={r.name}
                    onError={(e) => {
                        e.currentTarget.src = defaultRestaurantImg;
                    }}
                />
            </div>

            <h3>{r.name}</h3>
            <p><strong>Quartier :</strong> {r.district}</p>
            <p><strong>Thèmes :</strong> {r.themes.join(", ")}</p>
            <p>{r.short_description}</p>

            {r.url ? (
            <a
                href={r.url}
                target="_blank"
                rel="noreferrer"
                className="card-link"
            >
                Voir plus
            </a>
) : (
  <span className="card-link disabled">Lien indisponible</span>
)}

          </div>
        ))}
      </div>
    </section>
  );
}