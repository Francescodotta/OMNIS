// src/components/Analytics.js
import React from "react";
import "./styles.css";

const Analytics = () => {
  return (
    <section id="analytics" className="analytics-section">
      <h2>Analytics at Scale</h2>
      <p>
        Perform computationally intensive multi-omics analyses directly on our
        platform, with powerful cloud-based infrastructure supporting your
        research.
      </p>
      <div className="analytics-stats">
        <div className="stat-card">
          <h3>500+</h3>
          <p>Genomic Analyses Completed</p>
        </div>
        <div className="stat-card">
          <h3>300TB+</h3>
          <p>Data Processed</p>
        </div>
        <div className="stat-card">
          <h3>99.9%</h3>
          <p>Uptime Guarantee</p>
        </div>
      </div>
    </section>
  );
};

export default Analytics;
