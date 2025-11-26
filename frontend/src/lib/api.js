// src/lib/api.js
import axios from "axios";

// Get API URL from environment or use production URL as fallback
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://tailmind.onrender.com";

console.log("🔗 API Base URL:", API_BASE_URL);

// Create axios instance with configuration
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds for slow initial loads
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`📤 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error("❌ API Request Error:", error);
    return Promise.reject(error);
  }
);

// Add response interceptor for logging and error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error(`❌ API Error (${error.response.status}):`, error.response.data);
    } else if (error.request) {
      // Request made but no response received
      console.error("❌ API Error: No response received", error.request);
    } else {
      // Error setting up request
      console.error("❌ API Error:", error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * Format date/timestamp to readable string
 * @param {string|Date} ts - Timestamp to format
 * @returns {string} Formatted date string
 */
export function formatDate(ts) {
  if (!ts) return "";
  
  try {
    const date = new Date(ts);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return ts;
    }
    
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    // Return relative time for recent emails
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    // Return formatted date for older emails
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    });
  } catch (error) {
    console.error("Error formatting date:", error);
    return ts;
  }
}

/**
 * Format relative time (e.g., "2 hours ago")
 * @param {string|Date} ts - Timestamp
 * @returns {string} Relative time string
 */
export function formatRelativeTime(ts) {
  if (!ts) return "";
  
  try {
    const date = new Date(ts);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return "just now";
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
    
    return date.toLocaleDateString();
  } catch (error) {
    console.error("Error formatting relative time:", error);
    return ts;
  }
}

export default api;