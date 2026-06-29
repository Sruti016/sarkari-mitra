# llm/generator.py
# ─────────────────────────────────────────────────────────
# FIXES APPLIED IN THIS VERSION:
#
# FIX 1 — "Server busy" + Wrong schemes
#   Root: _get_eligible_scheme_names() was reading
#   `eligibility_rules` but scheme_registry.json uses `eligibility`
#   → rules was always {} → every scheme passed all checks
#   → student got farmer schemes, eligible list was garbage
#   FIXED: Now reads correct keys from `eligibility` block:
#     profession  ← eligibility.profession  (list)
#     max_income  ← eligibility.max_income
#     age_min     ← eligibility.age_min
#     age_max     ← eligibility.age_max
#     gender      ← eligibility.gender
#
# FIX 2 — Proper ranking (profession > income > relevance)
#   Old: top_3 = eligible_schemes["eligible"][:3]  (no ranking)
#   New: _rank_eligible_schemes() scores each scheme:
#     +10 if profession matches exactly
#     +5  if income is within limit
#     +3  if age is within range
#     +2  if gender matches or is "all"
#     Sorted descending → top 3 picked
#
# FIX 3 — format_response() TypeError → 500
#   Some early-return paths were missing `focused_scheme_ids`
#   kwarg. Added focused_scheme_ids=None as default in all
#   format_response() calls so it never crashes.
#
# FIX 4 — Groq rate limit "server busy"
#   Retry wait increased from 6s → 10s.
#   Added a second fallback with reduced max_tokens (512)
#   so retry has better chance of succeeding.
# ─────────────────────────────────────────────────────────

import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from groq import Groq
from output.response_formatter import format_response

# ── Settings — loaded from config.py → .env ───────────────
# NEVER hardcode the API key here.
# Key lives in .env → config.py reads it → imported here.
from config import (
    GROQ_API_KEY,
    MODEL_NAME,
    MAX_TOKENS,
    TEMPERATURE,
)

# Max messages sent to LLM (prevents context overflow on long sessions)
MAX_HISTORY_FOR_LLM = 6   # reduced from 20 → saves ~1400 tokens per request

from rag.retriever import Retriever
from agent.language_detector import detect_language, get_language_label
from memory.chat_memory import (
    get_history, save_message,
    get_user_profile, save_user_profile
)
from llm.prompts import (
    get_system_prompt,
    get_rag_prompt,
    get_profile_collection_prompt
)


