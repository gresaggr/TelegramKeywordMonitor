"""add language and include_source_link

Revision ID: <generated_id>
Revises: <previous_revision>
Create Date: <generated_date>

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a138aa309db'
down_revision: Union[str, Sequence[str], None] = 'a138aa309db2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns with defaults first
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR DEFAULT 'en'")
    op.execute("UPDATE users SET language = 'en' WHERE language IS NULL")
    op.execute("ALTER TABLE users ALTER COLUMN language SET NOT NULL")

    op.execute("ALTER TABLE monitoring_tasks ADD COLUMN IF NOT EXISTS include_source_link BOOLEAN DEFAULT false")
    op.execute("UPDATE monitoring_tasks SET include_source_link = false WHERE include_source_link IS NULL")
    op.execute("ALTER TABLE monitoring_tasks ALTER COLUMN include_source_link SET NOT NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('monitoring_tasks', 'include_source_link')
    op.drop_column('users', 'language')