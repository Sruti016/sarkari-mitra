import React, { useState, useRef, useEffect, useCallback } from "react";
import { addBookmark, removeBookmark, getBookmarks } from "../bookmarks";
import { auth } from "../firebase";
import { signOut } from "firebase/auth";
import { useNavigate } from "react-router-dom";
import {
  getOrCreateSession,
  resetSession,
  sendChat,
  getVoice,
} from "../api/axios";
import ReactMarkdown from "react-markdown";
import toast from "react-hot-toast";
import {
  LANGUAGES,
  QUICK_ACTIONS,
  POPULAR_SCHEMES,
  MOCK_PROFILE,
  t,
} from "../utils/staticData";
import { save, load, clear } from "../utils/storage";

// ── Storage keys ───────────────────────────────────────────────────────────────
const userId = auth.currentUser?.uid || "guest";
const ACTIVE_KEY = `sm_active_${userId}`;
const PROFILE_KEY = `sm_profile_${userId}`;
const LANG_KEY = `sm_lang_${userId}`;
const SESSIONS_KEY = `sm_sessions_${userId}`;
const SIDEBAR_KEY = `sm_sidebar_open_${userId}`;

// ── Helpers ────────────────────────────────────────────────────────────────────
const uid = () => Math.random().toString(36).slice(2, 9);
const now = () =>
  new Date().toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });

function relativeDate(dateStr) {
  const d = new Date(dateStr);
  const diff = Math.floor((Date.now() - d) / 86400000);
  if (diff === 0) return "TODAY";
  if (diff === 1) return "YESTERDAY";
  if (diff < 7) return `${diff} DAYS AGO`;
  return d
    .toLocaleDateString("en-IN", { day: "numeric", month: "short" })
    .toUpperCase();
}

