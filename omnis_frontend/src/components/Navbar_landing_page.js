import React, { useState } from "react";
import api from "../utils/Api";
import "./styles.css";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff } from 'lucide-react';

const Navbar = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await api.post("/api/login", { username, password });

      if (response.status !== 200) {
        throw new Error("Login failed");
      }

      const data = response.data;
      console.log("Login successful:", data);
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      localStorage.setItem('username', username);
      localStorage.setItem('role', data.role);

      
      if (data.role === 'admin') {
        navigate("/admin");
      } else if (data.role === 'user') {
        navigate("/user");
      } else {
        navigate("/");
      }
      
      // Puoi gestire lo stato di login qui
    } catch (error) {
      setError("Login failed. Please check your credentials and try again.");
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white shadow-sm">
      <div className="container mx-auto flex flex-col md:flex-row h-auto md:h-16 items-center justify-between px-4 py-3 md:py-0">
        <div className="flex w-full md:w-auto items-center justify-between">
          <div className="flex items-center gap-2">
            <button 
              className="md:hidden text-blue-600"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
              <span className="sr-only">Toggle menu</span>
            </button>
            <a href="/" className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 text-blue-600">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
              </svg>
              <span className="font-bold text-lg text-blue-600">Omnis Platform</span>
            </a>
          </div>
        </div>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-6">
          <a
            href="#features"
            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
          >
            Features
          </a>
          <a
            href="#analytics"
            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
          >
            Analytics
          </a>
          <a
            href="#footer"
            className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
          >
            Contact
          </a>
        </nav>

        {/* Login Form */}
        <form 
          onSubmit={handleLogin} 
          className="hidden md:flex items-center gap-2 mt-4 md:mt-0"
        >
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <input
            type={isPasswordVisible ? "text" : "password"}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button 
            type="button" 
            onClick={() => setIsPasswordVisible(!isPasswordVisible)}
            className="ml-2"
          >
            {isPasswordVisible ? (
              <EyeOff size={24} />
            ) : (
              <Eye size={24} />
            )}
          </button>
          <button 
            type="submit" 
            className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Login
          </button>
        </form>
        
        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden w-full mt-4">
            <nav className="flex flex-col gap-4 pb-4">
              <a
                href="#features"
                className="text-gray-600 hover:text-blue-600 transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Features
              </a>
              <a
                href="#analytics"
                className="text-gray-600 hover:text-blue-600 transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Analytics
              </a>
              <a
                href="#footer"
                className="text-gray-600 hover:text-blue-600 transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Contact
              </a>
            </nav>
            
            {/* Mobile Login Form */}
            <form onSubmit={handleLogin} className="flex flex-col gap-3 mt-4">
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <input
                type={isPasswordVisible ? "text" : "password"}
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button 
                type="button" 
                onClick={() => setIsPasswordVisible(!isPasswordVisible)}
                className="ml-2"
              >
                {isPasswordVisible ? (
                  <EyeOff size={24} />
                ) : (
                  <Eye size={24} />
                )}
              </button>
              <button 
                type="submit" 
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Login
              </button>
            </form>
          </div>
        )}
        
        {/* Error Message */}
        {error && (
          <p className="text-sm text-red-500 mt-2 w-full text-center md:text-right">
            {error}
          </p>
        )}
      </div>
    </header>
  );
};

export default Navbar;