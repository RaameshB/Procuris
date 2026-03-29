# =============================================================================
# clean_data.py
# Supply Chain Data Pipeline — Data Cleaning & Processing
#
# Reads raw_* tables from PostgreSQL, applies time-series alignment and
# aggressive zero-null imputation, and writes to processed_* tables.
#
# Cleaning stages:
#   1. Special column preparation (e.g., Comtrade date parsing).
#   2. Pruning: Drop any column with >15% nulls (except time/group keys).
#   3. Alignment (Time-Series only): Reindex each group to a regular frequency
#      using per-group min/max dates to avoid leading/trailing NaNs.
#   4. Imputation: Fill missing values (median for numeric, mode/forward-fill
#      for categorical) to guarantee zero nulls remain.
#
# Run:
#   uv run python data_pipeline/clean_data.py
# =============================================================================

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.engine import Engine

from db_utils import (
    get_engine,
    list_tables,
    read_table,
    test_connection,
    write_dataframe,
)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
_ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=False)

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
# ── Configuration ─────────────────────────────────────────────────────────────
# =============================================================================

NULL_DROP_THRESHOLD: float = 0.15   # 15 %

RAW_TO_PROCESSED: dict[str, str] = {
    "raw_polygon":   "processed_polygon",
    "raw_census":    "processed_census",
    "raw_opensky":   "processed_opensky",
    "raw_comtrade":  "processed_comtrade",
    "raw_worldbank": "processed_worldbank",
    "raw_fred":      "processed_fred",
}

@dataclass
class TSConfig:
    time_col: str
    group_cols: list[str]
    freq: str

# Configs for time-series alignment. Tables not listed here are treated
# as cross-sectional or snapshot data (e.g. OpenSky, OSHub).
TS_CONFIGS: dict[str, TSConfig] = {
    "raw_polygon": TSConfig(
        time_col="end_date",
        group_cols=["ticker"],
        freq="QE",
    ),
    "raw_census": TSConfig(
        time_col="time_slot_date",
        group_cols=["category_code", "data_type_code", "seasonally_adj"],
        freq="ME",
    ),
    "raw_comtrade": TSConfig(
        time_col="period_date",
        group_cols=["reporter_code", "partner_code", "commodity_code", "flow_code"],
        freq="ME",
    ),
    "raw_worldbank": TSConfig(
        time_col="date",
        group_cols=["indicator_code", "country_code"],
        freq="YE",
    ),
    "raw_fred": TSConfig(
        time_col="date",
        group_cols=["series_id"],
        freq="ME",
    ),
}

# =============================================================================
# ── Data structures ───────────────────────────────────────────────────────────
# =============================================================================

class ColumnReport(NamedTuple):
    name: str
    dtype: str
    null_count: int
    total_rows: int
    null_fraction: float
    will_drop: bool

class TableCleaningReport(NamedTuple):
    table_name: str
    rows_before: int
    rows_after: int
    cols_before: int
    cols_after: int
    cols_dropped: list[str]

# =============================================================================
# ── Pipeline Stages ───────────────────────────────────────────────────────────
# =============================================================================

def _prep_comtrade_time(df: pd.DataFrame) -> pd.DataFrame:
    """Special handling for UN Comtrade 'period' column."""
    if "period" not in df.columns:
        return df

    # Comtrade period is usually an int/str like 202101 or 2021
    periods = df["period"].astype(str)

    def parse_period(p: str) -> pd.Timestamp:
        if len(p) == 4:
            return pd.to_datetime(f"{p}-01-01")
        elif len(p) == 6:
            return pd.to_datetime(f"{p[:4]}-{p[4:6]}-01")
        return pd.NaT

    df["period_date"] = periods.apply(parse_period)
    return df

