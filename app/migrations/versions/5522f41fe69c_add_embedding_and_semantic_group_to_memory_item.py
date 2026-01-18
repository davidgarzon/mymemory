"""add embedding and semantic_group to memory_item

Revision ID: 5522f41fe69c
Revises: 01064e6fc6d6
Create Date: 2026-01-17 20:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '5522f41fe69c'
down_revision = '01064e6fc6d6'
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Add embedding column (Vector(1536) for text-embedding-3-small)
    op.add_column('memory_item', sa.Column('embedding', Vector(1536), nullable=True))
    
    # Add semantic_group_id column
    op.add_column('memory_item', sa.Column('semantic_group_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create index on semantic_group_id
    op.create_index('ix_memory_item_semantic_group_id', 'memory_item', ['semantic_group_id'])
    
    # Create index on embedding for similarity search (using cosine distance)
    # This will use pgvector's ivfflat index for faster similarity searches
    op.execute("CREATE INDEX ix_memory_item_embedding_cosine ON memory_item USING ivfflat (embedding vector_cosine_ops)")


def downgrade():
    # Drop index on embedding
    op.drop_index('ix_memory_item_embedding_cosine', table_name='memory_item')
    
    # Drop index on semantic_group_id
    op.drop_index('ix_memory_item_semantic_group_id', table_name='memory_item')
    
    # Drop columns
    op.drop_column('memory_item', 'semantic_group_id')
    op.drop_column('memory_item', 'embedding')
