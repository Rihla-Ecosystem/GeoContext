"""add site_type and zone_type

Revision ID: 69835acf0ac2
Revises: 37dbcfd51815
Create Date: 2026-07-17 20:32:11.398250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '69835acf0ac2'
down_revision: Union[str, None] = '37dbcfd51815'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sites', sa.Column('site_type', sa.String(length=50), nullable=False, server_default='tourist'))
    op.create_index(op.f('ix_sites_site_type'), 'sites', ['site_type'], unique=False)

    op.add_column('restricted_zones', sa.Column('zone_type', sa.String(length=50), nullable=False, server_default='restricted'))
    op.create_index(op.f('ix_restricted_zones_zone_type'), 'restricted_zones', ['zone_type'], unique=False)

    # Existing protected areas should not be marked as "restricted"
    op.execute("UPDATE restricted_zones SET zone_type='protected' WHERE subtype='protected'")


def downgrade() -> None:
    op.drop_index(op.f('ix_restricted_zones_zone_type'), table_name='restricted_zones')
    op.drop_column('restricted_zones', 'zone_type')
    op.drop_index(op.f('ix_sites_site_type'), table_name='sites')
    op.drop_column('sites', 'site_type')
