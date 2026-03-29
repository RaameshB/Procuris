# =============================================================================
# ingest_csv.py
# Supply Chain Data Pipeline — Manual CSV Loader (UN Comtrade)
#
# Reads one or more manually downloaded UN Comtrade CSV files from the local
# `data_pipeline/raw_csvs/` directory and pushes the combined dataset into
# the `raw_comtrade` PostgreSQL table.
#
# UN Comtrade is the United Nations' international merchandise trade statistics
# database. It publishes bilateral trade flows (exports + imports) for ~200
# countries, broken down by HS commodity code — essential for mapping global
# supply-chain exposure by product category and trade corridor.
#
# How to get Comtrade CSV files:
#   1. Visit https://comtradeplus.un.org/  (free account required)
#   2. Use the "Bulk Download" or "Query" tool to select:
#        - Reporter(s): e.g. "United States", "China", "Germany"
#        - Partner(s):  e.g. "World" (aggregated) or specific countries
#        - Commodity:   HS 2-digit / 4-digit / 6-digit codes of interest
#        - Period:      Year or month range
#        - Trade flow:  Import, Export, or both
#   3. Download as CSV and place the file(s) in: data_pipeline/raw_csvs/
#
# Run:
#   uv run python data_pipeline/ingest_csv.py          (from repo root)
#   uv run ingest_csv.py                               (from data_pipeline/)
# =============================================================================

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from db_utils import get_engine, test_connection, write_dataframe

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

# Directory where manually downloaded UN Comtrade CSV files are placed.
# Path is resolved relative to this script file, so it works regardless of
# the caller's working directory.
RAW_CSV_DIR: Path = Path(__file__).parent / "raw_csvs"

# Target PostgreSQL table name
TARGET_TABLE: str = "raw_comtrade"

# When True, a pre-existing raw_comtrade table is completely replaced each run.
# Set to "append" if you want to accumulate multiple ingestion runs.
IF_EXISTS_MODE: str = "replace"

# Maximum number of rows to display in the summary preview log
PREVIEW_ROWS: int = 3

# ---------------------------------------------------------------------------
# Column name normalisation map
# ---------------------------------------------------------------------------
# The UN Comtrade "bulk download" CSV format uses human-readable column names
# with spaces and special characters that are awkward in SQL.  We rename them
# to snake_case equivalents while preserving every field.
#
# This map covers both the legacy Comtrade+ format and the newer API v2 format.
# Columns NOT listed here are kept as-is (lowercased & spaces→underscores by
# the fallback normaliser below).
COMTRADE_COLUMN_MAP: dict[str, str] = {
    # ── Metadata ──────────────────────────────────────────────────────────
    "Classification":       "classification",
    "Type Code":            "type_code",
    "Freq Code":            "freq_code",
    "Ref Year":             "ref_year",
    "Ref Month":            "ref_month",
    "Period":               "period",
    "Period Desc.":         "period_desc",
    "Aggregate Level":      "aggregate_level",
    "Is Leaf Code":         "is_leaf_code",
    # ── Trade flow ────────────────────────────────────────────────────────
    "Flow Code":            "flow_code",
    "Flow Desc":            "flow_desc",
    "Trade Flow Code":      "trade_flow_code",
    "Trade Flow":           "trade_flow",
    # ── Reporter (the country filing the statistics) ───────────────────────
    "Reporter Code":        "reporter_code",
    "Reporter":             "reporter",
    "Reporter ISO":         "reporter_iso",
    "Reporter Desc":        "reporter_desc",
    # ── Partner (the counterpart country in the trade) ─────────────────────
    "Partner Code":         "partner_code",
    "Partner":              "partner",
    "Partner ISO":          "partner_iso",
    "Partner Desc":         "partner_desc",
    # ── Second partner (for re-exports) ───────────────────────────────────
    "2nd Partner Code":     "second_partner_code",
    "2nd Partner":          "second_partner",
    "2nd Partner ISO":      "second_partner_iso",
    "2nd Partner Desc":     "second_partner_desc",
    # ── Commodity / product ───────────────────────────────────────────────
    "Cmd Code":             "commodity_code",
    "Commodity Code":       "commodity_code",
    "Cmd Desc":             "commodity_desc",
    "Commodity":            "commodity_desc",
    "Ag Level":             "hs_ag_level",
    # ── Custom procedure ──────────────────────────────────────────────────
    "Customs Code":         "customs_code",
    "Customs Desc":         "customs_desc",
    "Mos Code":             "mos_code",
    "Mos Desc":             "mos_desc",
    # ── Quantity & value ──────────────────────────────────────────────────
    "Qty Unit Code":        "qty_unit_code",
    "Qty Unit":             "qty_unit",
    "Qty":                  "qty",
    "Alt Qty Unit Code":    "alt_qty_unit_code",
    "Alt Qty Unit":         "alt_qty_unit",
    "Alt Qty":              "alt_qty",
    "Netweight (kg)":       "netweight_kg",
    "Net Weight (kg)":      "netweight_kg",
    "Gross Weight (kg)":    "gross_weight_kg",
    "CIF Value (US$)":      "cif_value_usd",
    "FOB Value (US$)":      "fob_value_usd",
    "Trade Value (US$)":    "trade_value_usd",
    "Primary Value":        "primary_value_usd",
    # ── Flags ─────────────────────────────────────────────────────────────
    "Flag":                 "flag",
    "Is Reported":          "is_reported",
    "Is Aggregate":         "is_aggregate",
}

