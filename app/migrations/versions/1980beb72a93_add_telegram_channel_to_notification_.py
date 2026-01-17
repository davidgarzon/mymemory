"""add_telegram_channel_to_notification_channel_enum

Revision ID: 1980beb72a93
Revises: b53427ee70e0
Create Date: 2026-01-17 12:58:55.682809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1980beb72a93'
down_revision: Union[str, None] = 'b53427ee70e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
