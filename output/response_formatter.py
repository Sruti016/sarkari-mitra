# output/response_formatter.py
# ─────────────────────────────────────────────────────────
# ROOT BUGS FIXED IN THIS VERSION:
#
# BUG 1 — Wrong schemes shown (student/labour gets farmer schemes)
#   Old logic: keyword-match query first → THEN check eligibility
#   Problem:   "scheme batao" / "labour" / "worker" matched farmer
#              keywords → farmer schemes passed into eligible list
#   Fix:       PROFESSION CHECK IS NOW GATE 1.
#              If profession doesn't match → scheme is skipped entirely.
#              Keyword match runs ONLY on schemes that already passed
#              the profession gate.
#
# BUG 2 — General queries ("sabhi scheme batao") show all schemes
#   Old logic: no profession gate → all 13 schemes returned
#   Fix:       When query is general (no specific keyword), return
#              ALL profession-eligible schemes ranked by priority.
#              This means a labour user gets housing + health schemes,
#              NOT PM Kisan / KCC / KUSUM.
#
# BUG 3 — "server busy" on first message from new chat
#   Old logic: format_response crashed when profile was empty {}
#              because check_eligibility did int() on None income
#   Fix:       All profile fields safely defaulted to 0 / ""
#              before any comparison. Never crashes on empty profile.
#
# PRESERVED:
#   - focused_scheme_ids filter (for direct scheme queries)
#   - priority-based ranking (eligible first, then priority number)
#   - description field in scheme cards
#   - sources field hidden from API response
# ─────────────────────────────────────────────────────────

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "knowledge_base",
    "scheme_registry.json"
)


