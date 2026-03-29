# =============================================================================
# test_db.py
# Supply Chain Data Pipeline — Database Smoke Test
#
# Verifies that db_utils.py works end-to-end against a live PostgreSQL
# instance. Run this AFTER `docker compose up -d` and AFTER copying
# .env.example → .env with real credentials.
#
# Run:
#   uv run python data_pipeline/test_db.py       (from repo root)
#   uv run test_db.py                            (from data_pipeline/)
#
# Exit codes:
#   0 — all checks passed
#   1 — one or more checks failed
# =============================================================================

from __future__ import annotations

import sys
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment — load .env relative to this file so the script works from
# any working directory.
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
logger = logging.getLogger("test_db")

# ---------------------------------------------------------------------------
# Import db_utils from the same directory as this script
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
import db_utils  # noqa: E402  (import after sys.path manipulation)


# =============================================================================
# Test helpers
# =============================================================================

_PASS  = "✅ PASS"
_FAIL  = "❌ FAIL"
_results: list[tuple[str, bool, str]] = []   # (test_name, passed, detail)


def _record(name: str, passed: bool, detail: str = "") -> None:
    """Record a test outcome and print it immediately."""
    status = _PASS if passed else _FAIL
    msg = f"  {status}  {name}"
    if detail:
        msg += f"  —  {detail}"
    print(msg)
    _results.append((name, passed, detail))


def _section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# =============================================================================
# Test: 1 — Engine creation
# =============================================================================

def test_engine_creation() -> db_utils.Engine | None:
    """Verify that get_engine() returns a usable Engine without raising."""
    _section("1 · Engine Creation")
    try:
        engine = db_utils.get_engine(echo=False)
        _record("get_engine() returns an Engine", True, str(engine.url).replace(str(engine.url.password), "***"))
        return engine
    except Exception as exc:
        _record("get_engine() returns an Engine", False, str(exc))
        return None


# =============================================================================
# Test: 2 — Connectivity
# =============================================================================

def test_connectivity(engine) -> bool:
    """Run test_connection() and verify it returns True."""
    _section("2 · Database Connectivity  (SELECT 1)")
    if engine is None:
        _record("test_connection()", False, "Engine is None — cannot proceed")
        return False

    ok = db_utils.test_connection(engine)
    _record(
        "test_connection() returns True",
        ok,
        "Postgres is reachable" if ok else "Could not reach Postgres — is docker compose up?",
    )
    return ok


# =============================================================================
# Test: 3 — Write DataFrame
# =============================================================================

_TEST_TABLE = "_pipeline_smoke_test"

def _make_test_dataframe() -> pd.DataFrame:
    """Create a small DataFrame with mixed types to stress the writer."""
    return pd.DataFrame({
        "id":          [1, 2, 3, 4, 5],
        "ticker":      ["AAPL", "MSFT", "AMZN", "TSLA", "WMT"],
        "revenue":     [100.5, 200.0, None, 400.25, 500.0],   # intentional null
        "on_ground":   [True, False, True, False, True],
        "label":       ["alpha", "beta", None, "delta", "epsilon"],  # intentional null
        "period_date": pd.to_datetime(["2024-01-01", "2024-04-01", "2024-07-01",
                                        "2024-10-01", "2025-01-01"]),
    })


def test_write_dataframe(engine, connected: bool) -> bool:
    """Write a test DataFrame to Postgres and verify the row count returned."""
    _section("3 · Write DataFrame → Postgres")
    if not connected:
        _record("write_dataframe()", False, "Skipped — no DB connection")
        return False

    df = _make_test_dataframe()
    try:
        n = db_utils.write_dataframe(df, _TEST_TABLE, engine, if_exists="replace")
        expected = len(df)
        ok = n == expected
        _record(
            f"write_dataframe() returns correct row count ({expected})",
            ok,
            f"got {n}",
        )
        return ok
    except Exception as exc:
        _record("write_dataframe() raises no exception", False, str(exc))
        return False


# =============================================================================
# Test: 4 — table_exists
# =============================================================================

