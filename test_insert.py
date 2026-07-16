import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert
from app.core.config import settings
from app.models.boundary import Boundary
from geoalchemy2.elements import WKTElement

async def test():
    engine = create_async_engine(settings.DATABASE_URL)
    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_maker() as session:
        # With string
        try:
            stmt = insert(Boundary).values([{
                "osm_type": "test_str",
                "osm_id": 2,
                "name": "test",
                "level": "test",
                "geometry": "SRID=4326;MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))"
            }])
            await session.execute(stmt)
            await session.commit()
            print("String inserted successfully!")
        except Exception as e:
            print("String insert failed:", type(e), e)

        # With WKTElement
        try:
            stmt = insert(Boundary).values([{
                "osm_type": "test_wkt",
                "osm_id": 3,
                "name": "test",
                "level": "test",
                "geometry": WKTElement("MULTIPOLYGON(((0 0, 1 0, 1 1, 0 1, 0 0)))", srid=4326)
            }])
            await session.execute(stmt)
            await session.commit()
            print("WKTElement inserted successfully!")
        except Exception as e:
            print("WKTElement insert failed:", type(e), e)

asyncio.run(test())
