# =============================================================================
# db_utils.py
# Supply Chain Data Pipeline — Database Utilities
#
# Provides:
#   - SQLAlchemy engine creation from .env credentials
#   - DataFrame → PostgreSQL write helper  (write_dataframe)
#   - PostgreSQL table → DataFrame read helper (read_table)
#   - Lightweight connection health check    (test_connection)
#   - Table existence check                  (table_exists)
#
# All other pipeline modules import from this file — it is the single
# source of truth for database connectivity.
# =============================================================================

import logging
import os
from pathlib import Path
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# ---------------------------------------------------------------------------
# Environment — load .env from the data_pipeline/ directory so the module
# works correctly regardless of the working directory the caller uses.
# ---------------------------------------------------------------------------
_ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=False)  # won't stomp already-set vars

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Connection helpers
# =============================================================================


def get_connection_string() -> str:
    """
    Build a PostgreSQL DSN from environment variables.

    Expected variables (with fallback defaults that match docker-compose.yml):
        POSTGRES_HOST     → localhost
        POSTGRES_PORT     → 5432
        POSTGRES_USER     → scuser
        POSTGRES_PASSWORD → scpassword
        POSTGRES_DB       → supply_chain

    Returns:
        A psycopg2-compatible SQLAlchemy connection string.
    """
    host     = os.getenv("POSTGRES_HOST",     "localhost")
    port     = os.getenv("POSTGRES_PORT",     "5432")
    user     = os.getenv("POSTGRES_USER",     "scuser")
    password = os.getenv("POSTGRES_PASSWORD", "scpassword")
    db       = os.getenv("POSTGRES_DB",       "supply_chain")

    dsn = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return dsn


def get_engine(echo: bool = False) -> Engine:
    """
    Create and return a SQLAlchemy Engine connected to the pipeline's
    PostgreSQL database.

    The engine uses a connection pool with pre-ping enabled, meaning each
    connection is validated before it is handed to application code — this
    prevents stale connections from causing silent failures.

    Args:
        echo: When True, SQLAlchemy logs every SQL statement it executes.
              Useful for debugging; leave False in production runs.

    Returns:
        A configured SQLAlchemy Engine instance.

    Raises:
        SQLAlchemyError: If the engine cannot be created (e.g. bad DSN).
    """
    dsn = get_connection_string()

    # Mask the password in the log line for safety
    safe_dsn = dsn.replace(os.getenv("POSTGRES_PASSWORD", "scpassword"), "***")
    logger.info("Creating SQLAlchemy engine: %s", safe_dsn)

    engine = create_engine(
        dsn,
        echo=echo,
        # ── Pool settings ────────────────────────────────────────────────
        pool_pre_ping=True,        # validate connections before use
        pool_size=5,               # keep up to 5 idle connections
        max_overflow=10,           # allow up to 10 additional on demand
        pool_recycle=1800,         # recycle connections after 30 min
        connect_args={
            "connect_timeout": 10, # fail fast if Postgres is unreachable
            "application_name": "supply_chain_pipeline",
        },
    )
    return engine


