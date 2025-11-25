// src/App.js
import React from "react";
import Navbar from "../components/Navbar_landing_page";
import HeroSection from "../components/HeroSection";
import Features from "../components/Features";
import Analytics from "../components/Analytics";
import Footer from "../components/Footer";
import "../components/styles.css";

function LandingPage() {
  return (
    <div className="App">
      <Navbar />
      <HeroSection />
      <Features />
      <Analytics />
      <Footer />
    </div>
  );
}

export default LandingPage;
