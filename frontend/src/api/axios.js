// src/api/axios.js
// ─────────────────────────────────────────────────────
// Real API calls to FastAPI backend
// Vite proxy: /api → http://localhost:8000
// ─────────────────────────────────────────────────────

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ── Session management ────────────────────────────────

export const createSession = async () => {
  const r = await fetch(`${BASE}/session/new`, { method: "POST" });
  const data = await r.json();
  return data.session_id;
};

export const getHistory = async (sessionId) => {
  const r = await fetch(`${BASE}/session/${sessionId}/history`);
  return r.json();
};

export const getProfile = async (sessionId) => {
  const r = await fetch(`${BASE}/session/${sessionId}/profile`);
  return r.json();
};

export const clearChat = async (sessionId) => {
  const r = await fetch(`${BASE}/session/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return r.json();
};

// ── Main chat ─────────────────────────────────────────

export const sendChat = async (sessionId, message) => {
  const r = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message: message,
    }),
  });
  if (!r.ok) throw new Error(`Chat API error: ${r.status}`);
  return r.json();
  // Returns:
  // {
  //   response              : "bot reply text",
  //   language              : "hinglish",
  //   sources               : ["pm_kisan.pdf"],
  //   user_profile          : { age, income, profession, state, category, gender },
  //   scheme_recommendations: [ { scheme_name, eligible, key_benefit, ... } ],
  //   conversation          : { total_messages: 4 }
  // }
};

// ── Voice TTS ─────────────────────────────────────────

export const getVoice = async (text, language) => {
  const r = await fetch(`${BASE}/voice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  return r.json();
  // Returns: { audio_url: "/audio/audio_abc123.mp3" }
};

export const playVoice = (audioUrl) => {
  // audioUrl = "/audio/filename.mp3"
  // Vite proxies /audio → localhost:8000/audio
  const audio = new Audio(audioUrl);
  audio.play();
  return audio;
};

// ── Knowledge base stats ──────────────────────────────

export const getIndexStats = async () => {
  const r = await fetch(`${BASE}/index/stats`);
  return r.json();
};

export const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const r = await fetch(`${BASE}/upload-pdf`, {
    method: "POST",
    body: formData,
    // DO NOT set Content-Type header — browser sets it automatically
  });
  return r.json();
};

// ── Session helpers ───────────────────────────────────

export const getOrCreateSession = async () => {
  // Always create fresh session — Railway resets DB on every deploy
  const sessionId = await createSession();
  localStorage.setItem("sarkari_session_id", sessionId);
  return sessionId;
};

export const resetSession = async () => {
  const sessionId = await createSession();
  localStorage.setItem("sarkari_session_id", sessionId);
  return sessionId;
};
