"""Non binary gender

Revision ID: 494b49f127b9
Revises: 1a2dbf09fd47
Create Date: 2022-06-22 06:29:22.682930

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.

revision = '494b49f127b9'
down_revision = '1a2dbf09fd47'
branch_labels = None
depends_on = None

old_options = ('male', 'female')
new_options = ('male','female', 'nonbinary')

old_type = sa.Enum(*old_options, name='gender')
new_type = sa.Enum(*new_options, name='gender')
tmp_type = sa.Enum(*new_options, name='_gender')

tcr = sa.sql.table('user',
                   sa.Column('gender', new_type, nullable=True))


def upgrade():
    # Create a tempoary "_gender" type, convert and drop the "old" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE public."user" ALTER COLUMN gender TYPE _gender'
               ' USING gender::text::_gender')
    old_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "new" gender type
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE public."user" ALTER COLUMN gender TYPE gender'
               ' USING gender::text::gender')
    tmp_type.drop(op.get_bind(), checkfirst=False)


def downgrade():
    # Convert 'nonbinary' gender into None
    op.execute(tcr.update().where(tcr.c.gender=='nonbinary')
               .values(gender=None))
    # Create a tempoary "_gender" type, convert and drop the "new" type
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE public."user" ALTER COLUMN gender TYPE _gender'
               ' USING gender::text::_gender')
    new_type.drop(op.get_bind(), checkfirst=False)
    # Create and convert to the "old" gender type
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE public."user" ALTER COLUMN gender TYPE gender'
               ' USING gender::text::gender')
    tmp_type.drop(op.get_bind(), checkfirst=False)