def audit_and_drop_columns(
    df: pd.DataFrame,
    table_name: str,
    protected_cols: set[str]
) -> tuple[pd.DataFrame, list[ColumnReport]]:
    """Drop columns with > 15% nulls, unless they are protected (time/group keys)."""
    n_rows = len(df)
    reports = []
    cols_to_drop = []

    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_fraction = null_count / n_rows if n_rows > 0 else 0.0

        will_drop = null_fraction > NULL_DROP_THRESHOLD and col not in protected_cols

        reports.append(ColumnReport(
            name=col, dtype=str(df[col].dtype),
            null_count=null_count, total_rows=n_rows,
            null_fraction=null_fraction, will_drop=will_drop
        ))
        if will_drop:
            cols_to_drop.append(col)

    if cols_to_drop:
        logger.info("[%s] Dropping %d columns exceeding null threshold: %s",
                    table_name, len(cols_to_drop), cols_to_drop)
        df = df.drop(columns=cols_to_drop)

    return df, reports

def align_time_series(df: pd.DataFrame, config: TSConfig, table_name: str) -> pd.DataFrame:
    """
    Reindex each group to a regular frequency using per-group min/max dates
    to avoid leading or trailing NaNs.
    """
    time_col = config.time_col
    freq = config.freq
    group_cols = config.group_cols

    # Ensure time column is datetime
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])

    if df.empty:
        return df

    # Groupby and resample
    aligned_dfs = []

    # Sort to ensure proper alignment
    df = df.sort_values(by=time_col)

    grouped = df.groupby(group_cols, dropna=True)

    for name, group in grouped:
        if group.empty:
            continue

        group = group.set_index(time_col)
        # Handle duplicates by taking the last entry for that period
        group = group[~group.index.duplicated(keep="last")]

        # Create a date range from the group's min to max date
        min_date = group.index.min()
        max_date = group.index.max()

        # Resample to common frequency
        full_idx = pd.date_range(start=min_date, end=max_date, freq=freq)
        group = group.reindex(full_idx)

        # Restore group columns
        if isinstance(name, tuple):
            for col, val in zip(group_cols, name):
                group[col] = val
        else:
            group[group_cols[0]] = name

        group = group.rename_axis(time_col).reset_index()
        aligned_dfs.append(group)

    if not aligned_dfs:
        return df

    res_df = pd.concat(aligned_dfs, ignore_index=True)
    return res_df

def impute_zero_nulls(df: pd.DataFrame, config: TSConfig | None) -> pd.DataFrame:
    """
    Interpolate and impute to guarantee 0 nulls remain.
    - Numeric: linear interpolate (for TS), then bfill/ffill, then median fallback.
    - Categorical/String: ffill/bfill, then mode fallback, then "Missing".
    """
    if df.empty:
        return df

    group_cols = config.group_cols if config else []

    for col in df.columns:
        if col in group_cols or (config and col == config.time_col):
            continue

        if df[col].isnull().any():
            is_numeric = pd.api.types.is_numeric_dtype(df[col])

            if config and group_cols:
                # Time-series aware imputation per group
                if is_numeric:
                    df[col] = df.groupby(group_cols)[col].transform(
                        lambda x: x.interpolate(method='linear', limit_direction='both')
                    )
                else:
                    df[col] = df.groupby(group_cols)[col].transform(
                        lambda x: x.ffill().bfill()
                    )

            # Global fallback if groups couldn't fill everything
            if df[col].isnull().any():
                if is_numeric:
                    median_val = df[col].median()
                    fill_val = median_val if not pd.isna(median_val) else 0
                    df[col] = df[col].fillna(fill_val)
                else:
                    mode_s = df[col].mode()
                    fill_val = mode_s.iloc[0] if not mode_s.empty else "Missing"
                    df[col] = df[col].fillna(fill_val)

    return df

