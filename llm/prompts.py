# llm/prompts.py

def get_system_prompt(language: str, user_profile: dict) -> str:
    age      = user_profile.get('age',        'Not provided')
    income   = user_profile.get('income',     'Not provided')
    prof     = user_profile.get('profession', 'Not provided')
    state    = user_profile.get('state',      'Not provided')
    category = user_profile.get('category',   'Not provided')
    gender   = user_profile.get('gender',     'Not provided')

    profession_rule = ""
    prof_lower = str(prof).lower()
    if prof_lower == "student":
        profession_rule = (
            "PROFESSION = STUDENT → You MUST NOT recommend any of these:\n"
            "  PM Kisan, KCC, Kisan Credit Card, PM KUSUM, Fasal Bima,\n"
            "  Pradhan Mantri Krishi Sinchayee, Soil Health Card,\n"
            "  Paramparagat Krishi, eNAM, NAMO Drone Didi.\n"
            "  These are ALL farmer-only. Student is NOT a farmer."
        )
    elif prof_lower == "farmer":
        profession_rule = (
            "PROFESSION = FARMER → Farmer schemes are eligible.\n"
            "  Check income and state for exact eligibility."
        )
    elif prof_lower in ["worker", "labour", "labor"]:
        profession_rule = (
            "PROFESSION = WORKER/LABOUR → Focus on income-based and housing schemes.\n"
            "  Avoid farmer-specific schemes."
        )
    else:
        profession_rule = (
            f"PROFESSION = {prof} → Match schemes to this profession.\n"
            "  Do NOT suggest farmer schemes unless profession is farmer."
        )

    return f"""You are Sarkari-Mitra — a helpful assistant for Indian government schemes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE RULE (HIGHEST PRIORITY): {language}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ENGLISH input   → reply in English
- HINDI Devanagari → reply fully in Hindi
- HINGLISH Roman  → reply in Hinglish Roman script (casual mix)
- NEVER switch language unless user switches first

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER PROFILE:
- Age       : {age}
- Income    : ₹{income}/year
- Profession: {prof}
- State     : {state}
- Category  : {category}
- Gender    : {gender}

{profession_rule}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FORMAT: 1-2 sentence direct answer → bullets → one next step.

NEVER:
- Say "According to the document" or "As per the PDF"
- Use: maybe / might / possibly / could be
- Recommend > 3 schemes
- Recommend farmer schemes to non-farmers"""


def get_rag_prompt(
    query         : str,
    context_chunks: list,
    language      : str,
    top_schemes   : list = None,
    web_context   : str = "",
) -> str:
    top_schemes = top_schemes or []

    allowed   = []
    blocked   = []

    for s in top_schemes:
        name     = (s.get("scheme_name") or "").strip()
        benefit  = (s.get("key_benefit") or "").strip()
        eligible = s.get("eligible", False)
        reason   = (s.get("reason") or "").strip()

        if not name:
            continue

        if eligible is True or eligible == "maybe":
            allowed.append({
                "name"   : name,
                "benefit": benefit,
                "reason" : reason
            })
        else:
            blocked.append({
                "name"  : name,
                "reason": reason
            })

    allowed_keys = []
    for s in allowed:
        n = s["name"].lower()
        allowed_keys.append(n.replace(" ", "_")[:12])
        words = n.split()
        if words and len(words[0]) > 3:
            allowed_keys.append(words[0])

    filtered_ctx = ""
    for chunk in (context_chunks or []):
        src = chunk.get("source", "").lower()
        txt = chunk.get("text", "")
        if any(k in src for k in allowed_keys if k):
            filtered_ctx += f"\n{txt[:400]}\n"

    ctx_section = ""
    if filtered_ctx.strip():
        ctx_section = (
            "\nSCHEME DETAILS (official documents — for specific questions):"
            f"\n{filtered_ctx}"
        )

    # Web context section
    web_section = ""
    if web_context and web_context.strip():
        web_section = f"\nADDITIONAL WEB INFORMATION:\n{web_context}\n"

    if "Devanagari" in language or (
        "Hindi" in language and "Hinglish" not in language
    ):
        rec_prefix  = "आपकी प्रोफ़ाइल के अनुसार, यह योजनाएं आपके लिए हैं:"
        no_info_msg = "इस विषय पर पर्याप्त जानकारी नहीं है।"
        no_scheme   = (
            "आपकी प्रोफ़ाइल के लिए कोई उपयुक्त योजना नहीं मिली। "
            "कृपया अपना पेशा और आय बताएं।"
        )
    elif "Hinglish" in language:
        rec_prefix  = "Aapke profile ke hisaab se, yeh schemes aapke liye hain:"
        no_info_msg = "Is topic pe mere paas abhi info nahi hai."
        no_scheme   = (
            "Aapki profile ke liye koi eligible scheme nahi mili. "
            "Apna profession aur income share karo."
        )
    else:
        rec_prefix  = "Based on your profile, here are the schemes for you:"
        no_info_msg = "I don't have enough information on this right now."
        no_scheme   = (
            "No eligible schemes found for your profile. "
            "Please share your profession and income."
        )

    # Agar koi allowed scheme nahi hai — web context use karo
    if not allowed:
        return (
            f"USER'S QUESTION: {query}\n"
            f"LANGUAGE: {language}\n"
            f"{web_section}"
            f"YOUR ANSWER: Use the web information above if available to answer the question in {language}. "
            f"If no web info, say: {no_scheme}"
        )

    allowed_names_str = "\n".join(f"  ✓ {s['name']}" for s in allowed)
    allowed_detail_str = "\n".join(
        f"  • {s['name']}: {s['benefit']}"
        for s in allowed if s['benefit']
    )

    blocked_str = ""
    if blocked:
        blocked_names_str = "\n".join(
            f"  ✗ {s['name']} (reason: {s['reason']})"
            for s in blocked
        )
        blocked_str = (
            f"\nNEVER MENTION THESE SCHEMES — USER IS NOT ELIGIBLE:\n"
            f"{blocked_names_str}\n"
        )

    return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALLOWED SCHEMES — YOU MAY ONLY TALK ABOUT THESE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{allowed_names_str}

