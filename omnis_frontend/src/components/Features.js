// src/components/Features.js
import React from "react";
import "./styles.css";

const Features = () => {
  return (
    <section id="features" className="features-section">
      <h2>Our Features</h2>
      <div className="features-container">
        <div className="feature-card">
          <i className="fas fa-dna"></i>
          <h3>Genomics</h3>
          <p>Comprehensive genomics analysis with state-of-the-art tools.</p>
        </div>
        <div className="feature-card">
          <i className="fas fa-microscope"></i>
          <h3>Proteomics</h3>
          <p>Analyze protein expression data with advanced algorithms.</p>
        </div>
        <div className="feature-card">
          <i className="fas fa-chart-line"></i>
          <h3>Metabolomics</h3>
          <p>Gain insights from complex metabolomics datasets.</p>
        </div>
      </div>
    </section>
  );
};

export default Features;
