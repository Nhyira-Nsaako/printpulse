// Centralizes the backend base URLs so the frontend can be deployed on a
// different host than the backend (e.g. frontend on Vercel, backend on
// Railway). Set VITE_API_URL / VITE_WS_URL at build time for production;
// both fall back to the original local-dev behavior (Vite's /api proxy and
// ws://localhost:8000) when unset, so `npm run dev` is unaffected.

export const API_BASE: string = import.meta.env.VITE_API_URL || '/api'

export const WS_BASE: string =
  import.meta.env.VITE_WS_URL ||
  (import.meta.env.DEV ? 'ws://localhost:8000' : `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`)
