# Maps filename to Model, Subtype/Category/Level
SOURCE_MAP = {
    "EgyptBoundries.geojson": {"model": "Boundary", "defaults": {"level": "country"}},
    "GovernratesBoundries.json": {"model": "Boundary", "defaults": {"level": "governorate"}},
    "EgyptSites.geojson": {"model": "Site", "defaults": {"category": "archaeological"}},
    "IslamicSites.geojson": {"model": "Site", "defaults": {"category": "islamic"}},
    "ChristianSites.geojson": {"model": "Site", "defaults": {"category": "christian"}},
    "ProtectedAreas.geojson": {"model": "RestrictedZone", "defaults": {"subtype": "protected", "source": "osm"}},
    "Ristracted.geojson": {"model": "RestrictedZone", "defaults": {"subtype": "military", "source": "osm"}},
}
