"""add prompt_block table

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-01-17 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Create prompt_block table
    op.create_table(
        'prompt_block',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_prompt_block_id', 'prompt_block', ['id'])
    op.create_index('ix_prompt_block_name', 'prompt_block', ['name'], unique=True)
    op.create_index('ix_prompt_block_order', 'prompt_block', ['order'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_prompt_block_order', table_name='prompt_block')
    op.drop_index('ix_prompt_block_name', table_name='prompt_block')
    op.drop_index('ix_prompt_block_id', table_name='prompt_block')
    
    # Drop table
    op.drop_table('prompt_block')
