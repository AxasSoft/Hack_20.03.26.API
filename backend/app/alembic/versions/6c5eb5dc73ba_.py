"""empty message

Revision ID: 6c5eb5dc73ba
Revises: 47848e2ae192
Create Date: 2023-09-18 12:31:57.545189

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c5eb5dc73ba'
down_revision = '47848e2ae192'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""CREATE EXTENSION IF NOT EXISTS "postgis";""")


def downgrade():
    pass
