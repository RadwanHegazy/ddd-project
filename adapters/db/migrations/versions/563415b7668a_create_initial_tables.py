"""create initial tables

Revision ID: 563415b7668a
Revises: 300404e866ca
Create Date: 2026-09-28 10:46:09.922054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '563415b7668a'
down_revision: Union[str, Sequence[str], None] = '300404e866ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
