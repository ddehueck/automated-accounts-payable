"""Added categories and invoice content hash

Revision ID: d1e622aadfb6
Revises: fd849f2a56de
Create Date: 2022-03-26 23:23:19.049778

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d1e622aadfb6"
down_revision = "fd849f2a56de"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "categories",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("organization_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("created_on", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_on", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_categories_organization_id"), "categories", ["organization_id"], unique=False)
    op.create_index(op.f("ix_categories_user_id"), "categories", ["user_id"], unique=False)
    op.create_table(
        "category_invoice_associations",
        sa.Column("category_id", sa.String(), nullable=False),
        sa.Column("invoice_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
        ),
        sa.PrimaryKeyConstraint("category_id", "invoice_id"),
    )
    op.add_column("invoices", sa.Column("content_hash", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("invoices", "content_hash")
    op.drop_table("category_invoice_associations")
    op.drop_index(op.f("ix_categories_user_id"), table_name="categories")
    op.drop_index(op.f("ix_categories_organization_id"), table_name="categories")
    op.drop_table("categories")
    # ### end Alembic commands ###
