from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text
from app.models import Boundary, Site, RestrictedZone

MODEL_REGISTRY = {
    "Boundary": Boundary,
    "Site": Site,
    "RestrictedZone": RestrictedZone,
}

async def upsert_features(session: AsyncSession, model_name: str, features: list[dict]):
    if not features:
        return
        
    model = MODEL_REGISTRY[model_name]
    
    # Postgres ON CONFLICT requires a unique constraint target.
    if model_name == "Boundary":
        constraint = "uq_boundary_osm_identity"
    elif model_name == "Site":
        constraint = "uq_site_osm_identity"
    elif model_name == "RestrictedZone":
        constraint = "uq_restricted_zone_osm_identity"
    else:
        raise ValueError(f"Unknown model: {model_name}")

    # Build the insert statement
    stmt = insert(model).values(features)
    
    # Filter out fields we don't want to update during conflict (like ID, created_at, osm identity)
    update_dict = {
        c.name: c for c in stmt.excluded 
        if c.name not in ('id', 'created_at', 'osm_type', 'osm_id')
    }
    
    # Merge categories idempotently instead of overwriting
    if model_name == "Site":
        update_dict["categories"] = text("ARRAY(SELECT DISTINCT UNNEST(sites.categories || EXCLUDED.categories))")
    
    # Configure the ON CONFLICT DO UPDATE behavior
    if model_name == "RestrictedZone":
        # RestrictedZone has a partial index: only unique where osm_id is not null
        stmt = stmt.on_conflict_do_update(
            index_elements=['osm_type', 'osm_id'],
            index_where=(model.osm_id.is_not(None)),
            set_=update_dict
        )
    else:
        stmt = stmt.on_conflict_do_update(
            constraint=constraint,
            set_=update_dict
        )
    
    await session.execute(stmt)
