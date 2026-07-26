"""drop_reports_table

Revision ID: 8f08c5a1be3f
Revises: 69835acf0ac2
Create Date: 2026-07-24 00:22:54.007714

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '8f08c5a1be3f'
down_revision: Union[str, None] = '69835acf0ac2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_reports_user_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_status'), table_name='reports')
    op.drop_table('reports')


def downgrade() -> None:
    op.create_table('reports',
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=True),
        sa.Column('related_site_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_foreign_key(None, 'reports', 'sites', ['related_site_id'], ['id'])
    op.create_index(op.f('ix_reports_status'), 'reports', ['status'], unique=False)
    op.create_index(op.f('ix_reports_user_id'), 'reports', ['user_id'], unique=False)
