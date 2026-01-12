import React, { useEffect, useRef, useState } from "react";

export default function FeatureCard({ title, text, imageSrc, alt }) {
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
        <img src={imageSrc} alt={alt || title} loading="lazy" />
      </div>

      <div className="feature-content">
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
    </article>
  );
}