def load_registry() -> list[dict]:
    """Load all schemes from registry JSON."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["schemes"]


def check_eligibility(scheme: dict, profile: dict) -> dict:
    """
    Check if a user is eligible for a scheme based on their profile.

    Returns:
    {
        "eligible"  : True / False / "maybe",
        "confidence": "high" / "medium" / "low",
        "reason"    : "Why eligible or not"
    }

    NOTE: This is called ONLY after the profession gate passes.
    So by the time we reach here, profession already matches.
    We only check income / gender / age / category here.
    """
    rules   = scheme.get("eligibility", {})
    reasons = []
    blocks  = []
    maybes  = []

    # ── Profession check (secondary confirmation) ─────────
    user_prof     = (profile.get("profession") or "").strip().lower()
    allowed_profs = [p.lower() for p in rules.get("profession", [])]
    if user_prof and allowed_profs:
        if user_prof not in allowed_profs:
            blocks.append(
                f"Scheme is for {', '.join(rules.get('profession', []))} "
                f"but your profession is {profile.get('profession', 'unknown')}"
            )
        else:
            reasons.append(f"Your profession ({profile.get('profession')}) matches")

    # ── Income check ──────────────────────────────────────
    user_income = int(profile.get("income") or 0)
    max_income  = rules.get("max_income")
    if user_income and max_income is not None:
        if user_income > max_income:
            blocks.append(
                f"Income ₹{user_income:,} exceeds limit of ₹{max_income:,}"
            )
        else:
            reasons.append(f"Income ₹{user_income:,} is within limit")

    # ── Gender check ──────────────────────────────────────
    required_gender = (rules.get("gender") or "all").lower().strip()
    user_gender     = (profile.get("gender") or "").lower().strip()
    if required_gender not in ["any", "all", ""]:
        if user_gender and user_gender != required_gender:
            blocks.append(
                f"This scheme is only for {rules.get('gender')} applicants"
            )
        elif not user_gender:
            maybes.append("Gender not provided — scheme may be gender-specific")

    # ── Category exclusion check ──────────────────────────
    excluded_cats = [c.upper() for c in rules.get("excluded_categories", [])]
    user_category = (profile.get("category") or "").upper().strip()
    if excluded_cats and user_category and user_category in excluded_cats:
        blocks.append(
            f"{user_category} category is excluded from this scheme"
        )

    # ── Age check ─────────────────────────────────────────
    user_age = int(profile.get("age") or 0)
    if user_age:
        age_min = rules.get("age_min") or 0
        age_max = rules.get("age_max") or 999
        if user_age < age_min:
            blocks.append(f"Minimum age required is {age_min}")
        if user_age > age_max:
            blocks.append(f"Maximum age limit is {age_max}")

    # ── Special conditions ────────────────────────────────
    special = rules.get("special")
    if special:
        maybes.append(f"Additional condition: {special}")

    # ── Final decision ────────────────────────────────────
    if blocks:
        return {
            "eligible"  : False,
            "confidence": "high" if len(blocks) > 1 else "medium",
            "reason"    : blocks[0]
        }
    elif maybes and not reasons:
        return {
            "eligible"  : "maybe",
            "confidence": "low",
            "reason"    : maybes[0]
        }
    elif maybes:
        return {
            "eligible"  : "maybe",
            "confidence": "medium",
            "reason"    : f"{reasons[0]}. But: {maybes[0]}"
        }
    else:
        return {
            "eligible"  : True,
            "confidence": "high",
            "reason"    : reasons[0] if reasons else "Meets all basic criteria"
        }


def _profession_passes_gate(scheme: dict, user_prof: str) -> bool:
    """
    BUG FIX GATE 1 — profession must match before anything else.

    If profession is unknown (empty profile), we let it through
    so new users still see schemes (with "maybe" eligibility).

    If profession IS known, it MUST appear in the scheme's
    allowed profession list — no exceptions.

    Examples:
      user_prof="student", scheme allows ["farmer"] → False (blocked)
      user_prof="farmer",  scheme allows ["farmer"] → True  (pass)
      user_prof="worker",  scheme allows ["farmer","worker"] → True
      user_prof="",        any scheme → True (unknown, show all)
    """
    if not user_prof:
        return True   # Unknown profession → show all (with "maybe")

    allowed_profs = [p.lower().strip() for p in
                     scheme.get("eligibility", {}).get("profession", [])]

    if not allowed_profs:
        return True   # Scheme has no profession restriction → anyone eligible

    return user_prof.lower().strip() in allowed_profs


def find_relevant_schemes(
    query              : str,
    sources_used       : list[str],
    profile            : dict,
    focused_scheme_ids : list[str] = None
) -> list[dict]:
    """
    Find which schemes are relevant to this query.

    NEW STRATEGY (fixes BUG 1 + BUG 2):
    ─────────────────────────────────────
    GATE 1 — Profession filter (HARD GATE, runs first)
      → Schemes whose profession list doesn't include user's
        profession are SKIPPED entirely. Never reach keyword check.

    GATE 2 — Relevance filter (runs only on profession-passed schemes)
      → If focused_scheme_ids given (direct query like "PM Kisan batao"):
          only return those specific schemes
      → If general query ("sabhi schemes", "best scheme for me"):
          return ALL profession-eligible schemes (ranked by priority)
      → If specific keywords in query:
          match those keywords against scheme keyword list

    GATE 3 — Eligibility check (income / age / gender / category)
      → Full eligibility check for display + sorting

    This means:
      - labour user NEVER sees PM Kisan / KCC / KUSUM
      - farmer user NEVER sees scholarship schemes
      - general "all schemes" query returns profession-filtered list
    """
    try:
        schemes = load_registry()
    except Exception as e:
        print(f"[ResponseFormatter] WARNING: Could not load registry — {e}")
        return []

    user_prof   = (profile.get("profession") or "").strip().lower()
    query_lower = query.lower()

    # ── Is this a general "show all" query? ───────────────
    # If yes, skip keyword matching and return all profession-eligible schemes
    general_keywords = [
        "sabhi", "sab", "all scheme", "all yojana", "sabhi scheme",
        "konsi milegi", "best scheme", "suggest", "recommend",
        "kaunsi", "konsi", "which scheme", "list", "batao",
        "mere liye", "for me", "mujhe", "show me"
    ]
    is_general_query = any(kw in query_lower for kw in general_keywords)

    relevant = []

    for scheme in schemes:

        # ── GATE 1: Profession must match ─────────────────
        # This is the fix — no keyword matching bypasses this gate
        if not _profession_passes_gate(scheme, user_prof):
            continue   # Skip this scheme entirely — wrong profession

        # ── GATE 2: Relevance check ────────────────────────

        is_relevant = False

        # 2a. Focused scheme IDs (direct query: "PM Kisan ke baare mein")
        if focused_scheme_ids:
            if scheme.get("id") in focused_scheme_ids:
                is_relevant = True

        # 2b. General query → all profession-eligible schemes are relevant
        elif is_general_query:
            is_relevant = True

        # 2c. Keyword match for specific but non-focused queries
        else:
            matched_keywords = [
                kw for kw in scheme.get("keywords", [])
                if kw.lower() in query_lower
            ]
            if matched_keywords:
                is_relevant = True
            # Also match by PDF source if retriever returned it
            if sources_used and scheme.get("pdf_source") in sources_used:
                is_relevant = True

        if not is_relevant:
            continue

        # ── GATE 3: Full eligibility check ────────────────
        eligibility = check_eligibility(scheme, profile)

        relevant.append({
            "scheme_id"   : scheme.get("id", ""),
            "scheme_name" : scheme.get("name", "Unknown Scheme"),
            "source_pdf"  : scheme.get("pdf_source", ""),
            "category"    : scheme.get("category", ""),
            "description" : scheme.get("description", ""),
            "eligible"    : eligibility["eligible"],
            "confidence"  : eligibility["confidence"],
            "key_benefit" : scheme.get("benefit", ""),
            "reason"      : eligibility["reason"],
            "apply_url"   : scheme.get("apply_url", ""),
            "_priority"   : scheme.get("priority", 999)
        })

    # ── Ranking: eligible first, then by registry priority ─
    order = {True: 0, "maybe": 1, False: 2}
    relevant.sort(key=lambda x: (
        order.get(x["eligible"], 3),
        x.get("_priority", 999)
    ))

    # Remove internal _priority field before returning
    for r in relevant:
        r.pop("_priority", None)

    return relevant


def format_response(
    session_id         : str,
    user_message       : str,
    ai_answer          : str,
    language           : str,
    profile            : dict,
    history_length     : int,
    focused_scheme_ids : list[str] = None,
    **kwargs
) -> dict:
    """
    MAIN FUNCTION — builds the full structured JSON response.
    Called by generator.py after getting LLM answer.

    BUG 3 FIX: profile can be empty {} on first message.
    All downstream functions now safely handle None/missing values.
    """

    # Internal sources for scheme matching (not exposed in response)
    internal_sources = kwargs.get("_sources_internal", [])

    # Find relevant schemes + check eligibility
    scheme_recommendations = find_relevant_schemes(
        query              = user_message,
        sources_used       = internal_sources,
        profile            = profile or {},
        focused_scheme_ids = focused_scheme_ids
    )

    # Build profile_complete flag
    required = ["age", "income", "profession", "state"]
    missing  = [f for f in required if not (profile or {}).get(f)]

    return {
        # ── Core response ──────────────────────────────────
        "session_id" : session_id,
        "response"   : ai_answer,
        "language"   : language,

        # ── Profile intelligence ───────────────────────────
        "user_profile": {
            "age"             : (profile or {}).get("age"),
            "income"          : (profile or {}).get("income"),
            "profession"      : (profile or {}).get("profession"),
            "state"           : (profile or {}).get("state"),
            "category"        : (profile or {}).get("category"),
            "gender"          : (profile or {}).get("gender"),
            "profile_complete": len(missing) == 0,
            "missing_fields"  : missing
        },

        # ── Scheme recommendations ─────────────────────────
        "scheme_recommendations": scheme_recommendations,

        # ── Conversation metadata ──────────────────────────
        "conversation": {
            "language"      : language,
            "total_messages": history_length + 1
        }
    }


# ── Quick test ──────────────────────────────────────────
if __name__ == "__main__":

    # Test 1: Labour profile — must NOT get farmer schemes
    print("\n" + "=" * 60)
    print("TEST 1: Labour profile — no farmer schemes allowed")
    print("=" * 60)
    labour_profile = {
        "age"       : 40,
        "income"    : 80000,
        "profession": "worker",
        "state"     : "Bihar",
        "gender"    : "Male"
    }
    result = format_response(
        session_id    = "test-labour",
        user_message  = "Tell me which scheme is best for me",
        ai_answer     = "Based on your profile...",
        language      = "Hindi",
        profile       = labour_profile,
        history_length= 2
    )
    print("Schemes shown to labour user:")
    farmer_schemes = {"pm_kisan","kisan_credit_card","pm_kusum",
                      "pm_fasal_bima","pm_krishi_sinchayee",
                      "paramparagat_krishi","enam","soil_health_card"}
    passed = True
    for s in result["scheme_recommendations"]:
        icon = "✅" if s["eligible"] is True else ("⚠️" if s["eligible"] == "maybe" else "❌")
        print(f"  {icon} {s['scheme_name']} (id={s['scheme_id']})")
        if s["scheme_id"] in farmer_schemes:
            print(f"     ❌ FAIL — farmer scheme shown to labour user!")
            passed = False
    print(f"\n{'PASS ✅' if passed else 'FAIL ❌'} — No farmer schemes for labour user")

    # Test 2: Farmer profile — must get farmer schemes
    print("\n" + "=" * 60)
    print("TEST 2: Farmer profile — farmer schemes must appear")
    print("=" * 60)
    farmer_profile = {
        "age"       : 40,
        "income"    : 200000,
        "profession": "farmer",
        "state"     : "Madhya Pradesh",
        "gender"    : "Male"
    }
    result2 = format_response(
        session_id    = "test-farmer",
        user_message  = "sabhi scheme batao",
        ai_answer     = "Aapke liye yeh schemes hain...",
        language      = "Hinglish",
        profile       = farmer_profile,
        history_length= 2
    )
    farmer_ids = [s["scheme_id"] for s in result2["scheme_recommendations"]]
    print("Schemes shown to farmer:")
    for s in result2["scheme_recommendations"]:
        icon = "✅" if s["eligible"] is True else ("⚠️" if s["eligible"] == "maybe" else "❌")
        print(f"  {icon} {s['scheme_name']}")
    has_farmer = any(sid in farmer_ids for sid in ["pm_kisan","kisan_credit_card"])
    print(f"\n{'PASS ✅' if has_farmer else 'FAIL ❌'} — Farmer schemes present")

    # Test 3: Empty profile — must not crash
    print("\n" + "=" * 60)
    print("TEST 3: Empty profile — must not crash")
    print("=" * 60)
    try:
        result3 = format_response(
            session_id    = "test-empty",
            user_message  = "sabhi scheme batao",
            ai_answer     = "Please share your profile...",
            language      = "Hindi",
            profile       = {},
            history_length= 0
        )
        print("PASS ✅ — No crash on empty profile")
        print(f"  Schemes returned: {len(result3['scheme_recommendations'])}")
    except Exception as e:
        print(f"FAIL ❌ — Crashed: {e}")

    # Test 4: Student profile — must NOT get farmer schemes
    print("\n" + "=" * 60)
    print("TEST 4: Student profile — no farmer schemes")
    print("=" * 60)
    student_profile = {
        "age"       : 25,
        "income"    : 100000,
        "profession": "student",
        "state"     : "Madhya Pradesh",
        "gender"    : "Male"
    }
    result4 = format_response(
        session_id    = "test-student",
        user_message  = "konsi scheme milegi",
        ai_answer     = "Based on your profile...",
        language      = "English",
        profile       = student_profile,
        history_length= 1
    )
    passed4 = True
    print("Schemes shown to student:")
    for s in result4["scheme_recommendations"]:
        icon = "✅" if s["eligible"] is True else ("⚠️" if s["eligible"] == "maybe" else "❌")
        print(f"  {icon} {s['scheme_name']} (id={s['scheme_id']})")
        if s["scheme_id"] in farmer_schemes:
            print(f"     ❌ FAIL — farmer scheme shown to student!")
            passed4 = False
    print(f"\n{'PASS ✅' if passed4 else 'FAIL ❌'} — No farmer schemes for student")