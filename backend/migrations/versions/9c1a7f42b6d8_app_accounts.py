"""app accounts: users + user_sessions

Google is the only credential. ``users.google_sub`` is the stable Google
subject ID; ``username``, ``mlbb_id`` and ``password_hash`` are app-only
profile data (the MLBB ID is self-declared and never verified).

Revision ID: 9c1a7f42b6d8
Revises: 264514ec345c
Create Date: 2026-11-17 12:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c1a7f42b6d8'
down_revision: Union[str, Sequence[str], None] = '264514ec345c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('google_sub', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('email_verified', sa.Boolean(), nullable=False),
    sa.Column('google_name', sa.String(length=120), nullable=True),
    sa.Column('picture_url', sa.Text(), nullable=True),
    sa.Column('username', sa.String(length=24), nullable=True),
    sa.Column('mlbb_id', sa.String(length=32), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_google_sub'), 'users', ['google_sub'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table('user_sessions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_token_hash'), 'user_sessions', ['token_hash'], unique=True)
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_token_hash'), table_name='user_sessions')
    op.drop_table('user_sessions')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_google_sub'), table_name='users')
    op.drop_table('users')