def test_table_exists(engine, write_ok: bool) -> bool:
    """Confirm the test table now appears in the schema."""
    _section("4 · table_exists()")
    if not write_ok:
        _record("table_exists() detects written table", False, "Skipped — write failed")
        return False

    try:
        exists = db_utils.table_exists(_TEST_TABLE, engine)
        _record(
            f"table_exists('{_TEST_TABLE}') is True",
            exists,
            "found in information_schema" if exists else "NOT found — unexpected",
        )

        # Also check a definitely-absent table
        absent = db_utils.table_exists("_definitely_does_not_exist_xyzzy", engine)
        _record(
            "table_exists('_definitely_does_not_exist_xyzzy') is False",
            not absent,
            "correctly reported absent" if not absent else "WRONGLY reported present",
        )
        return exists and not absent
    except Exception as exc:
        _record("table_exists() raises no exception", False, str(exc))
        return False


# =============================================================================
# Test: 5 — list_tables
# =============================================================================

def test_list_tables(engine, write_ok: bool) -> bool:
    """Confirm list_tables() returns a list that includes the test table."""
    _section("5 · list_tables()")
    if not write_ok:
        _record("list_tables() includes written table", False, "Skipped — write failed")
        return False

    try:
        tables = db_utils.list_tables(engine)
        ok_type = isinstance(tables, list)
        ok_contains = _TEST_TABLE in tables
        _record("list_tables() returns a list", ok_type, f"type={type(tables).__name__}")
        _record(
            f"list_tables() contains '{_TEST_TABLE}'",
            ok_contains,
            f"tables found: {tables}",
        )
        return ok_type and ok_contains
    except Exception as exc:
        _record("list_tables() raises no exception", False, str(exc))
        return False


# =============================================================================
# Test: 6 — get_row_count
# =============================================================================

def test_get_row_count(engine, write_ok: bool) -> bool:
    """Verify get_row_count() returns the expected number of rows."""
    _section("6 · get_row_count()")
    if not write_ok:
        _record("get_row_count() returns correct count", False, "Skipped — write failed")
        return False

    expected = 5   # _make_test_dataframe() has 5 rows
    try:
        count = db_utils.get_row_count(_TEST_TABLE, engine)
        ok = count == expected
        _record(
            f"get_row_count() == {expected}",
            ok,
            f"got {count}",
        )
        return ok
    except Exception as exc:
        _record("get_row_count() raises no exception", False, str(exc))
        return False


# =============================================================================
# Test: 7 — read_table
# =============================================================================

def test_read_table(engine, write_ok: bool) -> bool:
    """Read the test table back and validate shape, dtypes, and null preservation."""
    _section("7 · read_table() — Round-trip Integrity")
    if not write_ok:
        _record("read_table() round-trip", False, "Skipped — write failed")
        return False

    try:
        df_back = db_utils.read_table(_TEST_TABLE, engine)
    except Exception as exc:
        _record("read_table() raises no exception", False, str(exc))
        return False

    original = _make_test_dataframe()
    all_ok = True

    # ── Row count ─────────────────────────────────────────────────────────
    ok_rows = len(df_back) == len(original)
    _record(
        f"Row count matches ({len(original)})",
        ok_rows,
        f"got {len(df_back)}",
    )
    all_ok = all_ok and ok_rows

    # ── Column presence ────────────────────────────────────────────────────
    expected_cols = set(original.columns)
    returned_cols = set(df_back.columns)
    ok_cols = expected_cols.issubset(returned_cols)
    _record(
        "All written columns are present in read-back",
        ok_cols,
        f"missing: {expected_cols - returned_cols}" if not ok_cols else "all present",
    )
    all_ok = all_ok and ok_cols

    # ── Null preservation ──────────────────────────────────────────────────
    # revenue row 2 (index 2) was None; it should come back as NaN
    if "revenue" in df_back.columns:
        null_preserved = df_back["revenue"].isnull().sum() == 1
        _record(
            "Null in 'revenue' column preserved after round-trip",
            null_preserved,
            f"null count = {df_back['revenue'].isnull().sum()} (expected 1)",
        )
        all_ok = all_ok and null_preserved

    # ── String null preservation ───────────────────────────────────────────
    if "label" in df_back.columns:
        str_null_preserved = df_back["label"].isnull().sum() == 1
        _record(
            "Null in 'label' string column preserved after round-trip",
            str_null_preserved,
            f"null count = {df_back['label'].isnull().sum()} (expected 1)",
        )
        all_ok = all_ok and str_null_preserved

    # ── Data values spot-check ─────────────────────────────────────────────
    if "ticker" in df_back.columns:
        tickers_back = set(df_back["ticker"].dropna().tolist())
        tickers_orig = set(original["ticker"].tolist())
        ok_values = tickers_back == tickers_orig
        _record(
            "Ticker values match original",
            ok_values,
            f"got {sorted(tickers_back)}, expected {sorted(tickers_orig)}",
        )
        all_ok = all_ok and ok_values

    return all_ok