def process_table(raw_table: str, processed_table: str, engine: Engine) -> TableCleaningReport | None:
    logger.info("--- Processing %s -> %s ---", raw_table, processed_table)

    try:
        df = read_table(raw_table, engine)
    except Exception as exc:
        logger.error("[%s] Read failed: %s", raw_table, exc)
        return None

    if df.empty:
        logger.warning("[%s] Table is empty. Skipping.", raw_table)
        return None

    rows_before = len(df)
    cols_before = len(df.columns)

    if raw_table == "raw_comtrade":
        df = _prep_comtrade_time(df)

    ts_config = TS_CONFIGS.get(raw_table)
    protected_cols = set(ts_config.group_cols + [ts_config.time_col]) if ts_config else set()
    if raw_table == "raw_comtrade":
        protected_cols.add("period") # protect original column

    # 1. Audit and drop high-null columns
    df, reports = audit_and_drop_columns(df, raw_table, protected_cols)
    cols_dropped = [r.name for r in reports if r.will_drop]

    # 2. Align time-series
    if ts_config:
        df = align_time_series(df, ts_config, raw_table)

    # 3. Final zero-null imputation
    df = impute_zero_nulls(df, ts_config)

    # Hard assertion
    remaining_nulls = df.isnull().sum().sum()
    if remaining_nulls > 0:
        logger.error("[%s] Failed zero-null guarantee. Remaining nulls:\n%s",
                     raw_table, df.isnull().sum()[df.isnull().sum() > 0])
        raise ValueError(f"Zero null guarantee failed for {raw_table}")

    # Add processing timestamp
    df["cleaned_at"] = pd.Timestamp.utcnow()

    # Write output
    logger.info("[%s] Writing %d rows, %d cols to %s",
                raw_table, len(df), len(df.columns), processed_table)
    write_dataframe(df, processed_table, engine)

    return TableCleaningReport(
        table_name=raw_table,
        rows_before=rows_before,
        rows_after=len(df),
        cols_before=cols_before,
        cols_after=len(df.columns),
        cols_dropped=cols_dropped
    )


# =============================================================================
# ── Orchestration entry point ─────────────────────────────────────────────────
# =============================================================================

def main() -> None:
    separator = "=" * 65

    logger.info(separator)
    logger.info("Supply Chain Pipeline — Data Cleaning Starting")
    logger.info(separator)

    engine = get_engine()
    if not test_connection(engine):
        logger.critical("Cannot reach PostgreSQL. Exiting.")
        return

    available_tables = list_tables(engine)
    outcomes: dict[str, str] = {}
    all_reports: list[TableCleaningReport] = []

    for raw_table, processed_table in RAW_TO_PROCESSED.items():
        if raw_table not in available_tables:
            logger.warning("Table '%s' not found in database. Skipping.", raw_table)
            outcomes[raw_table] = "NOT FOUND"
            continue

        try:
            report = process_table(raw_table, processed_table, engine)
            if report:
                all_reports.append(report)
                outcomes[raw_table] = "SUCCESS"
            else:
                outcomes[raw_table] = "EMPTY/SKIPPED"
        except Exception as exc:
            logger.error("Failed processing '%s': %s", raw_table, exc, exc_info=True)
            outcomes[raw_table] = "ERROR"

    # Final summary
    logger.info("")
    logger.info(separator)
    logger.info("Cleaning Pipeline Complete — Table Summary:")
    logger.info(separator)

    for table, status in outcomes.items():
        logger.info("  %-25s %s", table, status)

    if all_reports:
        logger.info("")
        logger.info("Detailed Execution Changes:")
        logger.info("  %-15s %10s %10s %10s %10s", "Table", "Rows(In)", "Rows(Out)", "Cols(In)", "Dropped")
        logger.info("  " + "-" * 60)
        for rpt in all_reports:
            logger.info(
                "  %-15s %10d %10d %10d %10d",
                rpt.table_name.replace("raw_", ""),
                rpt.rows_before,
                rpt.rows_after,
                rpt.cols_before,
                len(rpt.cols_dropped),
            )

    logger.info(separator)


if __name__ == "__main__":
    main()
