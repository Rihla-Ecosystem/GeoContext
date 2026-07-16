from typing import Any
import re
from shapely.geometry import shape

def extract_osm_identity(feature_id: Any) -> tuple[str, int]:
    """Extracts osm_type and osm_id from an overpass-style ID like 'way/12345'."""
    if not feature_id:
        return "unknown", 0
    if isinstance(feature_id, int):
        return "node", feature_id # Default fallback if just int
    
    match = re.match(r"(node|way|relation)/(\d+)", str(feature_id))
    if match:
        return match.group(1), int(match.group(2))
    
    # Fallback for unexpected string IDs to ensure integer osm_id
    return "unknown", abs(hash(str(feature_id))) % (10 ** 12)

def normalize_feature(feature: dict[str, Any], defaults: dict[str, str]) -> dict[str, Any]:
    """Converts a raw GeoJSON feature into a dict ready for SQLAlchemy ingestion."""
    props = feature.get("properties", {})
    
    # Extract identity
    osm_type, osm_id = extract_osm_identity(feature.get("id"))
    
    # Convert geometry to EWKT for GeoAlchemy2
    geom = shape(feature["geometry"])
    ewkt = f"SRID=4326;{geom.wkt}"
    
    # Extract names
    name = props.get("name", props.get("name:en", "Unnamed"))
    name_en = props.get("name:en")
    name_ar = props.get("name:ar")
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
        normalized["description"] = description or None
    elif model_type == "RestrictedZone":
        normalized["reason"] = description or None

    # Merge predefined defaults (e.g. category="archaeological", level="country")
    for k, v in defaults.items():
        if k != "model_type":  # Skip internal markers
            normalized[k] = v
            
    return normalized
