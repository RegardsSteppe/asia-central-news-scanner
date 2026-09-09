CENTRAL_ASIA_TERMS = [
    "central asia",
    "central asian",
    "kazakhstan",
    "kyrgyzstan",
    "tajikistan",
    "turkmenistan",
    "uzbekistan",
    "samarkand",
    "caspian",
    "trans-caspian",
    "eurasia",
]

SECURITY_TERMS = [
    "security",
    "defense",
    "defence",
    "deterrence",
    "military",
    "stability",
    "hedger",
    "pressure points",
    "competition",
]

ENERGY_CONNECTIVITY_TERMS = [
    "pipeline",
    "energy",
    "trade route",
    "trade routes",
    "corridor",
    "corridors",
    "connectivity",
    "transit",
    "infrastructure",
    "exports",
]

DIPLOMACY_TERMS = [
    "foreign policy",
    "partnership",
    "diplomacy",
    "diplomatic",
    "united nations",
    "un security council",
    "state department",
    "multilateral",
]

GREAT_POWER_TERMS = [
    "united states",
    "us ",
    "u.s.",
    "russia",
    "china",
    "iran",
    "europe",
    "ukraine",
    "taiwan",
    "indo-pacific",
]

LOW_SIGNAL_TERMS = [
    "analysis",
    "commentary",
    "strategy",
    "strategic",
]

NOISE_TERMS = [
    "podcast",
    "event",
    "video",
    "webinar",
]

SECURITY_WEIGHTS = {
    "security": 5,
    "deterrence": 6,
    "military": 5,
    "stability": 4,
    "competition": 3,
    "hedger": 4,
}

ENERGY_WEIGHTS = {
    "pipeline": 6,
    "energy": 5,
    "trade route": 4,
    "trade routes": 4,
    "corridor": 4,
    "corridors": 4,
    "connectivity": 4,
    "infrastructure": 3,
}

DIPLOMACY_WEIGHTS = {
    "foreign policy": 5,
    "partnership": 4,
    "diplomacy": 4,
    "diplomatic": 4,
    "united nations": 5,
    "un security council": 5,
    "state department": 5,
    "multilateral": 3,
}

GREAT_POWER_WEIGHTS = {
    "united states": 4,
    "russia": 4,
    "china": 4,
    "iran": 4,
    "europe": 3,
    "ukraine": 3,
    "taiwan": 4,
    "indo-pacific": 4,
}