def test_connection(engine: Engine) -> bool:
    """
    Execute a trivial query to verify the engine can reach the database.

    Args:
        engine: An existing SQLAlchemy Engine.

    Returns:
        True if the connection succeeds, False otherwise.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.close()
        logger.info("Database connection test: OK")
        return True
    except OperationalError as exc:
        logger.error(
            "Database connection test FAILED — is Postgres running "
            "and are the .env credentials correct?\n  Details: %s", exc
        )
        return False
    except SQLAlchemyError as exc:
        logger.error("Unexpected SQLAlchemy error during connection test: %s", exc)
        return False


# =============================================================================
# DataFrame I/O helpers
# =============================================================================

# Type alias for pandas to_sql's if_exists parameter
_IfExists = Literal["fail", "replace", "append"]


def write_dataframe(
    df: pd.DataFrame,
    table_name: str,
    engine: Engine,
    if_exists: _IfExists = "replace",
    index: bool = False,
    chunksize: int = 1_000,
    schema: str | None = None,
) -> int:
    """
    Write a pandas DataFrame to a PostgreSQL table.

    Uses the ``multi`` insert method for significantly better throughput vs.
    single-row inserts when writing large DataFrames.

    Args:
        df:         The DataFrame to persist.
        table_name: Target table name in Postgres.
        engine:     SQLAlchemy engine returned by :func:`get_engine`.
        if_exists:  What to do when the table already exists:
                      "replace" — drop & recreate (default, safe for raw ingestion)
                      "append"  — insert rows below existing data
                      "fail"    — raise an error
        index:      Whether to write the DataFrame's index as a column.
        chunksize:  Number of rows per INSERT batch. Tune this if you see
                    memory pressure on very large DataFrames.
        schema:     Postgres schema name (defaults to the engine's search_path,
                    usually "public").

    Returns:
        Number of rows written (0 if the DataFrame was empty).

    Raises:
        SQLAlchemyError: On any database-level error.
        ValueError: If ``if_exists`` is not a valid option.
    """
    if df is None or df.empty:
        logger.warning(
            "write_dataframe called with an empty DataFrame for table '%s'. "
            "Nothing written.", table_name
        )
        return 0

    n_rows, n_cols = df.shape
    logger.info(
        "Writing %d rows × %d cols to table '%s' (if_exists='%s') …",
        n_rows, n_cols, table_name, if_exists,
    )

    try:
        df.to_sql(
            name=table_name,
            con=engine,
            schema=schema,
            if_exists=if_exists,
            index=index,
            chunksize=chunksize,
            method="multi",   # batch inserts — much faster than row-by-row
        )
        logger.info("Successfully wrote %d rows to '%s'.", n_rows, table_name)
        return n_rows

    except SQLAlchemyError as exc:
        logger.error(
            "Failed to write DataFrame to table '%s': %s", table_name, exc
        )
        raise


def read_table(
    table_name: str,
    engine: Engine,
    schema: str | None = None,
    chunksize: int | None = None,
) -> pd.DataFrame:
    """
    Read an entire PostgreSQL table into a pandas DataFrame.

    Args:
        table_name: Name of the table to read.
        engine:     SQLAlchemy engine returned by :func:`get_engine`.
        schema:     Postgres schema (defaults to the engine's search_path).
        chunksize:  If set, returns a TextFileReader iterator of chunks
                    instead of a single DataFrame. Useful for tables that
                    don't fit comfortably in memory.

    Returns:
        A pandas DataFrame containing all rows of the table.

    Raises:
        ValueError:     If the table does not exist.
        SQLAlchemyError: On any database-level error.
    """
    if not table_exists(table_name, engine, schema=schema):
        raise ValueError(
            f"Table '{table_name}' does not exist in the database. "
            "Run the appropriate ingestion script first."
        )

    logger.info("Reading table '%s' …", table_name)
    try:
        df = pd.read_sql_table(
            table_name=table_name,
            con=engine,
            schema=schema,
            chunksize=chunksize,
        )
        # chunksize returns an iterator; only log shape for eager loads
        if isinstance(df, pd.DataFrame):
            logger.info(
                "Read %d rows × %d cols from '%s'.", *df.shape, table_name
            )
        return df

    except SQLAlchemyError as exc:
        logger.error("Failed to read table '%s': %s", table_name, exc)
        raise


def read_query(
    sql: str,
    engine: Engine,
    params: dict | None = None,
) -> pd.DataFrame:
    """
    Execute an arbitrary SELECT query and return the results as a DataFrame.

    Prefer :func:`read_table` for full-table reads; use this for filtered or
    joined reads.

    Args:
        sql:    A SQL SELECT statement (use :param syntax for parameters).
        engine: SQLAlchemy engine returned by :func:`get_engine`.
        params: Optional dict of bind parameters, e.g. {"ticker": "AAPL"}.

    Returns:
        A pandas DataFrame of query results.

    Example::

        df = read_query(
            "SELECT * FROM raw_polygon WHERE ticker = :ticker",
            engine,
            params={"ticker": "AAPL"},
        )
    """
    logger.info("Executing custom query …")
    try:
        df = pd.read_sql(text(sql), con=engine, params=params)
        logger.info("Query returned %d rows.", len(df))
        return df
    except SQLAlchemyError as exc:
        logger.error("Query failed: %s\n  SQL: %s", exc, sql)
        raise


# =============================================================================
# Introspection helpers
# =============================================================================


def table_exists(
    table_name: str,
    engine: Engine,
    schema: str | None = None,
) -> bool:
    """
    Check whether a table exists in the connected database.

    Args:
        table_name: Table name to check.
        engine:     SQLAlchemy engine.
        schema:     Postgres schema (defaults to the engine's search_path).

    Returns:
        True if the table exists, False otherwise.
    """
    insp = inspect(engine)
    return insp.has_table(table_name, schema=schema)


def list_tables(engine: Engine, schema: str | None = None) -> list[str]:
    """
    Return a sorted list of all table names visible to the engine.

    Args:
        engine: SQLAlchemy engine.
        schema: Postgres schema (defaults to the engine's search_path).

    Returns:
        Alphabetically sorted list of table names.
    """
    insp = inspect(engine)
    tables = sorted(insp.get_table_names(schema=schema))
    logger.info("Tables in database: %s", tables)
    return tables


def get_row_count(table_name: str, engine: Engine) -> int:
    """
    Return the number of rows in a table without loading it into memory.

    Args:
        table_name: Target table name.
        engine:     SQLAlchemy engine.

    Returns:
        Row count as an integer, or -1 if the table does not exist.
    """
    if not table_exists(table_name, engine):
        logger.warning("get_row_count: table '%s' does not exist.", table_name)
        return -1
    with engine.connect() as conn:
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        count: int = result.scalar()
    logger.info("Table '%s' has %d rows.", table_name, count)
    return count
