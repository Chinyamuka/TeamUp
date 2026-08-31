"""Add RBAC roles

Revision ID: add_rbac_roles
Revises: 
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_rbac_roles'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add role column to project_memberships if not exists
    op.add_column('project_memberships', 
        sa.Column('role', sa.String(20), server_default='member', nullable=False)
    )
    
    # Add index for faster role lookups
    op.create_index('ix_project_memberships_role', 'project_memberships', ['role'])


def downgrade():
    op.drop_index('ix_project_memberships_role', table_name='project_memberships')
    op.drop_column('project_memberships', 'role')
