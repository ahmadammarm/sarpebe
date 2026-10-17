"""add backend-owned authentication (credentials, refresh and email tokens)

Imports existing Supabase Auth accounts (email, bcrypt hash, confirmation time) into
profiles so users keep their passwords and their user ids.

Revision ID: b7e2f4a91c35
Revises: a3c1d9e47b20
Create Date: 2026-10-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e2f4a91c35'
down_revision: Union[str, Sequence[str], None] = 'a3c1d9e47b20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('profiles', sa.Column('email', sa.String(), nullable=True))
    op.add_column('profiles', sa.Column('password_hash', sa.String(), nullable=True))
    op.add_column('profiles', sa.Column('email_verified_at', sa.TIMESTAMP(timezone=True), nullable=True))

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('family_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('rotated', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_family_id'), 'refresh_tokens', ['family_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)

    op.create_table(
        'auth_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('purpose', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_auth_tokens_user_id'), 'auth_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_auth_tokens_token_hash'), 'auth_tokens', ['token_hash'], unique=True)

    # Import Supabase Auth accounts when the auth schema exists (it does on Supabase,
    # and is skipped on a plain PostgreSQL database).
    #  1. Profiles that already exist get their credentials copied from auth.users.
    #  2. Accounts that never produced a profile (registered but never logged in) get one.
    # Supabase stores bcrypt hashes in encrypted_password; an empty value means the account
    # has no password (e.g. OAuth only), so it is left NULL.
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('auth.users') IS NOT NULL THEN
                UPDATE profiles p
                SET email = lower(u.email),
                    password_hash = NULLIF(u.encrypted_password, ''),
                    email_verified_at = u.email_confirmed_at
                FROM auth.users u
                WHERE u.id = p.id AND u.email IS NOT NULL;

                INSERT INTO profiles
                    (id, email, password_hash, email_verified_at, full_name,
                     subscription_tier, role, created_at)
                SELECT u.id,
                       lower(u.email),
                       NULLIF(u.encrypted_password, ''),
                       u.email_confirmed_at,
                       COALESCE(NULLIF(u.raw_user_meta_data->>'full_name', ''),
                                split_part(u.email, '@', 1)),
                       'free',
                       'user',
                       COALESCE(u.created_at, now())
                FROM auth.users u
                WHERE u.email IS NOT NULL
                  AND NOT EXISTS (SELECT 1 FROM profiles p WHERE p.id = u.id);
            END IF;
        END $$;
        """
    )

    # Created after the import so a duplicate would fail loudly instead of half-importing.
    op.create_index(op.f('ix_profiles_email'), 'profiles', ['email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_profiles_email'), table_name='profiles')
    op.drop_index(op.f('ix_auth_tokens_token_hash'), table_name='auth_tokens')
    op.drop_index(op.f('ix_auth_tokens_user_id'), table_name='auth_tokens')
    op.drop_table('auth_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_family_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_column('profiles', 'email_verified_at')
    op.drop_column('profiles', 'password_hash')
    op.drop_column('profiles', 'email')
