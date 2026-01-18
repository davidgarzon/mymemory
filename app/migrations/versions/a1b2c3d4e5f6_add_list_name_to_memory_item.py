"""add list_name to memory_item

Revision ID: a1b2c3d4e5f6
Revises: 5522f41fe69c
Create Date: 2026-01-17 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '5522f41fe69c'
branch_labels = None
depends_on = None


def upgrade():
    # Add list_name column to memory_item table
    op.add_column(
        'memory_item',
        sa.Column('list_name', sa.String(), nullable=True)
    )
    
    # Create index on list_name
    op.create_index(
        'ix_memory_item_list_name',
        'memory_item',
        ['list_name']
    )


def downgrade():
    # Drop index on list_name
    op.drop_index('ix_memory_item_list_name', table_name='memory_item')
    
    # Drop column
    op.drop_column('memory_item', 'list_name')
