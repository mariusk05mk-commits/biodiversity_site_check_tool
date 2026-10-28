import requests
from concurrent.futures import ThreadPoolExecutor

API = "https://api.gbif.org/v1"

# GBIF liefert den Status mal als Kürzel, mal als Langtext, beides wird vereinheitlicht
STATUS_MAP = {
    "CR": "CR", "CRITICALLY_ENDANGERED": "CR",
    "EN": "EN", "ENDANGERED": "EN",
    "VU": "VU", "VULNERABLE": "VU",
    "NT": "NT", "NEAR_THREATENED": "NT",
    "LC": "LC", "LEAST_CONCERN": "LC",
    "DD": "DD", "DATA_DEFICIENT": "DD",
    "NE": "NE", "NOT_EVALUATED": "NE",
}


def _get(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=20)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def get_species_info(name):
    """Deutscher Name und IUCN-Status (global) für eine Art."""
    match = _get(f"{API}/species/match", {"name": name})
    key = match.get("usageKey")
    if not key:
        return {"Art (lat.)": name, "Deutscher Name": None, "IUCN": None}

    # 1. Versuch: IUCN-Kategorie direkt, 2. Versuch: Artprofil
    raw = _get(f"{API}/species/{key}/iucnRedListCategory").get("category")
    if not raw:
        for entry in _get(f"{API}/species/{key}/speciesProfiles").get("results", []):
            if entry.get("threatStatus"):
                raw = entry["threatStatus"]
                break

    names = _get(f"{API}/species/{key}/vernacularNames", {"limit": 100}).get("results", [])
    deutsch = next((n["vernacularName"] for n in names if n.get("language") == "deu"), None)

    return {"Art (lat.)": name, "Deutscher Name": deutsch, "IUCN": STATUS_MAP.get(raw)}


def get_many(names):
    """Fragt mehrere Arten parallel ab (sonst dauert es sehr lange)."""
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(get_species_info, names))
      