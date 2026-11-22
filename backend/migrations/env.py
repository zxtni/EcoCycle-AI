from alembic import context

from backend.db import engine

with engine.begin() as conn:
    context.configure(connection=conn)
    with context.begin_transaction():
        context.run_migrations()