class Generator:

    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set.")
        self.client = Groq(api_key=GROQ_API_KEY)
        print(f"[Generator] Groq client ready. Model: {MODEL_NAME}")
        print(f"[Generator] API key: {GROQ_API_KEY[:8]}...")
        print("[Generator] Loading retriever...")
        self.retriever = Retriever()
        print("[Generator] Ready.")

    # ─────────────────────────────────────────────────────
    # PROFILE EXTRACTION
    # ─────────────────────────────────────────────────────

    def _extract_profile_from_reply(self, text: str, existing: dict) -> dict:
        """Extract profile fields from user message, overwriting old values."""
        import re
        profile    = existing.copy()
        text_lower = text.lower()

        # ── Age ───────────────────────────────────────────
        age_match = re.search(
            r'\b(\d{1,2})\s*(years?|sal|saal|साल|वर्ष|year old|yrs)?\b',
            text, re.IGNORECASE
        )
        if age_match:
            age = int(age_match.group(1))
            if 10 < age < 100:
                profile["age"] = age

        # ── Income ────────────────────────────────────────
        new_income = None

        m = re.search(r'(\d+\.?\d*)lakh', text_lower)
        if m:
            new_income = int(float(m.group(1)) * 100_000)

        if not new_income:
            m = re.search(
                r'(\d+\.?\d*)\s*(lakh|lac|लाख)', text, re.IGNORECASE
            )
            if m:
                new_income = int(float(m.group(1)) * 100_000)

        if not new_income:
            m = re.search(r'\b(\d{5,7})\b', text.replace(",", ""))
            if m:
                new_income = int(m.group(1))

        if new_income:
            profile["income"] = new_income

        # ── Profession ────────────────────────────────────
        professions = {
            "farmer"  : ["farmer", "farming", "agriculture", "kisan", "किसान"],
            "student" : ["student", "studying", "college", "school", "छात्र", "padhai"],
            "worker"  : ["worker", "labour", "labor", "mazdoor", "मजदूर"],
            "business": ["business", "shop", "trader", "व्यापार", "dukan"],
            "other"   : ["other", "अन्य", "sarkari", "job", "service"]
        }
        for prof, keywords in professions.items():
            if any(kw in text_lower for kw in keywords):
                profile["profession"] = prof
                break

        # ── State ─────────────────────────────────────────
        states = {
            "Madhya Pradesh"  : ["madhya pradesh", "mp"],
            "Uttar Pradesh"   : ["uttar pradesh", "up"],
            "Maharashtra"     : ["maharashtra"],
            "Rajasthan"       : ["rajasthan"],
            "Gujarat"         : ["gujarat"],
            "Bihar"           : ["bihar"],
            "Punjab"          : ["punjab"],
            "Haryana"         : ["haryana"],
            "Karnataka"       : ["karnataka"],
            "Tamil Nadu"      : ["tamil nadu", "tn"],
            "West Bengal"     : ["west bengal", "wb"],
            "Andhra Pradesh"  : ["andhra pradesh", "ap"],
            "Telangana"       : ["telangana"],
            "Kerala"          : ["kerala"],
            "Jharkhand"       : ["jharkhand"],
            "Odisha"          : ["odisha", "orissa"],
            "Uttarakhand"     : ["uttarakhand"],
            "Himachal Pradesh": ["himachal", "hp"],
            "Chhattisgarh"    : ["chhattisgarh", "cg"],
            "Assam"           : ["assam"],
            "Goa"             : ["goa"],
            "Manipur"         : ["manipur"],
            "Meghalaya"       : ["meghalaya"],
            "Tripura"         : ["tripura"]
        }
        for state_name, keywords in states.items():
            if any(kw in text_lower for kw in keywords):
                profile["state"] = state_name
                break

        # ── Caste Category ────────────────────────────────
        categories = {
            "SC"      : ["sc", "scheduled caste", "dalit", "अनुसूचित जाति"],
            "ST"      : ["st", "scheduled tribe", "adivasi", "tribal"],
            "OBC"     : ["obc", "other backward", "पिछड़ा वर्ग"],
            "General" : ["general", "gen", "unreserved", "open category", "सामान्य"],
            "Minority": ["muslim", "christian", "sikh", "buddhist", "minority"]
        }
        for cat, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                if not profile.get("category"):
                    profile["category"] = cat
                break

        # ── Gender ────────────────────────────────────────
        if not profile.get("gender"):
            if any(w in text_lower for w in
                   ["female", "girl", "woman", "महिला", "लड़की", "औरत"]):
                profile["gender"] = "Female"
            elif any(w in text_lower for w in
                     ["male", "boy", "man", "पुरुष", "लड़का"]):
                profile["gender"] = "Male"

        return profile

    # ─────────────────────────────────────────────────────
    # LANGUAGE DETECTION
    # ─────────────────────────────────────────────────────

    def _detect_language_override(self, message: str) -> str | None:
        msg = message.lower().strip()
        if any(t in msg for t in [
            "in hindi", "hindi mein", "hindi me", "hindi mai",
            "बताओ हिंदी में", "हिंदी में"
        ]):
            return "Hindi (Devanagari script)"
        if any(t in msg for t in [
            "in hinglish", "hinglish mein", "hinglish me", "hinglish mai"
        ]):
            return "Hinglish (casual mixed Hindi-English in Roman script)"
        if any(t in msg for t in [
            "in english", "english mein", "english me", "english mai"
        ]):
            return "English"
        return None

    def _get_conversation_language(
        self,
        current_lang: str,
        history     : list,
        override    : str | None
    ) -> str:
        if override:
            return override
        if current_lang in [
            "Hindi (Devanagari script)",
            "Hinglish (casual mixed Hindi-English in Roman script)"
        ]:
            return current_lang
        if current_lang == "English" and history:
            for msg in reversed(history):
                if msg["role"] == "assistant":
                    content = msg["content"].lower()
                    if any(w in content for w in
                           ["yaar", "bhai", "hai", "milega", "karo", "toh"]):
                        return "Hinglish (casual mixed Hindi-English in Roman script)"
                    if any(w in content for w in ["है", "हैं", "और", "के"]):
                        return "Hindi (Devanagari script)"
                    break
        return current_lang

    # ─────────────────────────────────────────────────────
    # FOLLOW-UP QUERY HANDLING
    # ─────────────────────────────────────────────────────

    FOLLOWUP_PRONOUNS = [
        "yeh", "ye", "iske", "is", "uske", "uss",
        "it", "this", "that", "tell me more", "aur batao",
        "details", "explain", "kya hai", "kaise"
    ]

    def _build_rag_query(self, user_message: str, history: list) -> str:
        msg_lower  = user_message.lower().strip()
        word_count = len(user_message.split())

        if word_count <= 4:
            has_pronouns = any(p in msg_lower for p in self.FOLLOWUP_PRONOUNS)
            has_topic    = any(c.isalpha() and len(w) > 4
                               for w in msg_lower.split()
                               for c in [w]
                               if w not in self.FOLLOWUP_PRONOUNS)
            if has_pronouns and not has_topic:
                for msg in reversed(history):
                    if msg["role"] == "user":
                        return msg["content"] + " " + user_message
        return user_message

    # ─────────────────────────────────────────────────────
    # SCHEME QUERY MAP
    # ─────────────────────────────────────────────────────

    SCHEME_QUERY_MAP = {
        "crop insurance"     : ["pm_fasal_bima"],
        "fasal bima"         : ["pm_fasal_bima"],
        "bima"               : ["pm_fasal_bima"],
        "pmfby"              : ["pm_fasal_bima"],
        "flood"              : ["pm_fasal_bima"],
        "drought"            : ["pm_fasal_bima"],
        "credit card"        : ["kisan_credit_card"],
        "kcc"                : ["kisan_credit_card"],
        "kisan credit"       : ["kisan_credit_card"],
        "solar"              : ["pm_kusum"],
        "kusum"              : ["pm_kusum"],
        "solar pump"         : ["pm_kusum"],
        "pm kisan"           : ["pm_kisan"],
        "samman nidhi"       : ["pm_kisan"],
        "kisan samman"       : ["pm_kisan"],
        "awas"               : ["pm_awas"],
        "housing"            : ["pm_awas"],
        "ghar"               : ["pm_awas"],
        "pmay"               : ["pm_awas"],
        "house"              : ["pm_awas"],
        "ayushman"           : ["ayushman_bharat"],
        "health insurance"   : ["ayushman_bharat"],
        "hospital"           : ["ayushman_bharat"],
        "pmjay"              : ["ayushman_bharat"],
        "health card"        : ["ayushman_bharat"],
        "irrigation"         : ["pm_krishi_sinchayee"],
        "sinchayee"          : ["pm_krishi_sinchayee"],
        "drip"               : ["pm_krishi_sinchayee"],
        "sprinkler"          : ["pm_krishi_sinchayee"],
        "organic"            : ["paramparagat_krishi"],
        "jaivik"             : ["paramparagat_krishi"],
        "paramparagat"       : ["paramparagat_krishi"],
        "pkvy"               : ["paramparagat_krishi"],
        "mandi"              : ["enam"],
        "enam"               : ["enam"],
        "e-nam"              : ["enam"],
        "agriculture market" : ["enam"],
        "soil"               : ["soil_health_card"],
        "mitti"              : ["soil_health_card"],
        "soil test"          : ["soil_health_card"],
        "lakhpati"           : ["lakhpati_didi"],
        "self help group"    : ["lakhpati_didi"],
        "shg"                : ["lakhpati_didi"],
        "drone"              : ["namo_drone_didi"],
        "drone didi"         : ["namo_drone_didi"],
        "namo drone"         : ["namo_drone_didi"],
    }

    def _get_focused_scheme_ids(self, query: str) -> list | None:
        query_lower = query.lower()
        matched     = []
        for kw in sorted(self.SCHEME_QUERY_MAP, key=len, reverse=True):
            if kw in query_lower:
                matched.extend(self.SCHEME_QUERY_MAP[kw])
        return list(set(matched)) if matched else None

    # ─────────────────────────────────────────────────────
    # FIX 1 + FIX 2: ELIGIBILITY CHECK — correct JSON keys
    # ─────────────────────────────────────────────────────

    def _get_eligible_scheme_names(self, profile: dict) -> dict:
        """
        Check eligibility for ALL schemes against user profile.

        KEY FIX: scheme_registry.json uses `eligibility` block with:
          - profession  (list of allowed professions)
          - max_income  (int or null)
          - age_min     (int)
          - age_max     (int or null)
          - gender      (str: "all", "Male", "Female")

        Old code used `eligibility_rules` → always got {} → all schemes
        passed all checks → student was getting farmer schemes.
        """
        import json as _json

        registry_path = os.path.join(
            os.path.dirname(__file__), "..",
            "knowledge_base", "scheme_registry.json"
        )

        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                registry = _json.load(f)["schemes"]
        except FileNotFoundError:
            print(f"[Generator] WARNING: scheme_registry.json not found")
            return {"eligible": [], "ineligible": []}
        except Exception as e:
            print(f"[Generator] WARNING: registry load failed — {e}")
            return {"eligible": [], "ineligible": []}

        age      = int(profile.get("age", 0) or 0)
        income   = int(profile.get("income", 0) or 0)
        prof     = (profile.get("profession") or "").lower().strip()
        gender   = (profile.get("gender") or "").strip()

        eligible_list   = []
        ineligible_list = []

        for scheme in registry:
            is_eligible = True
            reason      = "Matches your profile"

            # ── FIX: read from `eligibility`, not `eligibility_rules` ──
            rules = scheme.get("eligibility", {})

            # 1. Profession check — HIGHEST PRIORITY
            #    JSON stores: "profession": ["farmer"] or ["farmer","worker"]
            allowed_profs = [
                p.lower().strip() for p in rules.get("profession", [])
            ]
            if allowed_profs and prof:
                if prof not in allowed_profs:
                    is_eligible = False
                    reason = (
                        f"Only for: {', '.join(rules.get('profession', []))}"
                    )

            # 2. Income check
            if is_eligible:
                max_income = rules.get("max_income")
                if max_income is not None and income and income > max_income:
                    is_eligible = False
                    reason = (
                        f"Income ₹{income:,} exceeds "
                        f"scheme limit ₹{max_income:,}"
                    )

            # 3. Age check
            if is_eligible:
                min_age = rules.get("age_min", 0) or 0
                max_age = rules.get("age_max") or 999
                if age and not (min_age <= age <= max_age):
                    is_eligible = False
                    reason = (
                        f"Age {age} not in required range "
                        f"{min_age}–{max_age}"
                    )

            # 4. Gender check
            if is_eligible:
                req_gender = (rules.get("gender") or "all").strip().lower()
                if req_gender not in ["any", "all", ""]:
                    user_gender = gender.lower()
                    if user_gender and user_gender != req_gender:
                        is_eligible = False
                        reason = (
                            f"Only for {rules.get('gender')} applicants"
                        )

            description = scheme.get("description", "")
            key_benefit = scheme.get("benefit") or (
                description[:100] + "..."
                if len(description) > 100 else description
            )

            entry = {
                "scheme_name" : scheme.get("name") or scheme.get("id", ""),
                "scheme_id"   : scheme.get("id", ""),
                "key_benefit" : key_benefit,
                "eligible"    : is_eligible,
                "reason"      : reason,
                "priority"    : scheme.get("priority", 99),
                "profession"  : rules.get("profession", [])
            }

            if is_eligible:
                eligible_list.append(entry)
            else:
                ineligible_list.append(entry)

        return {"eligible": eligible_list, "ineligible": ineligible_list}

    # ─────────────────────────────────────────────────────
    # FIX 2: PROPER RANKING — profession > income > age > priority
    # ─────────────────────────────────────────────────────

    def _rank_eligible_schemes(
        self,
        eligible_list : list,
        profile       : dict,
        top_n         : int = 3
    ) -> list:
        """
        Score and rank eligible schemes so most relevant appear first.

        Scoring:
          +10  profession matches exactly (e.g. farmer → farmer scheme)
          +5   income is within the scheme's max_income limit
          +3   age is within min/max range
          +2   gender matches or scheme is for all genders
          -    lower registry priority number = higher ranking (tiebreak)

        Returns top_n schemes sorted by score descending.
        """
        age    = int(profile.get("age", 0) or 0)
        income = int(profile.get("income", 0) or 0)
        prof   = (profile.get("profession") or "").lower().strip()
        gender = (profile.get("gender") or "").lower().strip()

        scored = []
        for s in eligible_list:
            score = 0

            # Profession match — highest weight
            allowed_profs = [p.lower() for p in s.get("profession", [])]
            if prof and allowed_profs and prof in allowed_profs:
                score += 10

            # Income within range
            if income:
                score += 5   # already passed max_income check in eligibility

            # Age within range
            if age:
                score += 3   # already passed age check

            # Gender match
            score += 2       # already passed gender check

            # Use registry priority as tiebreaker (lower = better)
            priority = s.get("priority", 99)

            scored.append((score, priority, s))

        # Sort: higher score first, then lower priority number first
        scored.sort(key=lambda x: (-x[0], x[1]))

        return [item[2] for item in scored[:top_n]]

    # ─────────────────────────────────────────────────────
    # FILTER CHUNKS TO ELIGIBLE PDFs
    # ─────────────────────────────────────────────────────

    def _filter_chunks_to_eligible(
        self,
        context_chunks : list,
        eligible_schemes: dict
    ) -> list:
        """
        Remove chunks from non-eligible scheme PDFs.
        A student will never see PM Kisan text.
        Falls back to all chunks only if filter removes everything.
        """
        eligible_list = eligible_schemes.get("eligible", [])
        if not eligible_list or not context_chunks:
            return context_chunks

        match_keys = set()
        for s in eligible_list:
            name = (s.get("scheme_name") or "").strip()
            if not name:
                continue
            match_keys.add(name.lower().replace(" ", "_")[:12])
            words = name.lower().split()
            if words and len(words[0]) > 3:
                match_keys.add(words[0])

        filtered = [
            c for c in context_chunks
            if any(k in c.get("source", "").lower() for k in match_keys)
        ]
        return filtered if filtered else context_chunks

    # ─────────────────────────────────────────────────────
    # PROFILE CONFIRMATION
    # ─────────────────────────────────────────────────────

    def _confirm_profile(self, profile: dict, language: str) -> str:
        age    = profile.get("age",        "?")
        income = profile.get("income",     "?")
        state  = profile.get("state",      "?")
        cat    = profile.get("category",   "?")
        gender = profile.get("gender",     "?")
        prof   = profile.get("profession", "?")

        if "Hinglish" in language:
            return (
                f"Got it! Maine yeh save kar liya: 😊\n"
                f"• Umar     : {age} saal\n"
                f"• Income   : ₹{income}/year\n"
                f"• Kaam     : {prof}\n"
                f"• State    : {state}\n"
                f"• Category : {cat}\n"
                f"• Gender   : {gender}\n\n"
                f"Ab batao — kaunsi scheme ke baare mein jaanna chahte ho? 🎯"
            )
        elif "Hindi" in language:
            return (
                f"ठीक है! मैंने यह जानकारी सेव कर ली: 😊\n"
                f"• उम्र    : {age} वर्ष\n"
                f"• आय     : ₹{income}/वर्ष\n"
                f"• पेशा   : {prof}\n"
                f"• राज्य  : {state}\n"
                f"• श्रेणी : {cat}\n"
                f"• लिंग   : {gender}\n\n"
                f"अब बताइए — आप किस योजना के बारे में जानना चाहते हैं? 🎯"
            )
        else:
            return (
                f"Got it! Here's what I've saved: 😊\n"
                f"• Age       : {age}\n"
                f"• Income    : ₹{income}/year\n"
                f"• Profession: {prof}\n"
                f"• State     : {state}\n"
                f"• Category  : {cat}\n"
                f"• Gender    : {gender}\n\n"
                f"Now tell me — which scheme would you like to know about? 🎯"
            )

    # ─────────────────────────────────────────────────────
    # ASK FOR MISSING FIELDS
    # ─────────────────────────────────────────────────────

    def _ask_missing_fields(self, missing: list, language: str) -> str:
        labels = {
            "age"       : {"en": "your age",           "hi": "आपकी उम्र",      "hl": "tumhari age"},
            "income"    : {"en": "your annual income", "hi": "आपकी सालाना आय", "hl": "yearly income"},
            "profession": {"en": "your profession",    "hi": "आपका पेशा",      "hl": "tumhara kaam"},
            "state"     : {"en": "your state",         "hi": "आपका राज्य",     "hl": "tumhara state"},
        }
        if "Hinglish" in language:
            parts = [labels[f]["hl"] for f in missing if f in labels]
            return (
                f"Ek kaam karo — mujhe "
                f"{' aur '.join(parts)} batao, "
                f"toh main tumhare liye accurate schemes dhundh sakta hoon! 😊"
            )
        elif "Hindi" in language:
            parts = [labels[f]["hi"] for f in missing if f in labels]
            return (
                f"एक काम करें — मुझे "
                f"{' और '.join(parts)} बताएं, "
                f"तो मैं आपके लिए सटीक योजनाएं खोज सकूंगा! 😊"
            )
        else:
            parts = [labels[f]["en"] for f in missing if f in labels]
            return (
                f"Could you share "
                f"{' and '.join(parts)}? "
                f"It'll help me find the right schemes for you! 😊"
            )

    # ─────────────────────────────────────────────────────
    # MAIN GENERATE METHOD
    # ─────────────────────────────────────────────────────

    def generate(self, session_id: str, user_message: str, web_context: str = "") -> dict:
        """
        Main entry point. Returns structured JSON dict.
        """

        # ── Step 1: Language detection ────────────────────
        lang_code     = detect_language(user_message.strip())
        detected_lang = get_language_label(lang_code)
        lang_override = self._detect_language_override(user_message)

        # ── Step 2: Load memory ───────────────────────────
        history = get_history(session_id)
        profile = get_user_profile(session_id)

        # ── Step 3: Resolve language ──────────────────────
        language = self._get_conversation_language(
            detected_lang, history, lang_override
        )

        # ── Step 4: Extract profile from message ──────────
        updated_profile = self._extract_profile_from_reply(
            user_message, profile
        )
        profile_changed = updated_profile != profile
        if profile_changed:
            save_user_profile(session_id, updated_profile)
            profile = updated_profile

        # ── Step 5: Language-switch short-circuit ─────────

        if lang_override and len(user_message.split()) <= 6:
            switch_msg = {
                "Hindi (Devanagari script)":
                    "ठीक है! अब मैं हिंदी में बात करूंगा। क्या जानना है?",
                "Hinglish (casual mixed Hindi-English in Roman script)":
                    "Sure! Ab Hinglish mein baat karte hain. Kya jaanna chahte ho?",
                "English":
                    "Sure! I'll continue in English. What would you like to know?"
            }.get(lang_override, "Sure! What would you like to know?")

            save_message(session_id, "user",      user_message)
            save_message(session_id, "assistant", switch_msg)
            # FIX 3: always pass focused_scheme_ids=None to avoid TypeError
            return format_response(
                session_id         = session_id,
                user_message       = user_message,
                ai_answer          = switch_msg,
                language           = language,
                profile            = profile,
                history_length     = len(history),
                focused_scheme_ids = None
            )

        # ── Step 6: Detect query intent ───────────────────
        scheme_keywords = [
            "scheme", "yojana", "eligible", "apply", "benefit",
            "scholarship", "छात्रवृत्ति", "योजना", "पात्र", "आवेदन",
            "subsidy", "kisan", "farmer", "student", "help",
            "milega", "chahiye", "batao", "bataiye",
            "konsa", "kaun", "kya", "what", "how", "tell",
            "insurance", "bima", "loan", "credit", "housing",
            "ghar", "sabhi", "sab", "all", "best", "suggest",
            "recommend", "labour", "labor", "worker", "medical",
            "health", "solar", "irrigation", "organic", "drone"
        ]
        is_scheme_query = any(
            kw in user_message.lower() for kw in scheme_keywords
        )

        # ── Step 7: Profile-only message ──────────────────
        is_only_profile = (
            profile_changed
            and len(user_message.split()) <= 10
            and not is_scheme_query
            and "?" not in user_message
        )
        if is_only_profile:
            confirm_msg = self._confirm_profile(profile, language)
            save_message(session_id, "user",      user_message)
            save_message(session_id, "assistant", confirm_msg)
            return format_response(
                session_id         = session_id,
                user_message       = user_message,
                ai_answer          = confirm_msg,
                language           = language,
                profile            = profile,
                history_length     = len(history),
                focused_scheme_ids = None
            )

        # ── Step 8: Missing fields prompt ─────────────────
        required_fields  = ["age", "income", "profession", "state"]
        missing_required = [f for f in required_fields if not profile.get(f)]

        if (
            missing_required
            and is_scheme_query
            and len(history) < 6
            and len(history) % 4 == 0
            and not profile_changed
        ):
            ask_msg = self._ask_missing_fields(missing_required, language)
            save_message(session_id, "user",      user_message)
            save_message(session_id, "assistant", ask_msg)
            return format_response(
                session_id         = session_id,
                user_message       = user_message,
                ai_answer          = ask_msg,
                language           = language,
                profile            = profile,
                history_length     = len(history),
                focused_scheme_ids = None
            )

        # ── Step 9: Recommendation → collect profile first ─
        # ── News Mode — Latest schemes check ──────────────
        news_keywords = [
            "nayi scheme", "new scheme", "latest scheme",
            "2026", "abhi", "recently", "naya", "launch",
            "latest news", "koi nayi", "new government"
        ]
        is_news_query = any(
            kw in user_message.lower() for kw in news_keywords
        )

        if is_news_query and web_context:
            news_prompt = (
                f"USER'S QUESTION: {user_message}\n"
                f"LANGUAGE: {language}\n"
                f"LATEST NEWS:\n{web_context}\n"
                f"YOUR ANSWER: Based on latest news above, answer in {language}."
            )
            save_message(session_id, "user", user_message)
            try:
                news_response = self.client.chat.completions.create(
                    model       = MODEL_NAME,
                    messages    = [
                        {"role": "system", "content": get_system_prompt(language, profile)},
                        {"role": "user",   "content": news_prompt}
                    ],
                    max_tokens  = MAX_TOKENS,
                    temperature = TEMPERATURE
                )
                answer = news_response.choices[0].message.content.strip()
            except:
                answer = web_context
            save_message(session_id, "assistant", answer)
            return format_response(
                session_id         = session_id,
                user_message       = user_message,
                ai_answer          = answer,
                language           = language,
                profile            = profile,
                history_length     = len(history),
                focused_scheme_ids = None
            )

        # ── Step 10: Focused scheme from keywords ─────────
        focused_scheme_ids = self._get_focused_scheme_ids(user_message)

        # ── Step 11: FIX 1+2 — Compute eligible + rank ────
        #
        # _get_eligible_scheme_names() now reads correct JSON keys
        # _rank_eligible_schemes() sorts by profession > income > age
        # This replaces the broken [:3] slice.
        #
        eligible_schemes = self._get_eligible_scheme_names(profile)

        # FIX 2: rank before slicing — profession-matched schemes first
        top_3 = self._rank_eligible_schemes(
            eligible_list = eligible_schemes["eligible"],
            profile       = profile,
            top_n         = 3
        )

        # ── Step 12: Build FAISS query ────────────────────
        rag_query = self._build_rag_query(user_message, history)

        # ── Step 13: Retrieve from FAISS ──────────────────
        context_chunks = self.retriever.retrieve(rag_query)

        # Fallback if FAISS returns nothing
        if not context_chunks:
            import json as _json
            registry_path = os.path.join(
                os.path.dirname(__file__), "..",
                "knowledge_base", "scheme_registry.json"
            )
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    reg = _json.load(f)["schemes"]
                context_chunks = [
                    {"text": s["description"], "source": s["pdf_source"]}
                    for s in reg[:5]
                ]
            except Exception as e:
                print(f"[Generator] Fallback registry failed — {e}")
                context_chunks = []

        # Filter chunks to focused scheme PDFs (keyword match)
        if focused_scheme_ids:
            import json as _json
            registry_path = os.path.join(
                os.path.dirname(__file__), "..",
                "knowledge_base", "scheme_registry.json"
            )
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    reg = _json.load(f)["schemes"]
                focused_pdfs = {
                    s["pdf_source"] for s in reg
                    if s.get("id") in focused_scheme_ids
                }
                filtered = [
                    c for c in context_chunks
                    if c.get("source") in focused_pdfs
                ]
                if filtered:
                    context_chunks = filtered
            except Exception as e:
                print(f"[Generator] Focused filter failed — {e}")

        # Filter chunks to ONLY eligible scheme PDFs
        context_chunks = self._filter_chunks_to_eligible(
            context_chunks, eligible_schemes
        )

        # ── Step 14: Build LLM prompt ──────────────────────
        system_prompt = get_system_prompt(language, profile)

        user_prompt = get_rag_prompt(
    query          = user_message,
    context_chunks = context_chunks,
    language       = language,
    top_schemes    = top_3,
    web_context    = web_context
)
# Web search context add karo
        if web_context:
            user_prompt = user_prompt + "\n\n" + web_context

        recent_history = history[-MAX_HISTORY_FOR_LLM:]
        clean_history  = [
            {"role": m["role"], "content": m["content"]}
            for m in recent_history
        ]

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(clean_history)
        messages.append({"role": "user", "content": user_prompt})

        # ── Step 15: Call Groq LLM ─────────────────────────
        # FIX 4: increased retry wait to 10s, reduced retry tokens to 512
        try:
            response = self.client.chat.completions.create(
                model       = MODEL_NAME,
                messages    = messages,
                max_tokens  = MAX_TOKENS,
                temperature = TEMPERATURE
            )
            answer = response.choices[0].message.content.strip()

        except Exception as e:
            err_str = str(e).lower()
            if "rate_limit" in err_str:
                print(f"[Generator] Rate limit hit — waiting 10s then retry")
                time.sleep(10)
                try:
                    response = self.client.chat.completions.create(
                        model       = MODEL_NAME,
                        messages    = messages,
                        max_tokens  = 512,      # reduced for retry
                        temperature = TEMPERATURE
                    )
                    answer = response.choices[0].message.content.strip()
                except Exception as e2:
                    print(f"[Generator] Retry also failed: {e2}")
                    answer = self._fallback_answer(language)
            else:
                print(f"[Generator] LLM error: {e}")
                answer = self._fallback_answer(language)

        # ── Step 16: Save to memory ────────────────────────
        save_message(session_id, "user",      user_message)
        save_message(session_id, "assistant", answer)

        # ── Step 17: Return JSON ───────────────────────────
        # FIX 3: focused_scheme_ids always passed, never missing
        return format_response(
            session_id         = session_id,
            user_message       = user_message,
            ai_answer          = answer,
            language           = language,
            profile            = profile,
            history_length     = len(history),
            focused_scheme_ids = focused_scheme_ids
        )

    def _fallback_answer(self, language: str) -> str:
        """Safe fallback when LLM call fails — never shows raw error."""
        if "Devanagari" in language or (
            "Hindi" in language and "Hinglish" not in language
        ):
            return (
                "क्षमा करें, अभी सर्वर पर अधिक लोड है। "
                "कृपया कुछ सेकंड बाद फिर से प्रयास करें।"
            )
        elif "Hinglish" in language:
            return (
                "Server abhi busy hai. "
                "Thodi der baad dobara try karo."
            )
        else:
            return (
                "The server is temporarily busy. "
                "Please try again in a few seconds."
            )


# ── Quick test ───────────────────────────────────────────
if __name__ == "__main__":
    import json
    from memory.chat_memory import initialize_db, create_session

    initialize_db()
    gen = Generator()
    sid = create_session()

    print("=" * 60)
    print("SARKARI-MITRA — Terminal Test")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            result = gen.generate(sid, user_input)
            print(f"\nBot: {result['response']}")

            recs = result.get("scheme_recommendations", [])
            if recs:
                print("\n── Schemes ──")
                for s in recs:
                    icon = (
                        "✅" if s["eligible"] is True
                        else "⚠️" if s["eligible"] == "maybe"
                        else "❌"
                    )
                    print(f"{icon} {s['scheme_name']} — {s['reason']}")

            p = result.get("user_profile", {})
            if p.get("missing_fields"):
                print(f"── Missing: {p['missing_fields']}")

        except KeyboardInterrupt:
            print("\nBye!")
            break