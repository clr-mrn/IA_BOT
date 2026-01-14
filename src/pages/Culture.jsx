import React, { useMemo, useState } from "react";
import FeatureCard from "../components/ui/FeatureCard";
import data from "/backend/data/kb.json";

import themeImg1 from "../assets/images/themes/theme1.jpg";
import themeImg2 from "../assets/images/themes/theme2.jpg";
import themeImg3 from "../assets/images/themes/theme3.jpg";
import defaultCultureImg from "../assets/images/default-culture.jpg";

const slugify = (s = "") =>
  s
    .toString()
    .toLowerCase()
    .trim()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

const capitalize = (s = "") =>
  s.charAt(0).toUpperCase() + s.slice(1);

const THEME_META_DEFAULTS = [
  { image: themeImg1, desc: "Découvre les lieux incontournables et les collections à ne pas manquer." },
  { image: themeImg2, desc: "Parcours les sites historiques, monuments et quartiers emblématiques." },
  { image: themeImg3, desc: "Une sélection de lieux parfaits pour une sortie culturelle ce week-end." },
];

const Culture = () => {
  const basePlaces = useMemo(() => {
    const places = data?.places ?? [];
    return places.filter((p) => p.type === "museum" || p.type === "heritage");
  }, []);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [selectedTheme, setSelectedTheme] = useState("");

  const filteredPlaces = useMemo(() => {
    const q = search.toLowerCase().trim();

    return basePlaces.filter((place) => {
      const matchFilter = filter === "all" || place.type === filter;

      const text = `
        ${place.name ?? ""}
        ${place.district ?? ""}
        ${place.short_description ?? ""}
        ${(place.themes ?? []).join(" ")}
      `.toLowerCase();

      const matchSearch = q === "" ? true : text.includes(q);

      return matchFilter && matchSearch;
    });
  }, [basePlaces, search, filter]);

  const themeStats = useMemo(() => {
    const counts = new Map();
    basePlaces.forEach((p) => {
      (p.themes ?? []).forEach((t) => {
        counts.set(t, (counts.get(t) ?? 0) + 1);
      });
    });

    return Array.from(counts.entries())
      .map(([theme, count]) => ({ theme, count }))
      .sort((a, b) => b.count - a.count);
  }, [basePlaces]);

  const allThemes = useMemo(() => {
    return themeStats
      .map((x) => x.theme)
      .sort((a, b) => a.localeCompare(b, "fr"));
  }, [themeStats]);

  const featuredThemes = useMemo(() => {
    const top3 = themeStats.slice(0, 3).map((x) => x.theme);

    return top3.map((theme, i) => ({
      theme,
      image: THEME_META_DEFAULTS[i]?.image ?? defaultCultureImg,
      desc:
        THEME_META_DEFAULTS[i]?.desc ??
        "Explore une sélection de lieux liés à ce thème.",
    }));
  }, [themeStats]);

  const placesByTheme = useMemo(() => {
    const map = new Map();

    filteredPlaces.forEach((place) => {
      (place.themes ?? []).forEach((t) => {
        if (!map.has(t)) map.set(t, []);
        map.get(t).push(place);
      });
    });

    return Array.from(map.entries()).sort(([a], [b]) =>
      a.localeCompare(b, "fr")
    );
  }, [filteredPlaces]);

  const scrollToTheme = (theme) => {
    const id = `theme-${slugify(theme)}`;
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const onSelectTheme = (e) => {
    const theme = e.target.value;
    setSelectedTheme(theme);
    if (theme) scrollToTheme(theme);
  };

  return (
<div className="page restaurants-page">
<h1>Culture à Lyon</h1>

      <input
        className="search-bar"
        type="text"
        placeholder="Rechercher un lieu culturel..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="culture-filters">
<button
          className={`culture-filter-btn ${filter === "all" ? "active" : ""}`}
          onClick={() => setFilter("all")}
>
          Tout
</button>
<button
          className={`culture-filter-btn ${filter === "museum" ? "active" : ""}`}
          onClick={() => setFilter("museum")}
>
          Musées
</button>
<button
          className={`culture-filter-btn ${filter === "heritage" ? "active" : ""}`}
          onClick={() => setFilter("heritage")}
>
          Patrimoine
</button>
</div>

      <div className="culture-theme-picker">
<label className="culture-theme-label" htmlFor="themeSelect">
          Séléctionner directement un thème :
</label>

        <select
          id="themeSelect"
          className="culture-theme-select"
          value={selectedTheme}
          onChange={onSelectTheme}
>
<option value="">Choisir un thème</option>
          {allThemes.map((t) => (
<option key={t} value={t}>
              {capitalize(t)}
</option>
          ))}
</select>
</div>

      <div className="theme-feature-grid">
        {featuredThemes.map((t) => (
<button
            key={t.theme}
            className="theme-feature-card"
            onClick={() => scrollToTheme(t.theme)}
            type="button"
>
<img
              className="theme-feature-img-img"
              src={t.image}
              alt={t.theme}
              style={{
                width: "100%",
                height: 160,
                objectFit: "cover",
                display: "block",
              }}
            />

            <div className="theme-feature-content">
<h3>{capitalize(t.theme)}</h3>
<p>{t.desc}</p>
<span className="theme-feature-cta">Explorer →</span>
</div>
</button>
        ))}
</div>

      {placesByTheme.length === 0 && (
<p style={{ textAlign: "center", marginTop: 24 }}>
          Aucun résultat avec ces filtres / cette recherche.
</p>
      )}

      <div className="culture-sections">
        {placesByTheme.map(([theme, places]) => (
<section key={theme} className="culture-section">
<h2 id={`theme-${slugify(theme)}`} className="culture-section-title">
              {capitalize(theme)}
<span className="culture-section-count">({places.length})</span>
</h2>

            <div className="restaurant-list">
              {places.map((place) => (
<FeatureCard
                  key={`${theme}-${place.id}`}
                  title={place.name}
                  text={place.short_description}
                  imageSrc={defaultCultureImg}
                  alt={place.name}
                />
              ))}
</div>
</section>
        ))}
</div>
</div>
  );
};

export default Culture;