// ── Typing indicator ───────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex items-end gap-2 mb-3">
      <div className="w-8 h-8 rounded-full bg-green-100 border-2 border-green-200 flex items-center justify-center text-base flex-shrink-0">
        🏛️
      </div>
      <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1.5 items-center">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-2 h-2 rounded-full bg-green-500 block"
              style={{
                animation: "bounce 1.2s infinite",
                animationDelay: `${i * 0.2}s`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Single message bubble — with TTS speaker button ────────────────────────────
function Bubble({ msg, onSpeak, speakingId }) {
  const isUser = msg.sender === "user";
  const isSpeaking = speakingId === msg.id;

  return (
    <div
      className={`flex items-end gap-2 mb-3 ${isUser ? "flex-row-reverse" : ""}`}
    >
      <div
        className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center font-bold text-sm shadow-sm
        ${isUser ? "bg-green-700 text-white text-base" : "bg-green-100 border-2 border-green-200 text-base"}`}
      >
        {isUser ? "👤" : "🏛️"}
      </div>

      <div
        className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}
        style={{ maxWidth: "75%" }}
      >
        <div
          className={`px-4 py-3 rounded-2xl text-[14px] leading-relaxed shadow-sm
          ${
            isUser
              ? "bg-green-700 text-white rounded-br-sm"
              : "bg-white border border-gray-100 text-gray-800 rounded-bl-sm"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{msg.text}</p>
          ) : (
            <ReactMarkdown
              components={{
                h1: ({ children }) => (
                  <p className="font-bold text-green-800 text-base mb-2">
                    {children}
                  </p>
                ),
                h2: ({ children }) => (
                  <p className="font-bold text-green-800 mb-1">{children}</p>
                ),
                h3: ({ children }) => (
                  <p className="font-semibold text-green-700 mb-0.5">
                    {children}
                  </p>
                ),
                p: ({ children }) => (
                  <p className="mb-2 last:mb-0">{children}</p>
                ),
                strong: ({ children }) => (
                  <strong className="font-bold text-green-800">
                    {children}
                  </strong>
                ),
                ul: ({ children }) => (
                  <ul className="my-1 space-y-0.5">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="my-1 space-y-0.5 list-decimal pl-4">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="flex gap-1.5 items-start text-[13px]">
                    <span className="text-green-500 mt-0.5 flex-shrink-0">
                      •
                    </span>
                    <span>{children}</span>
                  </li>
                ),
              }}
            >
              {msg.text}
            </ReactMarkdown>
          )}
        </div>

        {/* PDF source badges */}
        {!isUser && msg.sources?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {msg.sources.map((s, i) => (
              <span
                key={i}
                className="text-[11px] bg-green-50 text-green-700 border border-green-200 rounded-full px-2 py-0.5 font-medium"
              >
                📄 {s}
              </span>
            ))}
          </div>
        )}

        {/* Scheme mini cards */}
        {!isUser && msg.schemes?.length > 0 && (
          <div className="flex flex-col gap-1.5 w-full mt-1">
            {msg.schemes.slice(0, 3).map((s, i) => {
              const icon =
                s.eligible === true
                  ? "✅"
                  : s.eligible === "maybe"
                    ? "⚠️"
                    : "❌";
              const color =
                s.eligible === true
                  ? "#2E7D32"
                  : s.eligible === "maybe"
                    ? "#E65100"
                    : "#C62828";
              const bg =
                s.eligible === true
                  ? "#F1FFF4"
                  : s.eligible === "maybe"
                    ? "#FFF8F0"
                    : "#FFF1F1";
              return (
                <div
                  key={i}
                  style={{
                    background: bg,
                    borderLeft: `3px solid ${color}`,
                    borderRadius: "8px",
                    padding: "6px 10px",
                  }}
                >
                  <p style={{ fontSize: "12px", fontWeight: "700", color }}>
                    {icon} {s.scheme_name}
                  </p>
                  <p
                    style={{
                      fontSize: "11px",
                      color: "#555",
                      marginTop: "2px",
                    }}
                  >
                    {s.key_benefit}
                  </p>

                  <button
  onClick={() => addBookmark({
    id: s.scheme_name?.replace(/\s+/g, '_').toLowerCase(),
    name: s.scheme_name,
    benefit: s.key_benefit
  })}
  style={{
    fontSize: "10px",
    color: "#888",
    background: "none",
    border: "none",
    cursor: "pointer",
    marginTop: "4px",
    padding: "0"
  }}
>
  🔖 Save
</button>
                </div>
              );
            })}
          </div>
        )}

        {/* Bottom row: timestamp + speaker button */}
        <div className="flex items-center gap-2 px-1">
          <span className="text-[11px] text-gray-400">{msg.time}</span>

          {/* SPEAKER BUTTON — only on bot messages */}
          {!isUser && (
            <button
              onClick={() => onSpeak(msg)}
              title="Sunao (Listen)"
              className={`w-6 h-6 rounded-full flex items-center justify-center transition-all active:scale-90
                ${
                  isSpeaking
                    ? "bg-green-500 text-white animate-pulse"
                    : "bg-gray-100 text-gray-500 hover:bg-green-100 hover:text-green-700"
                }`}
            >
              {isSpeaking ? (
                <svg
                  width="12"
                  height="12"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" />
                </svg>
              ) : (
                <svg
                  width="12"
                  height="12"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M11 5L6 9H2v6h4l5 4V5z" />
                  <path
                    d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"
                    strokeLinecap="round"
                  />
                </svg>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── LEFT SIDEBAR ───────────────────────────────────────────────────────────────
function LeftSidebar({
  sessions,
  onSelect,
  onNew,
  activeId,
  lang,
  onDeleteSession,
  isOpen,
  onToggle,
}) {
  const groups = {};
  [...sessions].reverse().forEach((s) => {
    const label = relativeDate(s.date);
    if (!groups[label]) groups[label] = [];
    groups[label].push(s);
  });

  return (
    <div
      className="flex flex-col h-full relative"
      style={{
        width: isOpen ? "260px" : "60px",
        flexShrink: 0,
        transition: "width 0.25s cubic-bezier(0.4,0,0.2,1)",
        overflow: "hidden",
        background:
          "linear-gradient(180deg, #0f3d1f 0%, #14532d 40%, #166534 100%)",
        borderRight: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      {/* ── COLLAPSED VIEW ── */}
      {!isOpen && (
        <div className="flex flex-col items-center h-full py-3 gap-3">
          <button
            onClick={onToggle}
            title="Open sidebar"
            className="w-10 h-10 rounded-xl flex items-center justify-center transition-all active:scale-90"
            style={{
              color: "#86efac",
              fontSize: "22px",
              fontWeight: "bold",
              background: "rgba(255,255,255,0.08)",
            }}
          >
            ›
          </button>
          <button
            onClick={onNew}
            title="New chat"
            className="w-10 h-10 rounded-xl flex items-center justify-center transition-all active:scale-90"
            style={{ background: "rgba(255,255,255,0.15)", color: "#fff" }}
          >
            <svg
              width="18"
              height="18"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
          </button>
          <div
            className="w-6"
            style={{ borderTop: "1px solid rgba(255,255,255,0.12)" }}
          />
          <div className="flex flex-col gap-1.5 flex-1 overflow-hidden items-center pt-1">
            {[...sessions]
              .reverse()
              .slice(0, 12)
              .map((session) => (
                <button
                  key={session.id}
                  onClick={() => onSelect(session)}
                  title={session.title}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-xs transition-all active:scale-90"
                  style={{
                    background:
                      activeId === session.id
                        ? "rgba(255,255,255,0.25)"
                        : "rgba(255,255,255,0.08)",
                    color: activeId === session.id ? "#fff" : "#86efac",
                  }}
                >
                  💬
                </button>
              ))}
          </div>
        </div>
      )}

      {/* ── EXPANDED VIEW ── */}
      {isOpen && (
        <>
          <div
            className="flex items-center gap-3 px-4 py-4 flex-shrink-0"
            style={{ borderBottom: "1px solid rgba(255,255,255,0.1)" }}
          >
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
              style={{ background: "rgba(255,255,255,0.15)" }}
            >
              🏛️
            </div>
            <div className="flex-1 min-w-0">
              <p
                className="font-bold text-[15px] truncate"
                style={{ color: "#fff" }}
              >
                सरकारी मित्र
              </p>
              <p className="text-[11px] truncate" style={{ color: "#86efac" }}>
                Chat History
              </p>
            </div>
            <button
              onClick={onToggle}
              title="Collapse sidebar"
              className="w-8 h-8 rounded-lg flex items-center justify-center transition-all flex-shrink-0 active:scale-90"
              style={{
                color: "#86efac",
                fontSize: "22px",
                fontWeight: "bold",
                background: "rgba(255,255,255,0.08)",
              }}
            >
              ‹
            </button>
          </div>

          <div
            className="px-4 py-3 flex-shrink-0"
            style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}
          >
            <button
              onClick={onNew}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-bold text-[13px] transition-all hover:opacity-90 active:scale-95"
              style={{
                background: "rgba(255,255,255,0.15)",
                color: "#fff",
                border: "1px solid rgba(255,255,255,0.2)",
              }}
            >
              <span className="text-lg">＋</span>
              {t(lang, "नया Chat", "New Chat", "Naya Chat")}
            </button>
          </div>

          <div className="px-4 py-2 flex items-center justify-between flex-shrink-0">
            <p
              className="text-[11px] font-bold uppercase tracking-wider"
              style={{ color: "#4ade80" }}
            >
              {t(lang, "Chat History", "Chat History", "Chat History")}
            </p>
            <span className="text-[11px]" style={{ color: "#4ade80" }}>
              {sessions.length} chats
            </span>
          </div>

          <div
            className="flex-1 overflow-y-auto px-3 pb-4"
            style={{
              scrollbarWidth: "thin",
              scrollbarColor: "rgba(255,255,255,0.2) transparent",
            }}
          >
            {sessions.length === 0 ? (
              <div className="text-center py-10">
                <p className="text-3xl mb-2">💬</p>
                <p className="text-[13px]" style={{ color: "#86efac" }}>
                  {t(
                    lang,
                    "कोई history नहीं",
                    "No history yet",
                    "Koi history nahi",
                  )}
                </p>
              </div>
            ) : (
              Object.entries(groups).map(([label, items]) => (
                <div key={label} className="mb-3">
                  <p
                    className="text-[10px] font-bold uppercase tracking-wider mb-1.5 px-2"
                    style={{ color: "#4ade80" }}
                  >
                    {label}
                  </p>
                  {items.map((session) => (
                    <div
                      key={session.id}
                      className="group flex items-center gap-2 px-2 py-2.5 rounded-xl mb-0.5 cursor-pointer transition-all"
                      style={{
                        background:
                          activeId === session.id
                            ? "rgba(255,255,255,0.18)"
                            : "transparent",
                        border:
                          activeId === session.id
                            ? "1px solid rgba(255,255,255,0.2)"
                            : "1px solid transparent",
                      }}
                      onMouseEnter={(e) => {
                        if (activeId !== session.id)
                          e.currentTarget.style.background =
                            "rgba(255,255,255,0.08)";
                      }}
                      onMouseLeave={(e) => {
                        if (activeId !== session.id)
                          e.currentTarget.style.background = "transparent";
                      }}
                      onClick={() => onSelect(session)}
                    >
                      <div
                        className="w-7 h-7 rounded-lg flex items-center justify-center text-xs flex-shrink-0"
                        style={{
                          background:
                            activeId === session.id
                              ? "rgba(255,255,255,0.25)"
                              : "rgba(255,255,255,0.1)",
                          color: "#fff",
                        }}
                      >
                        💬
                      </div>
                      <div className="flex-1 min-w-0">
                        <p
                          className="text-[12px] font-semibold truncate"
                          style={{
                            color: activeId === session.id ? "#fff" : "#bbf7d0",
                          }}
                        >
                          {session.title}
                        </p>
                        <p className="text-[10px]" style={{ color: "#4ade80" }}>
                          {session.messageCount} msgs
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(session.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 w-6 h-6 rounded-lg flex items-center justify-center transition-all flex-shrink-0"
                        style={{
                          color: "#fca5a5",
                          background: "rgba(255,0,0,0.12)",
                        }}
                        title="Delete chat"
                      >
                        <svg
                          width="12"
                          height="12"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth="2.5"
                        >
                          <path
                            d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              ))
            )}
          </div>

          <div
            className="px-4 py-3 flex-shrink-0"
            style={{
              borderTop: "1px solid rgba(255,255,255,0.08)",
              background: "rgba(0,0,0,0.15)",
            }}
          >
            <p className="text-[10px] text-center" style={{ color: "#4ade80" }}>
              {t(lang, "Locally saved", "Locally saved", "Locally saved")}
            </p>
          </div>
        </>
      )}
    </div>
  );
}

// ── Profile row ────────────────────────────────────────────────────────────────
function ProfileRow({ icon, label, value }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-gray-100 last:border-0">
      <span className="text-gray-500 text-[14px] flex items-center gap-2">
        {icon} {label}
      </span>
      {value ? (
        <span className="font-bold text-gray-800 text-[14px]">{value}</span>
      ) : (
        <span className="text-gray-300 text-[13px]">—</span>
      )}
    </div>
  );
}

// ─────────────────────────── MAIN CHAT PAGE ────────────────────────────────────
export default function ChatPage() {
  const navigate = useNavigate();

  const [lang, setLang] = useState(() => load(LANG_KEY, "hi"));
  const [messages, setMessages] = useState(() => load(ACTIVE_KEY, []));
  const [profile, setProfile] = useState(() =>
    load(PROFILE_KEY, { ...MOCK_PROFILE }),
  );
  const [sessions, setSessions] = useState(() => load(SESSIONS_KEY, []));
  const [activeId, setActiveId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(() => load(SIDEBAR_KEY, true));
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [listening, setListening] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  // ── TTS state ──────────────────────────────────────────────────────────────
  const [speakingId, setSpeakingId] = useState(null); // id of the message currently being spoken
  const audioRef = useRef(null); // current Audio object

  // ── Backend session ID ─────────────────────────────────────────────────────
  const [sessionId, setSessionId] = useState(null);

  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const recognRef = useRef(null);

  // ── Initialize backend session on mount ───────────────────────────────────
  useEffect(() => {
    const initSession = async () => {
      try {
        const sid = await getOrCreateSession();
        setSessionId(sid);
      } catch (err) {
        console.error("Backend not running!", err);
        toast.error("Backend connect nahi ho raha. Server start karo!");
      }
    };
    initSession();
  }, []);

  // ── Persist to localStorage ────────────────────────────────────────────────
  useEffect(() => {
    save(LANG_KEY, lang);
  }, [lang]);
  useEffect(() => {
    save(ACTIVE_KEY, messages);
  }, [messages]);
  useEffect(() => {
    save(PROFILE_KEY, profile);
  }, [profile]);
  useEffect(() => {
    save(SESSIONS_KEY, sessions);
  }, [sessions]);
  useEffect(() => {
    save(SIDEBAR_KEY, sidebarOpen);
  }, [sidebarOpen]);
  useEffect(() => {
    if (messages.length > 0) setShowWelcome(false);
  }, [messages]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Toggle sidebar ─────────────────────────────────────────────────────────
  const toggleSidebar = useCallback(() => setSidebarOpen((prev) => !prev), []);

  // ── Save session to localStorage ───────────────────────────────────────────
  const saveSession = useCallback(() => {
    if (messages.length === 0) return;
    const first = messages.find((m) => m.sender === "user");
    const title = first
      ? first.text.slice(0, 36) + (first.text.length > 36 ? "…" : "")
      : "Chat";
    const session = {
      id: activeId || uid(),
      title,
      date: new Date().toISOString(),
      messageCount: messages.length,
      messages: [...messages],
      profile: { ...profile },
    };
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== session.id);
      return [...filtered, session].slice(-30);
    });
    return session.id;
  }, [messages, profile, activeId]);

  // ── Delete local session ───────────────────────────────────────────────────
  const deleteSession = useCallback(
    (sid) => {
      setSessions((prev) => prev.filter((s) => s.id !== sid));
      if (activeId === sid) {
        setMessages([]);
        setActiveId(null);
        setShowWelcome(true);
      }
      toast.success(
        t(lang, "Chat delete हो गया", "Chat deleted", "Chat delete ho gaya"),
      );
    },
    [activeId, lang],
  );

  // ── New chat ───────────────────────────────────────────────────────────────
  const startNewChat = useCallback(async () => {
    saveSession();
    clear(ACTIVE_KEY);
    setMessages([]);
    setProfile({ ...MOCK_PROFILE });
    setActiveId(uid());
    setShowWelcome(true);
    setMenuOpen(false);

    // Stop any playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setSpeakingId(null);

    try {
      const newSid = await resetSession();
      setSessionId(newSid);
    } catch (err) {
      console.error("Session reset error:", err);
    }

    toast.success(
      t(lang, "नया chat शुरू!", "New chat started!", "Naya chat start!"),
    );
  }, [saveSession, lang]);

  // ── Load session ───────────────────────────────────────────────────────────
  const loadSession = useCallback(
    (session) => {
      saveSession();
      setMessages(session.messages);
      setProfile(session.profile || { ...MOCK_PROFILE });
      setActiveId(session.id);
      setShowWelcome(false);
    },
    [saveSession],
  );

  // ── TTS: speak a bot message ───────────────────────────────────────────────
  const handleSpeak = useCallback(
    async (msg) => {
      // If already speaking this message → stop
      if (speakingId === msg.id) {
        audioRef.current?.pause();
        audioRef.current = null;
        setSpeakingId(null);
        return;
      }

      // Stop whatever was playing before
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      setSpeakingId(msg.id);

      try {
        // getVoice should return an audio Blob / ArrayBuffer / URL
        // Adjust based on your actual API response shape:
        //   Option A — returns a Blob:      const blob = await getVoice(msg.text, lang);
        //   Option B — returns a URL string: const url  = await getVoice(msg.text, lang);
        const result = await getVoice(msg.text, lang);

        // backend gives audio_url
        const url = (import.meta.env.VITE_API_URL || "http://localhost:8000") + result.audio_url;

        const audio = new Audio(url);
        audioRef.current = audio;

        audio.onended = () => {
          setSpeakingId(null);
          audioRef.current = null;
        };

        audio.onerror = () => {
          setSpeakingId(null);
          audioRef.current = null;
          toast.error("Audio play nahi hua. Backend check karo.");
        };

        await audio.play();
      } catch (err) {
        console.error("TTS error:", err);
        setSpeakingId(null);
        toast.error("Voice generate nahi hua. Backend check karo.");
      }
    },
    [speakingId, lang],
  );

  // ── Send message ───────────────────────────────────────────────────────────
  const sendMessage = useCallback(
    async (text) => {
      const txt = (text || input).trim();
      if (!txt || loading) return;

      const userMsg = { id: uid(), sender: "user", text: txt, time: now() };
      setMessages((p) => [...p, userMsg]);
      setInput("");
      setLoading(true);
      setShowWelcome(false);
      if (inputRef.current) inputRef.current.style.height = "auto";

     try {
  // Agar session nahi hai toh pehle banao
  let sid = sessionId;
  if (!sid) {
    const { createSession } = await import("../api/axios");
    sid = await createSession();
    setSessionId(sid);
    localStorage.setItem("sarkari_session_id", sid);
  }
  const data = await sendChat(sid, txt);
  
      setMessages((p) => [
          ...p,
          {
            id: uid(),
            sender: "bot",
            text: data.response,
            sources: data.sources || [],
            schemes: data.scheme_recommendations || [],
            language: data.language,
            time: now(),
          },
        ]);

        if (data.user_profile) {
          setProfile((prev) => ({
            ...prev,
            profession: data.user_profile.profession
              ? data.user_profile.profession
              : prev.profession,
            state: data.user_profile.state
              ? data.user_profile.state
              : prev.state,
            category: data.user_profile.category
              ? data.user_profile.category
              : prev.category,
            gender: data.user_profile.gender
              ? data.user_profile.gender
              : prev.gender,
            age: data.user_profile.age
              ? data.user_profile.age + " साल"
              : prev.age,
            income: data.user_profile.income
              ? "₹" + data.user_profile.income.toLocaleString("en-IN")
              : prev.income,
          }));
        }
      } catch (err) {
        console.error("Chat API error:", err);
        setMessages((p) => [
          ...p,
          {
            id: uid(),
            sender: "bot",
            text: "⚠️ Backend se connect nahi ho pa raha. Kripya server start karein:\n`uvicorn main:app --reload --port 8000`",
            sources: [],
            time: now(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [input, loading, sessionId],
  );

  // ── Voice input ────────────────────────────────────────────────────────────
  const toggleVoice = async () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      toast.error(
        t(
          lang,
          "Voice support नहीं है",
          "Voice not supported",
          "Voice support nahi hai",
        ),
      );
      return;
    }
    if (listening) {
      recognRef.current?.stop();
      setListening(false);
      return;
    }
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      toast.error(
        t(
          lang,
          "Microphone permission do",
          "Please allow microphone permission",
          "Microphone permission do bhai",
        ),
      );
      return;
    }
    try {
      const r = new SR();
      r.lang = lang === "en" ? "en-IN" : "hi-IN";
      r.continuous = false;
      r.interimResults = false;
      r.maxAlternatives = 1;

      r.onstart = () => {
        setListening(true);
      };
      r.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        setInput(transcript);
        setListening(false);
        toast.success(
          t(lang, "Voice capture हो गया!", "Voice captured!", "Voice aa gaya!"),
        );
      };
      r.onerror = (e) => {
        setListening(false);
        const msgs = {
          "not-allowed":
            "Microphone blocked hai. Browser settings mein allow karo.",
          "no-speech": "Koi awaaz nahi aayi. Phir try karo.",
          "audio-capture": "Microphone detect nahi hua. Check karo.",
          network: "Network error. Internet check karo.",
          aborted: "Voice cancel ho gayi.",
          "service-not-allowed": "Voice service blocked hai.",
        };
        toast.error(msgs[e.error] || `Error: ${e.error}. Phir try karo.`);
      };
      r.onend = () => setListening(false);
      r.start();
      recognRef.current = r;
    } catch (err) {
      setListening(false);
      toast.error("Voice start nahi hua. Phir try karo.");
    }
  };

  const onInputChange = (e) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
  };
  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div
      className="flex h-screen bg-gray-100 overflow-hidden"
      style={{ fontFamily: "'Noto Sans','Hind',system-ui,sans-serif" }}
    >
      {/* ══ LEFT SIDEBAR ══ */}
      <LeftSidebar
        sessions={sessions}
        onSelect={loadSession}
        onNew={startNewChat}
        activeId={activeId}
        lang={lang}
        onDeleteSession={deleteSession}
        isOpen={sidebarOpen}
        onToggle={toggleSidebar}
      />

      {/* ══ MAIN CHAT COLUMN ══ */}
      <div className="flex flex-col flex-1 min-w-0 bg-gray-50">
        {/* NAVBAR */}
        <nav
          className="flex items-center justify-between px-5 flex-shrink-0 z-20"
          style={{
            height: "60px",
            background: "linear-gradient(135deg,#14532d 0%,#166534 100%)",
            boxShadow: "0 2px 12px rgba(20,83,45,0.3)",
          }}
        >
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={toggleSidebar}
                title="Open sidebar"
                className="w-9 h-9 rounded-xl flex items-center justify-center transition-all active:scale-90"
                style={{
                  color: "#86efac",
                  fontSize: "22px",
                  fontWeight: "bold",
                  background: "rgba(255,255,255,0.1)",
                }}
              >
                ›
              </button>
            )}
            <div className="relative">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-lg"
                style={{ background: "rgba(255,255,255,0.15)" }}
              >
                🏛️
              </div>
              <span
                className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-400 rounded-full border-2 border-green-800"
                style={{ animation: "pulse 2s infinite" }}
              />
            </div>

            {/* Logout Button */}
<button
  onClick={() => signOut(auth)}
  className="text-white text-xs bg-red-500 hover:bg-red-600 px-3 py-1 rounded-full"
>
  Logout
  
  </button>

   <button
  onClick={() => navigate("/bookmarks")}
  className="text-white text-xs bg-green-600 hover:bg-green-700 px-3 py-1 rounded-full ml-2"
>
  🔖 Meri Schemes
</button>

            <div>
              <p className="text-white font-bold text-[15px] leading-tight">
                Sarkari Mitra AI
              </p>
              <p className="text-green-300 text-[10px]">
                ● {sessionId ? "Online · Connected" : "Connecting..."} ·{" "}
                {t(
                  lang,
                  "Hindi | English | Hinglish",
                  "Hindi | English | Hinglish",
                  "Hindi | English | Hinglish",
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex bg-white/10 rounded-full p-0.5">
              {LANGUAGES.map((l) => (
                <button
                  key={l.code}
                  onClick={() => {
                    setLang(l.code);
                    save(LANG_KEY, l.code);
                  }}
                  className={`px-3 py-1 rounded-full text-[11px] font-bold transition-all ${lang === l.code ? "bg-white text-green-800" : "text-green-200 hover:text-white"}`}
                >
                  {l.label}
                </button>
              ))}
            </div>
            <div className="relative">
              <button
                onClick={() => setMenuOpen((o) => !o)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-white hover:bg-white/10 transition-all"
              >
                <svg
                  width="18"
                  height="18"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <circle cx="12" cy="5" r="1.8" />
                  <circle cx="12" cy="12" r="1.8" />
                  <circle cx="12" cy="19" r="1.8" />
                </svg>
              </button>
              {menuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-30"
                    onClick={() => setMenuOpen(false)}
                  />
                  <div
                    className="absolute right-0 top-10 bg-white rounded-2xl shadow-2xl z-40 overflow-hidden border border-gray-100"
                    style={{ width: "190px" }}
                  >
                    {[
                      {
                        icon: "🏛️",
                        label: t(
                          lang,
                          "Scheme देखें",
                          "View Schemes",
                          "Schemes Dekho",
                        ),
                        action: () => {
                          navigate("/schemes");
                          setMenuOpen(false);
                        },
                      },
                      {
                        icon: "🔄",
                        label: t(lang, "नया Chat", "New Chat", "Naya Chat"),
                        action: startNewChat,
                        danger: true,
                      },
                    ].map((item, i) => (
                      <button
                        key={i}
                        onClick={item.action}
                        className={`w-full flex items-center gap-3 px-4 py-3.5 text-left text-[14px] font-semibold transition-colors border-b border-gray-50 last:border-0
                          ${item.danger ? "text-red-600 hover:bg-red-50" : "text-gray-700 hover:bg-green-50"}`}
                      >
                        <span className="text-xl">{item.icon}</span>{" "}
                        {item.label}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </nav>

        {/* CHAT AREA */}
        <div
          className="flex-1 overflow-y-auto px-6 py-4"
          style={{
            scrollbarWidth: "thin",
            scrollbarColor: "#d1fae5 transparent",
          }}
        >
          {/* Welcome screen */}
          {showWelcome && (
            <div className="max-w-2xl mx-auto flex flex-col gap-5 pt-2 pb-6">
              <div
                className="w-full rounded-3xl p-6 text-center"
                style={{
                  background: "linear-gradient(135deg,#14532d,#166534)",
                  boxShadow: "0 8px 32px rgba(20,83,45,0.25)",
                }}
              >
                <div className="text-5xl mb-2">🏛️</div>
                <h1 className="text-white font-bold text-[22px] mb-1">
                  🙏{" "}
                  {t(
                    lang,
                    "Namaste! Main hun Sarkari Mitra",
                    "Hello! I am Sarkari Mitra",
                    "Namaste! Main hun Sarkari Mitra",
                  )}
                </h1>
                <p className="text-green-200 text-[14px] mb-1">
                  {t(
                    lang,
                    "Aapka trusted guide for all government schemes!",
                    "Your trusted guide for all government schemes!",
                    "Aapka trusted guide for all government schemes!",
                  )}
                </p>
                <p className="text-green-300 text-[13px] text-left mt-4">
                  <strong className="text-green-200">
                    {t(
                      lang,
                      "Main help kar sakta hun:",
                      "Main help kar sakta hun:",
                      "Main help kar sakta hun:",
                    )}
                  </strong>
                </p>
                <ul className="text-green-300 text-[13px] text-left mt-2 space-y-1">
                  <li>
                    🌾{" "}
                    {t(
                      lang,
                      "Kisan schemes (PM Kisan, Fasal Bima)",
                      "Kisan schemes (PM Kisan, Fasal Bima)",
                      "Kisan schemes (PM Kisan, Fasal Bima)",
                    )}
                  </li>
                  <li>
                    🏥{" "}
                    {t(
                      lang,
                      "Health schemes (Ayushman Bharat)",
                      "Health schemes (Ayushman Bharat)",
                      "Health schemes (Ayushman Bharat)",
                    )}
                  </li>
                  <li>
                    🏠{" "}
                    {t(
                      lang,
                      "Housing schemes (PM Awas)",
                      "Housing schemes (PM Awas)",
                      "Housing schemes (PM Awas)",
                    )}
                  </li>
                  <li>
                    ✅{" "}
                    {t(
                      lang,
                      "Eligibility check karna",
                      "Eligibility check karna",
                      "Eligibility check karna",
                    )}
                  </li>
                </ul>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {QUICK_ACTIONS.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => sendMessage(a.query)}
                    className="flex flex-col items-center gap-2 p-4 rounded-2xl border-2 active:scale-95 transition-all text-center hover:shadow-md"
                    style={{
                      background: a.bg,
                      borderColor: a.color + "44",
                      boxShadow: `0 2px 8px ${a.color}22`,
                    }}
                  >
                    <span className="text-3xl">{a.icon}</span>
                    <p
                      className="font-bold text-[13px] leading-tight"
                      style={{ color: a.color }}
                    >
                      {t(lang, a.hi, a.en, a.mix)}
                    </p>
                  </button>
                ))}
              </div>

              <button
                onClick={() => navigate("/schemes")}
                className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl font-bold text-[15px] text-white active:scale-95 transition-all hover:opacity-90"
                style={{
                  background: "linear-gradient(135deg,#4f46e5,#7c3aed)",
                  boxShadow: "0 4px 16px rgba(124,58,237,0.3)",
                }}
              >
                🏛️{" "}
                {t(
                  lang,
                  "सभी Scheme Cards देखें",
                  "View All Scheme Cards",
                  "Sab Scheme Cards Dekho",
                )}{" "}
                <span className="text-lg">→</span>
              </button>

              <div>
                <p className="text-gray-400 text-[12px] font-semibold uppercase tracking-wider mb-2">
                  {t(
                    lang,
                    "लोकप्रिय योजनाएं",
                    "Popular Schemes",
                    "Popular Yojanaen",
                  )}
                </p>
                <div className="flex gap-2 overflow-x-auto pb-1 flex-wrap">
                  {POPULAR_SCHEMES.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => navigate(`/yojana/${s.id}`)}
                      className="flex items-center gap-1.5 px-3 py-2 bg-white border border-gray-200 rounded-full text-[13px] text-gray-700 font-semibold whitespace-nowrap hover:border-green-400 hover:bg-green-50 hover:text-green-800 active:scale-95 transition-all shadow-sm"
                    >
                      {s.icon} {t(lang, s.hi, s.en, s.en)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Messages — pass onSpeak + speakingId to every Bubble */}
          <div className="max-w-2xl mx-auto">
            {messages.map((msg) => (
              <Bubble
                key={msg.id}
                msg={msg}
                onSpeak={handleSpeak}
                speakingId={speakingId}
              />
            ))}
            {loading && <TypingDots />}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* QUICK CHIPS */}
        {!showWelcome && (
          <div
            className="flex gap-2 px-5 py-2 overflow-x-auto flex-shrink-0 bg-white border-t border-gray-100"
            style={{ scrollbarWidth: "none" }}
          >
            {QUICK_ACTIONS.map((a) => (
              <button
                key={a.id}
                onClick={() => sendMessage(a.query)}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[12px] font-bold whitespace-nowrap active:scale-95 transition-all disabled:opacity-40 flex-shrink-0"
                style={{
                  background: a.bg,
                  borderColor: a.color + "55",
                  color: a.color,
                }}
              >
                {a.icon} {t(lang, a.hi, a.en, a.mix)}
              </button>
            ))}
            <button
              onClick={() => navigate("/schemes")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-purple-200 bg-purple-50 text-purple-700 text-[12px] font-bold whitespace-nowrap active:scale-95 transition-all flex-shrink-0"
            >
              🏛️ {t(lang, "Schemes", "Schemes", "Schemes")}
            </button>
          </div>
        )}

        {/* INPUT BAR */}
        <div
          className="px-5 pt-2 pb-3 flex-shrink-0 bg-white border-t border-gray-100"
          style={{ boxShadow: "0 -4px 16px rgba(0,0,0,0.06)" }}
        >
          <div className="max-w-2xl mx-auto">
            <div
              className={`flex items-end gap-2 bg-gray-50 border-2 rounded-2xl px-3 py-2 transition-all
              ${loading ? "border-gray-200" : "border-gray-200 focus-within:border-green-500 focus-within:bg-white focus-within:shadow-[0_0_0_3px_rgba(22,163,74,0.12)]"}`}
            >
              {/* Mic button (speech-to-text) */}
              <button
                onClick={toggleVoice}
                title={listening ? "Stop listening" : "Voice input"}
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all flex-shrink-0
                  ${listening ? "bg-red-500 text-white animate-pulse" : "bg-green-100 text-green-700 hover:bg-green-200 active:scale-90"}`}
              >
                <svg
                  width="18"
                  height="18"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" />
                </svg>
              </button>

              {/* Text area */}
              <textarea
                ref={inputRef}
                value={input}
                onChange={onInputChange}
                onKeyDown={onKey}
                disabled={loading}
                rows={1}
                placeholder={t(
                  lang,
                  "Koi bhi scheme ke baare mein poochhein...",
                  "Ask about any government scheme...",
                  "Koi bhi scheme ke baare mein poochhein...",
                )}
                className="flex-1 bg-transparent border-none outline-none resize-none text-[15px] text-gray-800 placeholder-gray-400 leading-relaxed py-1.5"
                style={{
                  minHeight: "24px",
                  maxHeight: "120px",
                  fontFamily: "inherit",
                }}
              />

              {/* 🔊 TTS Speaker button — plays last bot message audio on demand */}
              <button
                onClick={() => {
                  // Find the last bot message and speak it
                  const lastBot = [...messages]
                    .reverse()
                    .find((m) => m.sender === "bot");
                  if (lastBot) handleSpeak(lastBot);
                  else
                    toast(
                      t(
                        lang,
                        "Koi bot message nahi",
                        "No bot message yet",
                        "Koi bot message nahi",
                      ),
                    );
                }}
                disabled={loading}
                title="Bot ki awaaz sunao (Listen to last reply)"
                className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all
                  ${
                    speakingId
                      ? "bg-green-500 text-white animate-pulse shadow-md shadow-green-200"
                      : "bg-green-100 text-green-700 hover:bg-green-200 active:scale-90 disabled:opacity-40"
                  }`}
              >
                {speakingId ? (
                  /* Animated speaker — playing */
                  <svg
                    width="18"
                    height="18"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" />
                  </svg>
                ) : (
                  /* Normal speaker icon */
                  <svg
                    width="18"
                    height="18"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M11 5L6 9H2v6h4l5 4V5z" />
                    <path
                      d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"
                      strokeLinecap="round"
                    />
                  </svg>
                )}
              </button>

              {/* Send button */}
              <button
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all
                  ${
                    loading || !input.trim()
                      ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                      : "bg-green-600 text-white hover:bg-green-700 active:scale-90 shadow-md shadow-green-200"
                  }`}
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <svg
                    width="17"
                    height="17"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2.5"
                  >
                    <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" />
                  </svg>
                )}
              </button>
            </div>

            {listening && (
              <p className="text-center text-red-500 text-[12px] font-bold mt-1.5 animate-pulse">
                🎙️{" "}
                {t(
                  lang,
                  "सुन रहा हूँ... बोलें",
                  "Listening... speak now",
                  "Sun raha hun... bolein",
                )}
              </p>
            )}
            <p className="text-center text-[11px] text-gray-400 mt-1.5">
              Sarkari Mitra · Hamesha official govt portals se verify karein
            </p>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-6px)} }
        @keyframes pulse  { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes spin   { to{transform:rotate(360deg)} }
        * { -webkit-tap-highlight-color:transparent; }
        ::-webkit-scrollbar { width:4px; height:4px; }
        ::-webkit-scrollbar-thumb { background:#d1fae5; border-radius:99px; }
        ::-webkit-scrollbar-track { background:transparent; }
      `}</style>
    </div>
  );
}
