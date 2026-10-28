import requests

GBIF_URL = "https://api.gbif.org/v1/occurrence/search"


def get_species_nearby(lat, lon, radius_m=500, limit=300):
    """Holt Beobachtungen im Radius um einen Standort."""
    params = {
        "geoDistance": f"{lat},{lon},{radius_m}m",
        "hasCoordinate": "true",
        "limit": limit,
    }
    data = requests.get(GBIF_URL, params=params, timeout=30).json()
    results = data.get("results", [])

    species = {}
    points = []
    for record in results:
        name = record.get("species")
        if not name:
            continue
        entry = species.setdefault(
            name,
            {"kingdom": record.get("kingdom"), "class": record.get("class"), "beobachtungen": 0},
        )
        entry["beobachtungen"] += 1
        if record.get("decimalLatitude") is not None:
            points.append(
                {"lat": record["decimalLatitude"], "lon": record["decimalLongitude"], "art": name}
            )

    return {
        "total_observations": data.get("count", 0),
        "used_observations": len(results),
        "species": species,
        "points": points,
    }