# Numeric columns that should be cast from string → float after loading
NUMERIC_COLUMNS: list[str] = [
    "ref_year", "ref_month", "period",
    "reporter_code", "partner_code",
    "aggregate_level", "is_leaf_code",
    "qty", "alt_qty",
    "netweight_kg", "gross_weight_kg",
    "cif_value_usd", "fob_value_usd",
    "trade_value_usd", "primary_value_usd",
    "flag",
]


# =============================================================================
# ── Helper: normalise any remaining column names ──────────────────────────────
# =============================================================================


def _normalise_column_name(col: str) -> str:
    """
    Convert a raw CSV column header to a SQL-safe snake_case name.

    Applies after the explicit ``COMTRADE_COLUMN_MAP`` lookup so that any
    columns not in the map still get a clean name.

    Transformations:
        - Strip leading/trailing whitespace
        - Lower-case everything
        - Replace spaces and hyphens with underscores
        - Remove characters that are invalid in Postgres identifiers (parens,
          dots, dollar signs, percent signs, slashes)

    Args:
        col: Raw column name from the CSV header row.

    Returns:
        A lowercase, underscore-separated identifier string.
    """
    import re
    col = col.strip().lower()
    col = re.sub(r"[\s\-]+", "_", col)                  # spaces/hyphens → _
    col = re.sub(r"[().$%/\\]", "", col)                 # remove illegal chars
    col = re.sub(r"_+", "_", col)                        # collapse repeated _
    col = col.strip("_")                                 # trim leading/trailing _
    return col


# =============================================================================
# ── Core CSV loading function ─────────────────────────────────────────────────
# =============================================================================


def load_comtrade_csv(filepath: Path) -> pd.DataFrame:
    """
    Read a single UN Comtrade CSV file into a cleaned, normalised DataFrame.

    Processing steps:
        1. Attempt UTF-8 read; fall back to Latin-1 for files exported by
           older Comtrade tools (common with certain country names).
        2. Rename columns via ``COMTRADE_COLUMN_MAP``; apply the fallback
           normaliser to any unmapped columns.
        3. Deduplicate column names introduced by the normaliser.
        4. Strip leading/trailing whitespace from all string columns.
        5. Coerce known numeric columns (quantities, values, weights).
        6. Attach provenance metadata: ``source_file`` and ``loaded_at``.

    Args:
        filepath: Absolute or relative path to the CSV file.

    Returns:
        A normalised pandas DataFrame, or an empty DataFrame on failure.
    """
    logger.info("[CSV] Loading: %s", filepath.name)

    # ── Step 1: Read raw CSV ──────────────────────────────────────────────────
    df: pd.DataFrame | None = None

    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(
                filepath,
                encoding=encoding,
                low_memory=False,   # avoid mixed-type warnings on large files
                dtype=str,          # read everything as string; coerce later
                na_values=["", "NA", "N/A", "null", "NULL", "None", "#N/A"],
                keep_default_na=True,
            )
            logger.info(
                "[CSV] %s: read successfully with encoding '%s' — "
                "shape: %d rows × %d cols.",
                filepath.name, encoding, *df.shape,
            )
            break
        except UnicodeDecodeError:
            logger.debug(
                "[CSV] %s: encoding '%s' failed, trying next …",
                filepath.name, encoding,
            )
        except pd.errors.ParserError as exc:
            logger.error(
                "[CSV] %s: CSV parsing error with encoding '%s': %s",
                filepath.name, encoding, exc,
            )
            break
        except Exception as exc:
            logger.error("[CSV] %s: unexpected read error: %s", filepath.name, exc)
            return pd.DataFrame()

    if df is None or df.empty:
        logger.warning("[CSV] %s: could not be read or is empty.", filepath.name)
        return pd.DataFrame()

    # ── Step 2: Rename columns ────────────────────────────────────────────────
    # Apply the explicit map first; then apply the fallback normaliser to any
    # column that wasn't in the map.
    rename_map: dict[str, str] = {}
    for raw_col in df.columns:
        if raw_col in COMTRADE_COLUMN_MAP:
            rename_map[raw_col] = COMTRADE_COLUMN_MAP[raw_col]
        else:
            rename_map[raw_col] = _normalise_column_name(raw_col)

    df.rename(columns=rename_map, inplace=True)

    # ── Step 3: Resolve duplicate column names ────────────────────────────────
    # Renaming can introduce duplicates (e.g. two raw columns both mapping to
    # "commodity_code"). Suffix subsequent duplicates to make them unique.
    seen: set[str] = set()
    new_cols: list[str] = []
    for i, col in enumerate(df.columns):
        if col in seen:
            # Suffix with its ordinal position to make it unique
            unique_col = f"{col}_{i}"
            new_cols.append(unique_col)
            logger.debug("[CSV] Duplicate column renamed: '%s' → '%s'", col, unique_col)
            seen.add(unique_col)
        else:
            new_cols.append(col)
            seen.add(col)
    df.columns = pd.Index(new_cols)

    # ── Step 4: Strip whitespace from string columns ──────────────────────────
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda series: series.str.strip())

    # ── Step 5: Coerce numeric columns ───────────────────────────────────────
    coerced = 0
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            # Strip thousand-separator commas and currency symbols before casting
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
            coerced += 1

    logger.info("[CSV] %s: coerced %d numeric column(s).", filepath.name, coerced)

    # ── Step 6: Provenance metadata ───────────────────────────────────────────
    df["source_file"] = filepath.name
    df["loaded_at"]   = pd.Timestamp.utcnow()

    logger.info(
        "[CSV] %s: finished normalisation — final shape: %d rows × %d cols.",
        filepath.name, *df.shape,
    )
    return df


