SOURCE_MAP = {
    "EgyptBoundries.geojson": {"model": "Boundary", "defaults": {"level": "country"}},
    "GovernratesBoundries.json": {"model": "Boundary", "defaults": {"level": "governorate"}},
    "EgyptSites.geojson": {"model": "Site", "defaults": {"categories": ["archaeological"], "site_type": "tourist"}},
    "IslamicSites.geojson": {"model": "Site", "defaults": {"categories": ["islamic"], "site_type": "tourist"}},
    "ChristianSites.geojson": {"model": "Site", "defaults": {"categories": ["christian"], "site_type": "tourist"}},
    "GovernmentalSites.geojson": {"model": "Site", "defaults": {"categories": ["infrastructure"], "site_type": "infrastructure"}},
    "ProtectedAreas.geojson": {"model": "RestrictedZone", "defaults": {"subtype": "protected", "source": "osm", "zone_type": "protected"}},
    "Ristracted.geojson": {"model": "RestrictedZone", "defaults": {"subtype": "military", "source": "osm", "zone_type": "restricted"}},
    "NonAttractionAreas.geojson": {"model": "RestrictedZone", "defaults": {"subtype": "informal_settlement", "source": "osm", "zone_type": "caution"}},
}
