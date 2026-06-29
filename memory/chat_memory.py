# memory/chat_memory.py
# ─────────────────────────────────────────────────────────
# PURPOSE: Save and load conversation history per session
# UPDATED: Added get_history_for_llm(), get_all_sessions(),
#          delete_session(), session_exists()
#          All needed by FastAPI endpoints
# ─────────────────────────────────────────────────────────

import sqlite3
import json
import uuid
from datetime import datetime

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DB_PATH, MAX_HISTORY


def get_connection():
    """
    Create and return a SQLite connection.
    check_same_thread=False needed for FastAPI (multi-threaded).
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row      # Returns rows as dicts, not tuples
    return conn


def initialize_db():
    """
    Create tables if they don't exist yet.
    Called ONCE at FastAPI startup in main.py lifespan.
    Safe to call multiple times — uses IF NOT EXISTS.

    Tables:
    - sessions : one row per user session + profile
    - messages : all chat messages linked to session_id
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id   TEXT PRIMARY KEY,
            created_at   TEXT NOT NULL,
            user_profile TEXT DEFAULT '{}'
        )
    """)

    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            timestamp  TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")


def create_session() -> str:
    """
    Create a new session and return its unique ID.
    Called by POST /session/new FastAPI endpoint.
    """
    session_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()

    conn = get_connection()
    conn.execute(
        "INSERT INTO sessions (session_id, created_at) VALUES (?, ?)",
        (session_id, created_at)
    )
    conn.commit()
    conn.close()

    return session_id


def session_exists(session_id: str) -> bool:
    """
    NEW — Check if a session ID exists in DB.
    Used by FastAPI to validate session_id before processing.
    Prevents errors when React sends invalid/expired session IDs.
    """
    conn = get_connection()
    cursor = conn.execute(
        "SELECT 1 FROM sessions WHERE session_id = ?",
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None


def save_message(session_id: str, role: str, content: str):
    """
    Save one message to the database.

    Args:
        session_id: Which session this belongs to
        role      : "user" or "assistant"
        content   : The actual message text
    """
    timestamp = datetime.now().isoformat()

    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, role, content, timestamp)
    )
    conn.commit()
    conn.close()


def get_history(session_id: str) -> list[dict]:
    """
    Get last MAX_HISTORY messages for a session.
    Returns in chronological order (oldest first).
    Includes timestamp — used by FastAPI history endpoint.
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT role, content, timestamp FROM messages
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (session_id, MAX_HISTORY)
    )
    rows = cursor.fetchall()
    conn.close()

    history = [
        {
            "role"     : row["role"],
            "content"  : row["content"],
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]
    # Reverse so oldest message comes first
    return list(reversed(history))


def get_history_for_llm(session_id: str) -> list[dict]:
    """
    NEW — Get history in LLM format (role + content only, no timestamp).
    Used when building messages array for Groq API call.
    Groq API does not accept timestamp field — this strips it out.
    """
    full_history = get_history(session_id)
    return [
        {"role": m["role"], "content": m["content"]}
        for m in full_history
    ]


def save_user_profile(session_id: str, profile: dict):
    """
    Save user profile JSON to sessions table.
    Called by generator.py after extracting profile from message.
    """
    conn = get_connection()
    conn.execute(
        "UPDATE sessions SET user_profile = ? WHERE session_id = ?",
        (json.dumps(profile, ensure_ascii=False), session_id)
    )
    conn.commit()
    conn.close()


def get_user_profile(session_id: str) -> dict:
    """
    Load user profile for a session.
    Returns empty dict if no profile saved yet.
    """
    conn = get_connection()
    cursor = conn.execute(
        "SELECT user_profile FROM sessions WHERE session_id = ?",
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return json.loads(row["user_profile"])
    return {}


def clear_session(session_id: str):
    """
    Delete all messages for a session.
    Called by POST /session/clear FastAPI endpoint.
    Does NOT delete the session itself or its profile.
    """
    conn = get_connection()
    conn.execute(
        "DELETE FROM messages WHERE session_id = ?",
        (session_id,)
    )
    conn.commit()
    conn.close()


def get_all_sessions() -> list[dict]:
    """
    NEW — Return all sessions with message count and profile.
    Used by GET /admin/sessions FastAPI endpoint.
    Admin dashboard uses this to monitor active sessions.
    """
    conn = get_connection()
    cursor = conn.execute(
        """
        SELECT
            s.session_id,
            s.created_at,
            s.user_profile,
            COUNT(m.id) as message_count
        FROM sessions s
        LEFT JOIN messages m ON s.session_id = m.session_id
        GROUP BY s.session_id
        ORDER BY s.created_at DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "session_id"   : row["session_id"],
            "created_at"   : row["created_at"],
            "message_count": row["message_count"],
            "user_profile" : json.loads(row["user_profile"])
        }
        for row in rows
    ]


def delete_session(session_id: str):
    """
    NEW — Completely delete a session and all its messages.
    Used by DELETE /admin/session/{id} FastAPI endpoint.
    Admin cleanup tool for removing old/test sessions.
    """
    conn = get_connection()
    # Delete messages first (foreign key constraint)
    conn.execute(
        "DELETE FROM messages WHERE session_id = ?",
        (session_id,)
    )
    # Then delete the session itself
    conn.execute(
        "DELETE FROM sessions WHERE session_id = ?",
        (session_id,)
    )
    conn.commit()
    conn.close()


# ── Quick test ──────────────────────────────────────────
# Run: python memory/chat_memory.py
if __name__ == "__main__":
    initialize_db()

    # Test 1 — Create session
    sid = create_session()
    print(f"Created session: {sid}")

    # Test 2 — session_exists
    print(f"Session exists: {session_exists(sid)}")
    print(f"Fake exists   : {session_exists('fake-id-123')}")

    # Test 3 — Save messages
    save_message(sid, "user",      "What is PM Kisan?")
    save_message(sid, "assistant", "PM Kisan gives Rs.6000/year to farmers.")
    save_message(sid, "user",      "Am I eligible?")

    # Test 4 — Get history (with timestamp)
    history = get_history(sid)
    print(f"\nFull history ({len(history)} messages):")
    for msg in history:
        print(f"  [{msg['role']}] {msg['content'][:40]} | {msg['timestamp']}")

    # Test 5 — Get history for LLM (no timestamp)
    llm_history = get_history_for_llm(sid)
    print(f"\nLLM history ({len(llm_history)} messages):")
    for msg in llm_history:
        print(f"  [{msg['role']}]: {msg['content'][:40]}")

    # Test 6 — Save and get profile
    save_user_profile(sid, {
        "age": 35, "income": 150000,
        "profession": "farmer", "state": "MP"
    })
    profile = get_user_profile(sid)
    print(f"\nUser profile: {profile}")

    # Test 7 — get_all_sessions
    all_s = get_all_sessions()
    print(f"\nAll sessions: {len(all_s)}")
    for s in all_s:
        print(f"  {s['session_id'][:8]}... | {s['message_count']} messages")

    # Test 8 — clear_session
    clear_session(sid)
    print(f"\nAfter clear: {len(get_history(sid))} messages")

    # Test 9 — delete_session
    delete_session(sid)
    print(f"After delete: session_exists = {session_exists(sid)}")

    print("\n[DONE] All memory tests passed!")