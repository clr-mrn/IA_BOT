import React, { useEffect, useRef, useState } from "react";
import defaultCultureImg from "../../assets/images/default-culture.jpg";

export default function FeatureCard({ title, text, imageSrc, alt, link, showLinkButton = true }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.unobserve(el); // animation une seule fois
        }
      },
      { threshold: 0.2 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <article ref={ref} className={`feature-card ${visible ? "is-visible" : ""}`}>
      <div className="feature-img">
        <img
            src={imageSrc || defaultCultureImg}
            alt={alt || title}
            loading="lazy"
            onError={(e) => {
                e.currentTarget.src = defaultCultureImg;
            }}
        />
      </div>


      <div className="feature-content">
        <h3>{title}</h3>
        <p>{text}</p>

        {/* Bouton "Voir plus" */}
            {showLinkButton && (
            link ? (
        <a
            href={link}
            target="_blank"
            rel="noreferrer"
            className="card-link"
        >
            Voir plus
        </a>
  ) : (
    <span className="card-link disabled">Lien indisponible</span>
  )
)}

      </div>
    </article>
  );
}
