// src/components/Footer.js
import React from "react";
import "./styles.css";

const Footer = () => {
  return (
    <footer id="footer" className="footer-section">
      <div className="footer-content">
        <h3>Bioinformatics Platform</h3>
        <p>Empowering researchers with multi-omics data analysis tools.</p>
        <ul className="social-links">
          <li><a href="#"><i className="fab fa-twitter"></i></a></li>
          <li><a href="#"><i className="fab fa-linkedin"></i></a></li>
          <li><a href="#"><i className="fab fa-github"></i></a></li>
        </ul>
      </div>
    </footer>
  );
};

export default Footer;
