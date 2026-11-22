"""Initial platform tables."""

import sqlalchemy as s
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pk = lambda: s.Column("id", s.Integer, primary_key=True)
    op.create_table(
        "users",
        pk(),
        s.Column("email", s.String(254), nullable=False, unique=True),
        s.Column("name", s.String(80), nullable=False),
        s.Column("password", s.Text),
        s.Column("role", s.String(16), nullable=False),
        s.Column("synthetic", s.Boolean, nullable=False),
    )
    op.create_table(
        "sessions",
        s.Column("token", s.String(64), primary_key=True),
        s.Column("user_id", s.Integer, s.ForeignKey("users.id"), nullable=False, index=True),
        s.Column("expires", s.DateTime, nullable=False),
    )
    op.create_table(
        "scans",
        pk(),
        s.Column("user_id", s.Integer, s.ForeignKey("users.id"), nullable=False, index=True),
        s.Column("created", s.DateTime, nullable=False, index=True),
        s.Column("predictions", s.Text, nullable=False),
        s.Column("image", s.Text, nullable=False),
        s.Column("material", s.String(16)),
        s.Column("weight", s.Float),
        s.Column("breakdown", s.Text),
        s.Column("ward", s.String(80), nullable=False),
    )
    op.create_table(
        "feedback",
        pk(),
        s.Column("scan_id", s.Integer, s.ForeignKey("scans.id"), nullable=False, unique=True),
        s.Column("material", s.String(16), nullable=False),
        s.Column("note", s.String(400), nullable=False),
        s.Column("status", s.String(16), nullable=False),
    )
    op.create_table(
        "centers",
        pk(),
        s.Column("name", s.String(120), nullable=False),
        s.Column("lat", s.Float, nullable=False),
        s.Column("lon", s.Float, nullable=False),
        s.Column("materials", s.String(100), nullable=False),
        s.Column("source", s.String(200), nullable=False),
    )
    op.create_table(
        "audit",
        pk(),
        s.Column("actor", s.Integer, s.ForeignKey("users.id"), nullable=False),
        s.Column("action", s.String(240), nullable=False),
        s.Column("created", s.DateTime, nullable=False),
    )


def downgrade():
    for table in ("audit", "feedback", "centers", "scans", "sessions", "users"):
        op.drop_table(table)
