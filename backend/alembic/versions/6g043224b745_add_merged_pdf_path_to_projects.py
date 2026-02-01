"""add merged_pdf_path to projects table

Revision ID: 6g043224b745
Revises: 5f932113a634
Create Date: 2026-02-01 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6g043224b745'
down_revision: Union[str, Sequence[str], None] = '5f932113a634'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add merged_pdf_path to projects table."""
    op.add_column('projects', sa.Column('merged_pdf_path', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema - remove merged_pdf_path from projects table."""
    op.drop_column('projects', 'merged_pdf_path')
