"""add preprocessing and classification fields to files table

Revision ID: 5f932113a634
Revises: 4a932113a633
Create Date: 2026-02-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f932113a634'
down_revision: Union[str, Sequence[str], None] = '4a932113a633'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add preprocessing and classification fields to files table."""
    # Remove old columns if they exist (from previous schema)
    try:
        op.drop_column('files', 'summary_json')
    except:
        pass  # Column may not exist
    
    # Add preprocessing fields
    op.add_column('files', sa.Column('extracted_content', sa.Text(), nullable=True))
    op.add_column('files', sa.Column('structured_content', sa.Text(), nullable=True))
    op.add_column('files', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('files', sa.Column('keywords', sa.Text(), nullable=True))
    op.add_column('files', sa.Column('document_type', sa.String(), nullable=True))
    op.add_column('files', sa.Column('key_entities', sa.Text(), nullable=True))
    op.add_column('files', sa.Column('llm_output_file', sa.String(), nullable=True))
    op.add_column('files', sa.Column('output_folder', sa.String(), nullable=True))
    
    # Add classification fields
    op.add_column('files', sa.Column('category_id', sa.Integer(), nullable=True))
    op.add_column('files', sa.Column('classification_confidence', sa.String(), nullable=True))
    op.add_column('files', sa.Column('classification_reasoning', sa.Text(), nullable=True))
    
    # Update category columns if they don't have proper comments
    # category_german and category_english should already exist


def downgrade() -> None:
    """Downgrade schema - remove preprocessing and classification fields."""
    # Remove preprocessing fields
    op.drop_column('files', 'extracted_content')
    op.drop_column('files', 'structured_content')
    op.drop_column('files', 'summary')
    op.drop_column('files', 'keywords')
    op.drop_column('files', 'document_type')
    op.drop_column('files', 'key_entities')
    op.drop_column('files', 'llm_output_file')
    op.drop_column('files', 'output_folder')
    
    # Remove classification fields
    op.drop_column('files', 'category_id')
    op.drop_column('files', 'classification_confidence')
    op.drop_column('files', 'classification_reasoning')
    
    # Restore old column
    op.add_column('files', sa.Column('summary_json', sa.Text(), nullable=True))
