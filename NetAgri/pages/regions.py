"""
Reference data for the North Eastern Region (NER).

Used by the dashboard to:
  * let a user pick their location manually when GPS is unavailable or denied
  * label a detected GPS position ("Near Jorhat, Assam")

Coordinates are approximate town centres (good to ~1-2 km), which is plenty for
weather lookups. Add more towns/districts here as the project grows - nothing
else needs to change.
"""

# Rough bounding box around the eight NER states, used to warn when a detected
# position is outside the region this prototype is built for.
NER_BOUNDS = {"south": 21.9, "north": 29.5, "west": 87.9, "east": 97.5}

# state -> list of (place name, latitude, longitude). The first entry of each
# state is its capital and is the default when that state is picked.
NER_PLACES = {
    "Arunachal Pradesh": [
        ("Itanagar", 27.0844, 93.6053),
        ("Tawang", 27.5860, 91.8594),
        ("Ziro", 27.5450, 93.8340),
        ("Pasighat", 28.0660, 95.3260),
    ],
    "Assam": [
        ("Guwahati", 26.1445, 91.7362),
        ("Dibrugarh", 27.4728, 94.9120),
        ("Dhemaji", 27.4833, 94.5833),
        ("Dhubri", 26.0200, 89.9800),
        ("Goalpara", 26.1667, 90.6167),
        ("Jorhat", 26.7509, 94.2037),
        ("Kokrajhar", 26.4000, 90.2700),
        ("Majuli (Garamur)", 26.9500, 94.1667),
        ("North Lakhimpur", 27.2360, 94.1010),
        ("Silchar", 24.8333, 92.7789),
        ("Tezpur", 26.6528, 92.7926),
    ],
    "Manipur": [
        ("Imphal", 24.8170, 93.9368),
        ("Churachandpur", 24.3333, 93.6833),
        ("Ukhrul", 25.1167, 94.3667),
    ],
    "Meghalaya": [
        ("Shillong", 25.5788, 91.8933),
        ("Tura", 25.5142, 90.2022),
    ],
    "Mizoram": [
        ("Aizawl", 23.7271, 92.7176),
        ("Lunglei", 22.8880, 92.7360),
    ],
    "Nagaland": [
        ("Kohima", 25.6751, 94.1086),
        ("Dimapur", 25.9063, 93.7276),
        ("Mokokchung", 26.3220, 94.5150),
    ],
    "Sikkim": [
        ("Gangtok", 27.3314, 88.6138),
        ("Namchi", 27.1667, 88.3500),
    ],
    "Tripura": [
        ("Agartala", 23.8315, 91.2868),
        ("Udaipur", 23.5333, 91.4833),
    ],
}


def places_for_frontend():
    """Shape the data for the template's json_script (stable, JSON-friendly)."""
    return {
        "bounds": NER_BOUNDS,
        "states": [
            {
                "name": state,
                "places": [
                    {"name": name, "lat": lat, "lon": lon}
                    for name, lat, lon in places
                ],
            }
            for state, places in NER_PLACES.items()
        ],
    }
