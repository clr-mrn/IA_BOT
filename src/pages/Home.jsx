import React from "react";
import Hero from "../components/ui/Hero";
import FeatureCard from "../components/ui/FeatureCard";

import imgIncontournables from "../assets/images/incontournable.jpg";
import imgGastronomie from "../assets/images/gastronomie.jpg";
import imgNature from "../assets/images/nature.jpg";

export default function Home() {
  return (
    <>
      <Hero
        title="Visiter Lyon"
        subtitle="Patrimoine, gastronomie et balades entre Rhône et Saône"
      />

      <section className="grid3">
        <FeatureCard
          title="Incontournables"
          text="Vieux-Lyon, Fourvière, Presqu’île."
          imageSrc={imgIncontournables}
          alt="Vue de Lyon et monuments"
        />

        <FeatureCard
          title="Gastronomie"
          text="Bouchons lyonnais et spécialités locales."
          imageSrc={imgGastronomie}
          alt="Plat typique lyonnais"
        />

        <FeatureCard
          title="Nature"
          text="Parc de la Tête d’Or, quais, balades."
          imageSrc={imgNature}
          alt="Parc et nature à Lyon"
        />
      </section>
    </>
  );
}
