export const save  = (key, val) => { try { localStorage.setItem(key, JSON.stringify(val)); } catch {} };
export const load  = (key, fallback = null) => { try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch { return fallback; } };
export const clear = (key) => { try { localStorage.removeItem(key); } catch {} };