# =============================================================================
# ── Validation helpers ────────────────────────────────────────────────────────
# =============================================================================


def _validate_dataframe(df: pd.DataFrame, source: str) -> list[str]:
    """
    Run lightweight sanity checks on a loaded Comtrade DataFrame and return
    a list of warning strings (empty list = no issues detected).

    Checks performed:
        - ``trade_value_usd`` column present and non-entirely-null
        - ``commodity_code`` column present (critical for supply-chain use)
        - No rows with both ``reporter_code`` and ``partner_code`` null
        - ``ref_year`` values are within a plausible range (2000–2030)

    Args:
        df:     The loaded and normalised DataFrame to validate.
        source: File name for log messages.

    Returns:
        List of human-readable warning strings.
    """
    warnings: list[str] = []

    if "trade_value_usd" not in df.columns:
        warnings.append(
            f"{source}: 'trade_value_usd' column missing — "
            "check that the CSV was exported with trade value included."
        )
    elif df["trade_value_usd"].isna().all():
        warnings.append(
            f"{source}: 'trade_value_usd' is entirely null — "
            "numeric coercion may have failed."
        )

    if "commodity_code" not in df.columns:
        warnings.append(
            f"{source}: 'commodity_code' column missing — "
            "verify the Comtrade export settings."
        )

    if "reporter_code" in df.columns and "partner_code" in df.columns:
        both_null = (
            df["reporter_code"].isna() & df["partner_code"].isna()
        ).sum()
        if both_null > 0:
            warnings.append(
                f"{source}: {both_null} row(s) have both reporter_code AND "
                "partner_code null — possible header/encoding mismatch."
            )

    if "ref_year" in df.columns:
        valid_years = df["ref_year"].dropna()
        if len(valid_years) > 0:
            min_yr, max_yr = valid_years.min(), valid_years.max()
            if min_yr < 2000 or max_yr > 2030:
                warnings.append(
                    f"{source}: ref_year range [{min_yr:.0f}–{max_yr:.0f}] looks "
                    "suspicious. Verify the downloaded file covers the intended period."
                )

    return warnings


def _log_preview(df: pd.DataFrame, n: int = PREVIEW_ROWS) -> None:
    """Log a brief preview of the combined DataFrame to aid visual QA."""
    if df.empty:
        return
    preview = df.head(n).to_string(max_cols=8, max_colwidth=25)
    logger.info("Preview (first %d rows):\n%s", n, preview)

    # Log null rates for key columns
    key_cols = [
        c for c in ("reporter", "partner", "commodity_code",
                    "trade_value_usd", "netweight_kg", "ref_year")
        if c in df.columns
    ]
    if key_cols:
        null_pct = df[key_cols].isnull().mean().mul(100).round(1)
        logger.info(
            "Null rates for key columns:\n%s",
            null_pct.to_string(),
        )


