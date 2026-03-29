import polars as pl
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import date

# Load environment variables
_ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=False)

supabase_ref = os.getenv("SUPABASE_PROJECT_REF", "").strip()
supabase_password = os.getenv("SUPABASE_PASSWORD", "").strip()
DATABASE_URL = f"postgresql://postgres.{supabase_ref}:{supabase_password}@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

def process_macro_data_v3(db_url: str):
    print("1. Fetching data from PostgreSQL into Polars...")
    df = pl.read_database_uri("SELECT * FROM unified_values_view", db_url, engine="adbc")

    # --- LIFESPAN FILTERING ---
    # Define your required dataset horizon.
    # Any column that doesn't fully cover this window gets dropped.
    TARGET_START_DATE = date(2016, 1, 1) # Matrix must go back to at least here
    TARGET_END_DATE = date(2024, 1, 1)   # Series must have data up to at least here
    MINIMUM_DATA_POINTS = 8                 # Drop broken series with almost no records

    cols_to_drop = []

    print("2. Analyzing column lifespans...")
    for col in df.columns:
        if col == 'date':
            continue

        # Get a series with the nulls removed to check dates and counts
        valid_data = df.select(['date', col]).drop_nulls()

        # Rule 1: Not enough total data
        if valid_data.height < MINIMUM_DATA_POINTS:
            cols_to_drop.append(col)
            continue

        first_date = valid_data['date'].min()
        last_date = valid_data['date'].max()

        # Rule 2: Late Starter (Would shrink our historical window)
        if first_date > TARGET_START_DATE:
            cols_to_drop.append(col)
            continue

        # Rule 3: Early Ender (Creates stale forward-filled data)
        if last_date < TARGET_END_DATE:
            cols_to_drop.append(col)
            continue

    print(f"Dropping {len(cols_to_drop)} incompatible columns out of {len(df.columns) - 1}.")
    df = df.drop(cols_to_drop)

    print("3. Upsampling and Forward Filling...")
    df_dense = (
        df.sort("date")
        .upsample(time_column="date", every="1d")
        .with_columns(pl.col("*").exclude("date").forward_fill())
        # Slice the dataset to our target start date before dropping the remaining leading nulls
        .filter(pl.col("date") >= TARGET_START_DATE)
        .drop_nulls()
    )

    print(f"Final dense matrix shape: {df_dense.shape}")

    if df_dense.height == 0:
        print("WARNING: Matrix is still 0 rows. You need to push your TARGET_START_DATE further forward.")
        return

    print("4. Writing dense table back to PostgreSQL...")
    df_dense.write_database(
        table_name="model_ready_dense_data",
        connection=db_url,
        if_table_exists="replace"
    )
    print("Pipeline complete.")

process_macro_data_v3(DATABASE_URL)
