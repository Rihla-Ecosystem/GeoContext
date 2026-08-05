"""Enhance sites table for dashboard integration, add location_warnings and nearby_services tables.

Revision ID: c4b6e9d8a1f3
Revises: 8f08c5a1be3f
Create Date: 2026-08-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = 'c4b6e9d8a1f3'
down_revision: Union[str, None] = '8f08c5a1be3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # Extend sites table with dashboard-required columns
    # ---------------------------------------------------------------
    op.add_column('sites', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('sites', sa.Column('category', sa.String(length=100), nullable=True, server_default='other', index=True))
    op.add_column('sites', sa.Column('governorate', sa.String(length=100), nullable=True, index=True))
    op.add_column('sites', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('sites', sa.Column('country', sa.String(length=100), nullable=True, server_default='Egypt'))
    op.add_column('sites', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('sites', sa.Column('safety_score', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('sites', sa.Column('risk_level', sa.String(length=50), nullable=True, server_default='low', index=True))
    op.add_column('sites', sa.Column('status', sa.String(length=50), nullable=True, server_default='draft', index=True))
    op.add_column('sites', sa.Column('visibility', sa.String(length=50), nullable=True, server_default='public'))
    op.add_column('sites', sa.Column('ai_summary', sa.Text(), nullable=True))
    op.add_column('sites', sa.Column('published_at', sa.DateTime(), nullable=True))
    op.add_column('sites', sa.Column('updated_by', sa.String(length=255), nullable=True))
    op.add_column('sites', sa.Column('created_by', sa.String(length=255), nullable=True))
    op.add_column('sites', sa.Column('version', sa.Integer(), nullable=True, server_default='1'))

    # Set defaults for existing rows
    op.execute("UPDATE sites SET category = 'other' WHERE category IS NULL")
    op.execute("UPDATE sites SET country = 'Egypt' WHERE country IS NULL")
    op.execute("UPDATE sites SET safety_score = 0.0 WHERE safety_score IS NULL")
    op.execute("UPDATE sites SET risk_level = 'low' WHERE risk_level IS NULL")
    op.execute("UPDATE sites SET status = 'draft' WHERE status IS NULL")
    op.execute("UPDATE sites SET visibility = 'public' WHERE visibility IS NULL")
    op.execute("UPDATE sites SET version = 1 WHERE version IS NULL")

    # ---------------------------------------------------------------
    # Create location_warnings table
    # ---------------------------------------------------------------
    op.create_table('location_warnings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('location_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_location_warnings_location_id'), 'location_warnings', ['location_id'], unique=False)
    op.create_index(op.f('ix_location_warnings_severity'), 'location_warnings', ['severity'], unique=False)
    op.create_foreign_key(
        'fk_warning_location',
        'location_warnings', 'sites',
        ['location_id'], ['id'],
        ondelete='CASCADE',
    )

    # ---------------------------------------------------------------
    # Create nearby_services table
    # ---------------------------------------------------------------
    op.create_table('nearby_services',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('location_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('contact', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_nearby_services_location_id'), 'nearby_services', ['location_id'], unique=False)
    op.create_foreign_key(
        'fk_service_location',
        'nearby_services', 'sites',
        ['location_id'], ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_service_location', 'nearby_services', type_='foreignkey')
    op.drop_index(op.f('ix_nearby_services_location_id'), table_name='nearby_services')
    op.drop_table('nearby_services')

    op.drop_constraint('fk_warning_location', 'location_warnings', type_='foreignkey')
    op.drop_index(op.f('ix_location_warnings_severity'), table_name='location_warnings')
    op.drop_index(op.f('ix_location_warnings_location_id'), table_name='location_warnings')
    op.drop_table('location_warnings')

    op.drop_column('sites', 'version')
    op.drop_column('sites', 'created_by')
    op.drop_column('sites', 'updated_by')
    op.drop_column('sites', 'published_at')
    op.drop_column('sites', 'ai_summary')
    op.drop_column('sites', 'visibility')
    op.drop_column('sites', 'status')
    op.drop_column('sites', 'risk_level')
    op.drop_column('sites', 'safety_score')
    op.drop_column('sites', 'address')
    op.drop_column('sites', 'country')
    op.drop_column('sites', 'city')
    op.drop_column('sites', 'governorate')
    op.drop_column('sites', 'category')
    op.drop_column('sites', 'description')
