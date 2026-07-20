import hashlib
from typing import Any
import re
from shapely.geometry import shape

def _stable_hash(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest()[:12], 16)

def extract_osm_identity(feature_id: Any, feature: dict) -> tuple[str, int]:
    """Extracts osm_type and osm_id from an overpass-style ID like 'way/12345'."""
    if not feature_id:
        return "unknown", _stable_hash(str(feature))
    
    if isinstance(feature_id, int):
        return "node", feature_id
    
    match = re.match(r"(node|way|relation)/(\d+)", str(feature_id))
    if match:
        return match.group(1), int(match.group(2))
    
    return "unknown", _stable_hash(str(feature_id))

def normalize_feature(feature: dict[str, Any], defaults: dict[str, str]) -> dict[str, Any]:
    """Converts a raw GeoJSON feature into a dict ready for SQLAlchemy ingestion."""
    props = feature.get("properties", {})
    
    # Extract identity
    osm_type, osm_id = extract_osm_identity(feature.get("id"), feature)
    
    # Convert geometry to EWKT for GeoAlchemy2
    geom = shape(feature["geometry"])
    ewkt = f"SRID=4326;{geom.wkt}"
    
    # Extract names (handle varying key formats across GeoJSON sources)
    name = props.get("name") or props.get("name:en") or props.get("name_en") or props.get("shapeName") or props.get("name:ar") or "Unnamed"
    name_en = props.get("name:en") or props.get("name_en") or props.get("name") or None
    name_ar = props.get("name:ar") or props.get("name_ar") or None
    description = props.get("description", props.get("note", None))

    normalized = {
        "osm_type": osm_type,
        "osm_id": osm_id,
        "name": name,
        "geometry": ewkt
    }
    
    # Model-specific key padding to ensure consistent batch shapes
    model_type = defaults.get("model_type")
    if model_type == "Boundary":
        normalized["name_en"] = name_en or None
        normalized["name_ar"] = name_ar or None
    elif model_type == "Site":
        normalized["name_en"] = name_en or None
        normalized["name_ar"] = name_ar or None
        normalized["details"] = {"description": description} if description else None
    elif model_type == "RestrictedZone":
        normalized["reason"] = description or None

    # Merge predefined defaults (e.g. category="archaeological", level="country")
    for k, v in defaults.items():
        if k != "model_type":  # Skip internal markers
            normalized[k] = v
            
    return normalized
