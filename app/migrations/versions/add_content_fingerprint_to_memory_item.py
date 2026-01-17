"""add_content_fingerprint_to_memory_item

Revision ID: add_content_fingerprint
Revises: 1980beb72a93
Create Date: 2026-01-17 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_content_fingerprint'
down_revision: Union[str, None] = '1980beb72a93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add content_fingerprint column to memory_item table
    op.add_column('memory_item', sa.Column('content_fingerprint', sa.String(), nullable=True))
    # Create index for faster lookups
    op.create_index('ix_memory_item_content_fingerprint', 'memory_item', ['content_fingerprint'])


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_memory_item_content_fingerprint', table_name='memory_item')
    # Remove column
    op.drop_column('memory_item', 'content_fingerprint')
