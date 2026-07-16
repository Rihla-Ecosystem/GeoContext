import json
from pathlib import Path

def load_geojson_features(filepath: str | Path):
    """Yields parsed feature dictionaries from a GeoJSON file. Safely skips empty files."""
    path = Path(filepath)
    if not path.exists() or path.stat().st_size == 0:
        return
        
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for feature in data.get('features', []):
            yield feature