# =============================================================================
# Test: 8 — read_query
# =============================================================================

def test_read_query(engine, write_ok: bool) -> bool:
    """Execute a parameterised SELECT query and verify the result."""
    _section("8 · read_query() — Parameterised SQL")
    if not write_ok:
        _record("read_query() returns correct rows", False, "Skipped — write failed")
        return False

    sql = f'SELECT ticker, revenue FROM "{_TEST_TABLE}" WHERE ticker = :ticker'
    try:
        df_q = db_utils.read_query(sql, engine, params={"ticker": "AAPL"})
        ok_rows = len(df_q) == 1
        ok_val  = (
            "revenue" in df_q.columns
            and abs(float(df_q["revenue"].iloc[0]) - 100.5) < 1e-6
        )
        _record(
            "read_query() returns 1 row for ticker='AAPL'",
            ok_rows,
            f"got {len(df_q)} row(s)",
        )
        _record(
            "read_query() revenue value == 100.5",
            ok_val,
            f"got {df_q['revenue'].iloc[0] if len(df_q) else 'N/A'}",
        )
        return ok_rows and ok_val
    except Exception as exc:
        _record("read_query() raises no exception", False, str(exc))
        return False


# =============================================================================
# Test: 9 — append mode
# =============================================================================

def test_append_mode(engine, write_ok: bool) -> bool:
    """Write a second batch in append mode and verify the total row count doubles."""
    _section("9 · write_dataframe() — Append Mode")
    if not write_ok:
        _record("append mode doubles row count", False, "Skipped — write failed")
        return False

    extra = _make_test_dataframe()
    try:
        db_utils.write_dataframe(extra, _TEST_TABLE, engine, if_exists="append")
        count_after = db_utils.get_row_count(_TEST_TABLE, engine)
        expected = len(extra) * 2   # original 5 + appended 5
        ok = count_after == expected
        _record(
            f"Row count after append == {expected}",
            ok,
            f"got {count_after}",
        )
        return ok
    except Exception as exc:
        _record("write_dataframe(if_exists='append') raises no exception", False, str(exc))
        return False


# =============================================================================
# Test: 10 — cleanup
# =============================================================================

def test_cleanup(engine, connected: bool) -> bool:
    """Drop the smoke-test table to leave the database clean."""
    _section("10 · Cleanup — Drop Test Table")
    if not connected:
        _record("DROP test table", False, "Skipped — no DB connection")
        return False

    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{_TEST_TABLE}"'))
        still_exists = db_utils.table_exists(_TEST_TABLE, engine)
        ok = not still_exists
        _record(
            f"Test table '{_TEST_TABLE}' dropped successfully",
            ok,
            "table gone" if ok else "table STILL EXISTS — manual cleanup needed",
        )
        return ok
    except Exception as exc:
        _record("DROP raises no exception", False, str(exc))
        return False


# =============================================================================
# Main
# =============================================================================

def main() -> int:
    print("=" * 60)
    print("  Supply Chain Pipeline — Database Smoke Test")
    print("=" * 60)
    print(f"  .env path : {_ENV_FILE}")
    print(f"  Test table: {_TEST_TABLE}")

    # ── Run all tests in dependency order ─────────────────────────────────
    engine    = test_engine_creation()
    connected = test_connectivity(engine)
    write_ok  = test_write_dataframe(engine, connected)
    test_table_exists(engine, write_ok)
    test_list_tables(engine, write_ok)
    test_get_row_count(engine, write_ok)
    test_read_table(engine, write_ok)
    test_read_query(engine, write_ok)
    test_append_mode(engine, write_ok)
    test_cleanup(engine, connected)

    # ── Summary ───────────────────────────────────────────────────────────
    total   = len(_results)
    passed  = sum(1 for _, ok, _ in _results if ok)
    failed  = total - passed

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  ({failed} FAILED)")
    else:
        print("  — all green ✅")
    print("=" * 60)

    if failed:
        print("\n  Failed tests:")
        for name, ok, detail in _results:
            if not ok:
                print(f"    ❌  {name}")
                if detail:
                    print(f"        {detail}")
        print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