# =============================================================================
# ── Main entry point ──────────────────────────────────────────────────────────
# =============================================================================


def main() -> None:
    """
    Discover all CSV files in ``raw_csvs/``, load and validate each one,
    combine them into a single DataFrame, and write to ``raw_comtrade``.

    Behaviour:
        - Files are processed alphabetically for reproducibility.
        - Each file is validated independently; warnings are logged but do
          not halt the pipeline — partial data is better than no data.
        - All files are combined into one DataFrame before writing, which
          avoids repeated table truncation when multiple files exist.
        - The ``source_file`` column on every row tracks which CSV it came from.
    """
    separator = "=" * 65

    logger.info(separator)
    logger.info("Supply Chain Pipeline — UN Comtrade CSV Ingestion")
    logger.info(separator)

    # ── Validate directory ────────────────────────────────────────────────────
    if not RAW_CSV_DIR.exists():
        logger.error(
            "CSV directory not found: %s\n"
            "  Create it and place UN Comtrade CSV files inside:\n"
            "    mkdir -p data_pipeline/raw_csvs/\n"
            "  Then download CSVs from https://comtradeplus.un.org/ and place\n"
            "  them there before re-running this script.",
            RAW_CSV_DIR,
        )
        return

    # Gather all CSVs, sorted alphabetically for deterministic ordering
    csv_files = sorted(RAW_CSV_DIR.glob("*.csv"))

    if not csv_files:
        logger.warning(
            "No CSV files found in %s\n"
            "  Expected at least one file matching *.csv\n"
            "  Download from https://comtradeplus.un.org/ and place the\n"
            "  file(s) in data_pipeline/raw_csvs/ before re-running.",
            RAW_CSV_DIR,
        )
        return

    logger.info("Found %d CSV file(s) to process.", len(csv_files))

    # ── Connect to database ───────────────────────────────────────────────────
    engine = get_engine()
    if not test_connection(engine):
        logger.critical(
            "Cannot reach the PostgreSQL database. "
            "Is docker compose up? Are the .env credentials correct? Exiting."
        )
        return

    # ── Load and validate each file ───────────────────────────────────────────
    loaded_frames: list[pd.DataFrame] = []
    file_summaries: list[dict] = []

    for csv_path in csv_files:
        df = load_comtrade_csv(csv_path)

        summary = {
            "file":    csv_path.name,
            "rows":    len(df),
            "cols":    df.shape[1] if not df.empty else 0,
            "status":  "OK" if not df.empty else "EMPTY / FAILED",
            "warnings": [],
        }

        if df.empty:
            logger.warning("[CSV] %s produced an empty DataFrame — skipping.", csv_path.name)
            file_summaries.append(summary)
            continue

        # Run validation checks
        issues = _validate_dataframe(df, csv_path.name)
        if issues:
            summary["warnings"] = issues
            for issue in issues:
                logger.warning("[CSV] Validation warning: %s", issue)

        loaded_frames.append(df)
        file_summaries.append(summary)

    # ── Bail out if nothing loaded ────────────────────────────────────────────
    if not loaded_frames:
        logger.error(
            "No data was successfully loaded from any CSV file. "
            "Review the warnings above."
        )
        return

    # ── Combine and write ─────────────────────────────────────────────────────
    logger.info(
        "Concatenating %d DataFrame(s) into a single dataset …",
        len(loaded_frames),
    )
    combined_df = pd.concat(loaded_frames, ignore_index=True, sort=False)
    logger.info(
        "Combined DataFrame: %d rows × %d columns.",
        *combined_df.shape,
    )

    # Log a brief preview for visual QA
    _log_preview(combined_df)

    # Write to Postgres — replaces the table so the pipeline is idempotent
    rows_written = write_dataframe(
        combined_df,
        TARGET_TABLE,
        engine,
        if_exists=IF_EXISTS_MODE,
    )

    # ── Print run summary ─────────────────────────────────────────────────────
    logger.info("\n%s", separator)
    logger.info("UN Comtrade CSV Ingestion Complete")
    logger.info(separator)
    logger.info("Files processed: %d", len(csv_files))
    logger.info("Files loaded:    %d", len(loaded_frames))
    logger.info("Total rows:      %d  → written to '%s'", rows_written, TARGET_TABLE)
    logger.info("")
    logger.info("Per-file summary:")
    for s in file_summaries:
        warn_txt = f"  ⚠  {len(s['warnings'])} warning(s)" if s["warnings"] else ""
        logger.info(
            "  %-40s  %6d rows  %3d cols  [%s]%s",
            s["file"], s["rows"], s["cols"], s["status"], warn_txt,
        )
    logger.info(separator)


if __name__ == "__main__":
    main()
