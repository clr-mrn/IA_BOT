import React, { useEffect, useState } from "react";

export default function ImageCarousel({ slides, interval = 4000 }) {
  const [index, setIndex] = useState(0);

  // Défilement automatique
  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % slides.length);
    }, interval);

    return () => clearInterval(timer);
  }, [slides.length, interval]);

  function prev() {
    setIndex((index - 1 + slides.length) % slides.length);
  }

  function next() {
    setIndex((index + 1) % slides.length);
  }

  return (
    <div className="carousel">
      <div
        className="carousel-slide"
        style={{ backgroundImage: `url(${slides[index].image})` }}
      >
        <div className="carousel-overlay">
          <h2>{slides[index].title}</h2>
          <p>{slides[index].description}</p>
        </div>
      </div>

      <button className="carousel-btn left" onClick={prev}>‹</button>
      <button className="carousel-btn right" onClick={next}>›</button>
    </div>
  );
}
