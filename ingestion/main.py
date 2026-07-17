import asyncio
import structlog
from pathlib import Path

from app.core.db import db_manager, get_db
from ingestion.source_map import SOURCE_MAP
from ingestion.load_geojson import load_geojson_features
from ingestion.normalize import normalize_feature
from ingestion.upsert import upsert_features

logger = structlog.get_logger()

# Resolve data directory relative to this script
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

async def run_ingestion():
    logger.info("Starting GeoContext Data Ingestion...")
    await db_manager.connect()
    
    # Use the async generator to acquire a session
    session_gen = get_db()
    session = await anext(session_gen)
    
    try:
        for filename, config in SOURCE_MAP.items():
            filepath = DATA_DIR / filename
            model_name = config["model"]
            defaults = config["defaults"]
            defaults["model_type"] = model_name # Pass model_type explicitly for normalization hints
            
            logger.info(f"Processing {filename} into {model_name}...")
            
            batch = []
            seen_ids = set()
            count = 0
            
            # load_geojson_features will handle empty files gracefully
            for feature in load_geojson_features(filepath):
                try:
                    normalized = normalize_feature(feature, defaults)
                except Exception as e:
                    logger.error(f"Failed to normalize feature", error=str(e), feature_id=feature.get("id"))
                    continue

                identity = (normalized["osm_type"], normalized["osm_id"])
                if identity in seen_ids:
                    continue
                seen_ids.add(identity)

                batch.append(normalized)

                # Upsert in batches of 500
                if len(batch) >= 500:
                    try:
                        await upsert_features(session, model_name, batch)
                        await session.commit()
                        count += len(batch)
                    except Exception as e:
                        await session.rollback()
                        logger.error(f"Failed to upsert batch", error=str(e), filename=filename)
                    batch = []

            # Upsert any remaining records
            if batch:
                try:
                    await upsert_features(session, model_name, batch)
                    await session.commit()
                    count += len(batch)
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Failed to upsert final batch", error=str(e), filename=filename)
                
            if count == 0:
                logger.warning(f"No valid records processed for {filename}. Is the file empty?")
            else:
                logger.info(f"Completed {filename}", records_upserted=count)

    except StopAsyncIteration:
        pass
    finally:
        await db_manager.disconnect()
        logger.info("GeoContext Data Ingestion Complete.")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
