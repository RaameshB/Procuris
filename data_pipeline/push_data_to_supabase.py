import pandas as pd
from sqlalchemy import create_engine, inspect

from pathlib import Path
from dotenv import load_dotenv

import os

_ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=False)

# 1. Define your connection strings
# Source: Your local or existing Postgres DB
postgres_host = os.getenv("POSTGRES_HOST", "").strip()
postgres_port = os.getenv("POSTGRES_PORT", "").strip()
postgres_user = os.getenv("POSTGRES_USER", "").strip()
postgres_password = os.getenv("POSTGRES_PASSWORD", "").strip()
postgres_db = os.getenv("POSTGRES_DB", "").strip()
SOURCE_URI = f"postgresql+psycopg2://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

# Target: Your Supabase Postgres DB
# Replace with your actual Supabase connection string
supabase_ref = os.getenv("SUPABASE_PROJECT_REF", "").strip()
supabase_password = os.getenv("SUPABASE_PASSWORD", "").strip()

TARGET_URI = f"postgresql://postgres.{supabase_ref}:{supabase_password}@aws-1-us-east-1.pooler.supabase.com:6543/postgres"

def migrate_database():
    print("Establishing connections...")
    source_engine = create_engine(SOURCE_URI)

    # Supabase connections require SSL. SQLAlchemy handles this natively,
    # but passing sslmode=require ensures a secure connection attempt.
    target_engine = create_engine(TARGET_URI, connect_args={'sslmode': 'require'})

    # 2. Inspect the source database to get all table names
    inspector = inspect(source_engine)
    tables = inspector.get_table_names(schema="public")

    print(f"Found {len(tables)} tables to migrate: {tables}")

    # 3. Iterate through tables and transfer data
    for table in tables:
        print(f"Migrating table: {table}...")
        try:
            # Read from source in chunks of 10,000 rows to manage memory safely
            for chunk in pd.read_sql_table(table, source_engine, chunksize=10000):

                # Push the chunk to Supabase
                chunk.to_sql(
                    name=table,
                    con=target_engine,
                    schema="public",
                    if_exists="append", # Appends data if the table exists, creates it if it doesn't
                    index=False,
                    method="multi"      # Optimizes the transfer by sending bulk INSERT statements
                )
            print(f"✓ Completed {table}")
        except Exception as e:
            print(f"✗ Error migrating {table}: {e}")

if __name__ == "__main__":
    migrate_database()