DETAILS:
{allowed_detail_str}
{blocked_str}{ctx_section}{web_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER'S QUESTION: {query}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES (violation = wrong answer):
1. ONLY mention schemes from the ALLOWED list above
2. NEVER mention schemes from the NEVER MENTION list
3. Max 2-3 schemes in your answer
4. State benefits directly — no hedging words
5. Recommend query → start: "{rec_prefix}"
6. Asked about scheme not in allowed list → use web info if available
7. Language: {language} — EXACT style
8. Hinglish = casual Roman script only, never Devanagari

YOUR ANSWER:"""


def get_profile_collection_prompt(missing_fields: list, language: str) -> str:
    if language == "Hindi (Devanagari script)":
        field_map = {
            "age"       : "• आपकी उम्र?",
            "income"    : "• सालाना घर की आमदनी? (रुपये में)",
            "profession": "• आप क्या करते हैं? (किसान / छात्र / मजदूर / व्यापार / अन्य)",
            "state"     : "• आप किस राज्य में रहते हैं?",
            "category"  : "• जाति श्रेणी? (SC / ST / OBC / सामान्य / अल्पसंख्यक)",
            "gender"    : "• लिंग? (पुरुष / महिला / अन्य)"
        }
        questions = "\n".join(
            field_map[f] for f in missing_fields if f in field_map
        )
        return (
            f"सही योजना ढूंढने के लिए कुछ जानकारी चाहिए! 😊\n\n"
            f"{questions}\n\n"
            f"यह बताइए, फिर मैं आपके लिए बेस्ट योजनाएं निकालूंगा! 🎯"
        )

    if language == "Hinglish (casual mixed Hindi-English in Roman script)":
        field_map = {
            "age"       : "• Tumhari age kya hai?",
            "income"    : "• Ghar ki yearly income kitni hai? (rupees mein)",
            "profession": "• Kya karte ho? (farmer / student / worker / business / other)",
            "state"     : "• Kaunse state mein rehte ho?",
            "category"  : "• Caste category? (SC / ST / OBC / General / Minority)",
            "gender"    : "• Gender? (Male / Female / Other)"
        }
        questions = "\n".join(
            field_map[f] for f in missing_fields if f in field_map
        )
        return (
            f"Sahi scheme suggest karne ke liye kuch basic info chahiye:\n\n"
            f"{questions}\n\n"
            f"Yeh share karo, accurate recommendation de sakta hoon."
        )

    field_map = {
        "age"       : "• Your age?",
        "income"    : "• Annual household income? (in rupees)",
        "profession": "• What do you do? (farmer / student / worker / business / other)",
        "state"     : "• Which state do you live in?",
        "category"  : "• Caste category? (SC / ST / OBC / General / Minority)",
        "gender"    : "• Gender? (Male / Female / Other)"
    }
    questions = "\n".join(
        field_map[f] for f in missing_fields if f in field_map
    )
    return (
        f"To find the best schemes for you, I need a few details:\n\n"
        f"{questions}\n\n"
        f"Share this and I'll give you accurate recommendations. 🎯"
    )