# agent/profile_agent.py
# ─────────────────────────────────────────────────────────
# PURPOSE: Manages profile field requirements and
#          smart detection of which fields to ask for
# UPDATED: Added get_missing_fields alias used by generator
# ─────────────────────────────────────────────────────────

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ── Field definitions ─────────────────────────────────────

REQUIRED_PROFILE_FIELDS = [
    "age",
    "income",
    "profession",
    "state",
    "category",     # SC / ST / OBC / General / Minority
    "gender"        # Male / Female / Other
]

SCHOLARSHIP_REQUIRED_FIELDS = [
    "age",
    "income",
    "category",     # Most scholarships are category-specific
    "gender",       # Some scholarships are gender-specific
    "state"
]

FARMER_REQUIRED_FIELDS = [
    "age",
    "income",
    "state",
    "profession"
]

HOUSING_REQUIRED_FIELDS = [
    "age",
    "income",
    "state",
    "gender"        # PM Awas has female priority
]


def get_missing_fields(profile: dict, field_set: list = None) -> list[str]:
    """
    Return list of fields not yet collected.

    Args:
        profile   : Current user profile dict
        field_set : Which fields to check (default: all required)

    Returns:
        List of missing field name strings
    """
    fields_to_check = field_set or REQUIRED_PROFILE_FIELDS
    return [f for f in fields_to_check if not profile.get(f)]


def is_profile_complete(profile: dict, field_set: list = None) -> bool:
    """Return True if all required fields are filled."""
    return len(get_missing_fields(profile, field_set)) == 0


def is_scholarship_query(text: str) -> bool:
    """Detect if user is asking about scholarships."""
    keywords = [
        "scholarship", "छात्रवृत्ति", "stipend", "education loan",
        "study", "college fee", "tuition", "merit", "post matric",
        "pre matric", "yashasvi", "vidya lakshmi", "nsp", "padhai ke liye"
    ]
    return any(kw in text.lower() for kw in keywords)


def is_farmer_query(text: str) -> bool:
    """Detect if user is asking about farmer schemes."""
    keywords = [
        "farmer", "kisan", "किसान", "agriculture", "crop", "fasal",
        "pm kisan", "krishi", "खेती", "subsidy", "irrigation", "sinchai"
    ]
    return any(kw in text.lower() for kw in keywords)


def is_housing_query(text: str) -> bool:
    """Detect if user is asking about housing schemes."""
    keywords = [
        "house", "housing", "awas", "ghar", "घर", "pm awas",
        "pradhan mantri awas", "home loan", "construction"
    ]
    return any(kw in text.lower() for kw in keywords)


def get_relevant_missing_fields(profile: dict, user_message: str) -> list[str]:
    """
    Smart field detection — only asks for fields relevant to query type.

    Examples:
    - Scholarship query → needs category + gender
    - Farmer query      → needs profession + state
    - Housing query     → needs income + gender
    - General query     → needs all fields

    Args:
        profile     : Current user profile
        user_message: What user just asked

    Returns:
        List of missing fields relevant to this query
    """
    if is_scholarship_query(user_message):
        return get_missing_fields(profile, SCHOLARSHIP_REQUIRED_FIELDS)
    elif is_farmer_query(user_message):
        return get_missing_fields(profile, FARMER_REQUIRED_FIELDS)
    elif is_housing_query(user_message):
        return get_missing_fields(profile, HOUSING_REQUIRED_FIELDS)
    else:
        return get_missing_fields(profile, REQUIRED_PROFILE_FIELDS)


def summarize_profile(profile: dict) -> str:
    """
    Human-readable profile summary.
    Used in logs, debug output, and confirm messages.
    """
    if not profile:
        return "No profile collected yet."

    lines = []
    if profile.get("age")       : lines.append(f"Age: {profile['age']}")
    if profile.get("income")    : lines.append(f"Income: ₹{profile['income']:,}/year")
    if profile.get("profession"): lines.append(f"Profession: {profile['profession'].title()}")
    if profile.get("state")     : lines.append(f"State: {profile['state']}")
    if profile.get("category")  : lines.append(f"Category: {profile['category']}")
    if profile.get("gender")    : lines.append(f"Gender: {profile['gender']}")

    return " | ".join(lines) if lines else "Profile is empty."


# ── Quick test ────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("PROFILE AGENT TEST")
    print("=" * 55)

    # Test 1: Empty profile
    profile = {}
    print(f"Missing (empty)      : {get_missing_fields(profile)}")

    # Test 2: Partial profile
    profile = {"age": 20, "profession": "student", "category": "SC"}
    print(f"Missing (partial)    : {get_missing_fields(profile)}")

    # Test 3: Scholarship query
    msg = "I want scholarship for SC students"
    print(f"Missing (scholarship): {get_relevant_missing_fields(profile, msg)}")

    # Test 4: Farmer query
    msg      = "PM Kisan eligibility batao"
    profile2 = {"age": 45, "state": "MP"}
    print(f"Missing (farmer)     : {get_relevant_missing_fields(profile2, msg)}")

    # Test 5: Housing query
    msg      = "PM Awas Yojana ke liye eligible hoon?"
    profile3 = {"age": 30, "income": 200000}
    print(f"Missing (housing)    : {get_relevant_missing_fields(profile3, msg)}")

    # Test 6: Full profile summary
    full = {
        "age": 20, "income": 150000, "profession": "student",
        "state": "Madhya Pradesh", "category": "SC", "gender": "Female"
    }
    print(f"Profile summary      : {summarize_profile(full)}")
    print(f"Complete             : {is_profile_complete(full)}")