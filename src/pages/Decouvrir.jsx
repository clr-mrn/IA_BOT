import React from "react";
import ImageCarousel from "../components/ui/ImageCarousel";

import vieuxLyon from "../assets/images/vieux-lyon.jpg";
import fourviere from "../assets/images/fourviere.jpg";
import croixRousse from "../assets/images/croix-rousse.jpg";
import teteOr from "../assets/images/tete-or.jpg";
import confluence from "../assets/images/confluence.jpg";
import presquile from "../assets/images/presquile.jpg";

export default function Decouvrir() {
  const slides = [
    {
      title: "Vieux-Lyon",
      description: "Ruelles pavées, traboules et architecture Renaissance.",
      image: vieuxLyon,
    },
    {
      title: "Fourvière",
      description: "Basilique emblématique et vue panoramique sur la ville.",
      image: fourviere,
    },
    {
      title: "Croix-Rousse",
      description: "Quartier des Canuts, artistique et vivant.",
      image: croixRousse,
    },
    {
      title: "Parc de la Tête d’Or",
      description: "Le poumon vert de Lyon, idéal pour se détendre.",
      image: teteOr,
    },
    {
      title: "Confluence",
      description: "Architecture moderne et Musée des Confluences.",
      image: confluence,
    },
    {
      title: "Presqu’île",
      description: "Cœur commerçant et historique de Lyon.",
      image: presquile,
    },
  ];

  return (
    <section className="page">
      <h1>Découvrir Lyon</h1>
      <p>Explorez les quartiers et lieux emblématiques de la ville.</p>

      <ImageCarousel slides={slides} />
    </section>
  );
}
