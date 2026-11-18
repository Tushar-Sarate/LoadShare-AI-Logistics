import subprocess
import sys

from sqlalchemy import text

from app.database import engine

# Development only: deletes ALL data
with engine.begin() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))

print("Schema dropped")

subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)

print("Database reset done (migrations applied)")