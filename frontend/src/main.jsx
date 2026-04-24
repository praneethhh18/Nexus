import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// Apply the persisted theme before React's first render so users don't see
// a dark-mode flash when they've chosen light, or vice versa.
try {
  const saved = localStorage.getItem('nexus_theme');
  if (saved === 'light' || saved === 'dark') {
    document.documentElement.setAttribute('data-theme', saved);
  }
} catch { /* localStorage disabled — fall back to default dark */ }

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
