# =============================================================================
# ingest_api.py
# Supply Chain Data Pipeline — Standard API Ingestion
#
# Pulls raw time-series data from six external sources and writes each
# result set to a dedicated raw_* table in PostgreSQL.
#
# Sources & target tables:
#   1. Polygon.io              → raw_polygon
#   2. US Census Bureau (M3)   → raw_census
#   3. OpenSky Network         → raw_opensky
#   4. Open Supply Hub         → raw_oshub
#   5. World Bank Open Data    → raw_worldbank
#   6. FRED (St. Louis Fed)    → raw_fred
#
# Run:
#   uv run python data_pipeline/ingest_api.py          (from repo root)
#   uv run ingest_api.py                               (from data_pipeline/)
#
# Rate limits enforced:
#   - Polygon free tier : 5 calls/min  → 12 s sleep between ticker calls
#   - OpenSky anonymous : polite 1 s   → authenticated users get more headroom
#   - OS Hub            : 1 s between pages
#   - World Bank        : 0.5 s between indicator calls (open API, no key)
#   - FRED              : 0.25 s between series calls   (free key required)
# =============================================================================

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv
from polygon import RESTClient as PolygonRESTClient
from polygon.exceptions import AuthError, BadResponse

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
# ── Configuration constants ───────────────────────────────────────────────────
# =============================================================================

# ── Polygon ──────────────────────────────────────────────────────────────────
# Publicly traded companies spanning retail, logistics, industrials, and tech —
# chosen to capture a broad cross-section of supply-chain activity.
POLYGON_TICKERS: list[str] = [
    "AAPL",  # Apple          — consumer electronics supply chain
    "MSFT",  # Microsoft      — cloud/hardware components
    "AMZN",  # Amazon         — e-commerce fulfillment & logistics
    "TSLA",  # Tesla          — EV manufacturing & battery supply
    "WMT",   # Walmart        — retail inventory management
    "TGT",   # Target         — retail supply chain
    "FDX",   # FedEx          — freight & parcel logistics
    "UPS",   # UPS            — parcel delivery logistics
    "HON",   # Honeywell      — industrial automation
    "CAT",   # Caterpillar    — heavy equipment manufacturing
    "XOM",   # ExxonMobil     — energy / petrochemicals
    "BA",    # Boeing         — aerospace manufacturing
]

# Free tier: 5 API calls per minute → sleep ≥12 s between calls.
POLYGON_RATE_LIMIT_SLEEP: int = 12  # seconds

# Number of quarterly reports to retrieve per ticker (most recent first).
POLYGON_QUARTERLY_LIMIT: int = 100

# ── US Census Bureau ──────────────────────────────────────────────────────────
# M3 — Manufacturers' Shipments, Inventories, and Orders survey.
# Variable reference: https://api.census.gov/data/timeseries/eits/m3/variables.json
CENSUS_M3_BASE_URL: str = "https://api.census.gov/data/timeseries/eits/m3"
CENSUS_M3_GET_VARS: str = (
    "cell_value,"       # Survey value (shipments / inventory / orders)
    "error_data,"       # Standard error / confidence interval
    "time_slot_date,"   # YYYY-MM reference period
    "seasonally_adj,"   # Y/N — whether the figure is seasonally adjusted
    "category_code,"    # Industry / product category code
    "data_type_code,"   # VS=Shipments, II=Inventories, NO=New Orders, IO=Inv/Orders
    "time_slot_id"      # Required by the Census API
)
CENSUS_M3_START_YEAR: str = "2010"  # Pull history from this year forward

# ── OpenSky Network ───────────────────────────────────────────────────────────
OPENSKY_STATES_URL: str = "https://opensky-network.org/api/states/all"

# Column names for the OpenSky /states/all response array.
# Index 17 (category) is only present for authenticated requests.
OPENSKY_STATE_COLUMNS: list[str] = [
    "icao24",         # Unique ICAO 24-bit address (hex string)
    "callsign",       # Aircraft callsign (may be null/whitespace)
    "origin_country", # Country of registration
    "time_position",  # Unix timestamp of last position update (nullable)
    "last_contact",   # Unix timestamp of last any message
    "longitude",      # WGS-84 longitude (nullable)
    "latitude",       # WGS-84 latitude  (nullable)
    "baro_altitude",  # Barometric altitude in metres (nullable)
    "on_ground",      # True if the aircraft is on the ground
    "velocity",       # Ground speed in m/s (nullable)
    "true_track",     # Track angle in degrees clockwise from north (nullable)
    "vertical_rate",  # Vertical rate in m/s; positive = climbing (nullable)
    "sensors",        # Receiver IDs that contributed data (nullable list)
    "geo_altitude",   # Geometric altitude in metres (nullable)
    "squawk",         # Squawk code (nullable)
    "spi",            # Special purpose indicator flag
    "position_source",# 0=ADS-B, 1=ASTERIX, 2=MLAT, 3=FLARM
    "category",       # Aircraft category (authenticated only; nullable)
]


# ── World Bank Open Data ──────────────────────────────────────────────────────
# Open API — no key required.
# Docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/898581
#
# We pass a semicolon-joined list of ISO-2 country codes; the API returns one
# record per (country, year) pair for the requested indicator.
WORLDBANK_BASE_URL: str = "https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}"

# Major economies and key supply-chain hubs.
WORLDBANK_COUNTRIES: list[str] = [
    "US", "CN", "DE", "JP", "KR", "GB", "FR", "IN",
    "CA", "MX", "VN", "SG", "NL", "BE", "TH", "ID",
    "BR", "AU", "CH", "SA",
]

# Indicators to pull.  Key:   World Bank series code
#                      Value: snake_case column name used in the raw table
WORLDBANK_INDICATORS: dict[str, str] = {
    # Macro / trade fundamentals
    "NY.GDP.MKTP.CD":   "gdp_current_usd",          # Annual GDP (current US$)
    "NE.TRD.GNFS.ZS":  "trade_pct_gdp",             # Trade as % of GDP
    "TX.VAL.MRCH.CD.WT": "merchandise_exports_usd", # Merchandise exports (US$)
    "TM.VAL.MRCH.CD.WT": "merchandise_imports_usd", # Merchandise imports (US$)
    "BX.GSR.NFSV.CD":  "services_exports_usd",      # Service exports (US$)
    "BM.GSR.NFSV.CD":  "services_imports_usd",      # Service imports (US$)
    # Logistics Performance Index (biennial — interpolated to annual in clean step)
    "LP.LPI.OVRL.XQ":  "lpi_overall",               # LPI: overall score
    "LP.LPI.CUST.XQ":  "lpi_customs",               # LPI: customs efficiency
    "LP.LPI.INFR.XQ":  "lpi_infrastructure",        # LPI: infrastructure quality
    "LP.LPI.TRAC.XQ":  "lpi_tracking_tracing",      # LPI: tracking & tracing
    "LP.LPI.TIME.XQ":  "lpi_timeliness",            # LPI: shipment timeliness
    # Labor & production
    "SL.TLF.TOTL.IN":  "labour_force_total",        # Total labour force
    "NV.IND.MANF.ZS":  "manufacturing_pct_gdp",     # Manufacturing value added % GDP
}

WORLDBANK_START_YEAR: int = 2010
WORLDBANK_END_YEAR:   int = 2024
WORLDBANK_INTER_CALL_SLEEP: float = 0.5   # seconds between indicator calls

# ── FRED (Federal Reserve Bank of St. Louis) ──────────────────────────────────
# Free API key required: https://fred.stlouisfed.org/docs/api/api_key.html
# (Instant, no cost, no usage limits for reasonable access patterns.)
FRED_BASE_URL: str = "https://api.stlouisfed.org/fred/series/observations"
FRED_OBSERVATION_START: str = "2010-01-01"

# Series to pull.  Key:   FRED series ID
#                  Value: snake_case label stored in the series_name column
FRED_SERIES: dict[str, str] = {
    # Manufacturing & orders (directly supply-chain relevant)
    "AMTMNO":        "mfg_new_orders_usd",           # New orders: total manufacturing
    "AMTMVS":        "mfg_shipments_usd",            # Shipments: total manufacturing
    "AMTMUO":        "mfg_unfilled_orders_usd",      # Unfilled orders: manufacturing
    "AMTMTI":        "mfg_total_inventories_usd",    # Total inventories: manufacturing
    # Inventory & utilisation
    "ISRATIO":       "inventory_to_sales_ratio",     # Total business inventory/sales
    "TCU":           "capacity_utilization_pct",     # Total industry capacity utilisation
    "INDPRO":        "industrial_production_index",  # Industrial production index
    # Prices & costs
    "WPU00000000":   "producer_price_index",         # Producer price index (all commodities)
    "CPIAUCSL":      "consumer_price_index",         # CPI: all urban consumers
    "DCOILWTICO":    "crude_oil_wti_usd",            # WTI crude oil spot price (daily→monthly)
    # Labour & demand signals
    "PAYEMS":        "nonfarm_payrolls_thousands",   # Total nonfarm payrolls
    "RSXFS":         "retail_sales_ex_food_usd",     # Advance retail & food services sales
}

FRED_INTER_CALL_SLEEP: float = 0.25   # seconds between series calls

# ── General HTTP settings ─────────────────────────────────────────────────────
REQUEST_TIMEOUT: int = 30       # seconds before a request is aborted
MAX_RETRIES: int = 3            # total attempts per request
RETRY_BACKOFF_BASE: int = 10    # base backoff in seconds; multiplied by attempt number


# =============================================================================
# ── Shared HTTP helper ────────────────────────────────────────────────────────
# =============================================================================


def _http_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    auth: tuple[str, str] | None = None,
    max_retries: int = MAX_RETRIES,
    backoff_base: int = RETRY_BACKOFF_BASE,
) -> requests.Response:
    """
    Perform an HTTP GET with retry logic and exponential backoff.

    Handles the following transient conditions automatically:
        - HTTP 429 Too Many Requests  → back off and retry
        - Network timeouts            → back off and retry
        - Connection errors           → back off and retry

    Non-transient HTTP errors (4xx except 429, 5xx) are raised immediately
    via ``raise_for_status()`` so callers know the request will not succeed.

    Args:
        url:          Target URL.
        params:       Query-string parameters dict.
        headers:      Additional HTTP request headers.
        auth:         (username, password) tuple for HTTP Basic Auth.
        max_retries:  Maximum number of attempts before raising.
        backoff_base: Seconds to wait on the first retry; multiplied by attempt.

    Returns:
        A successful ``requests.Response`` object.

    Raises:
        requests.HTTPError: On non-retryable HTTP error responses.
        RuntimeError:       When all retry attempts are exhausted.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                auth=auth,
                timeout=REQUEST_TIMEOUT,
            )

            # ── Rate-limit response: back off and retry ───────────────────
            if response.status_code == 429:
                wait = backoff_base * attempt
                logger.warning(
                    "HTTP 429 Too Many Requests (attempt %d/%d). "
                    "Sleeping %d s before retry …",
                    attempt, max_retries, wait,
                )
                time.sleep(wait)
                continue

            # ── All other non-2xx responses raise immediately ─────────────
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            wait = backoff_base * attempt
            logger.warning(
                "Request timed out (attempt %d/%d). URL: %s. "
                "Retrying in %d s …",
                attempt, max_retries, url, wait,
            )
            if attempt < max_retries:
                time.sleep(wait)

        except requests.exceptions.ConnectionError as exc:
            wait = backoff_base * attempt
            logger.warning(
                "Connection error (attempt %d/%d): %s. "
                "Retrying in %d s …",
                attempt, max_retries, exc, wait,
            )
            if attempt < max_retries:
                time.sleep(wait)

        except requests.exceptions.HTTPError:
            # Non-retryable; let it propagate to the caller.
            raise

    raise RuntimeError(
        f"All {max_retries} attempt(s) failed for URL: {url}"
    )


# =============================================================================
# ── Component 1: Polygon.io — Quarterly Financials ───────────────────────────
# =============================================================================


def _extract_data_point_value(obj: Any, attr: str) -> float | None:
    """
    Safely extract the numeric ``.value`` from a Polygon DataPoint object.

    Polygon financial fields are DataPointWithCurrencyName objects (or None).
    This helper handles the double-None case cleanly.

    Args:
        obj:  A Polygon financial statement sub-object (e.g. IncomeStatement).
        attr: The attribute name on that object (e.g. "revenues").

    Returns:
        The float value, or None if the attribute or its value is absent.
    """
    data_point = getattr(obj, attr, None)
    if data_point is None:
        return None
    return getattr(data_point, "value", None)


def ingest_polygon(engine) -> pd.DataFrame:
    """
    Pull quarterly financial filings for each ticker in ``POLYGON_TICKERS``
    from the Polygon.io Reference Financials endpoint.

    Metrics extracted per filing:
        Income Statement:
          revenues, gross_profit, net_income_loss, operating_income_loss,
          cost_of_revenue, basic_earnings_per_share
        Balance Sheet:
          assets, current_assets, current_liabilities, inventory,
          liabilities, long_term_debt (noncurrent liabilities)
        Cash Flow:
          net_cash_flow, net_cash_flow_from_operating_activities

        Derived:
          gross_profit_margin   = gross_profit / revenues
          net_profit_margin     = net_income_loss / revenues
          inventory_turnover    = cost_of_revenue / inventory
          dso_days              = (current_assets - inventory) / (revenues / 90)
          current_ratio         = current_assets / current_liabilities
          debt_to_assets        = liabilities / assets

    Rate limit: 12 s sleep after each ticker (≤ 5 calls/min on free tier).

    Args:
        engine: SQLAlchemy engine from :func:`db_utils.get_engine`.

    Returns:
        DataFrame of all extracted records (also written to ``raw_polygon``).
    """
    api_key = os.getenv("POLYGON_API_KEY", "").strip()
    if not api_key:
        logger.error(
            "[Polygon] POLYGON_API_KEY is not set in .env. "
            "Skipping Polygon ingestion."
        )
        return pd.DataFrame()

    try:
        client = PolygonRESTClient(api_key)
    except Exception as exc:
        logger.error("[Polygon] Failed to create Polygon client: %s", exc)
        return pd.DataFrame()

    all_records: list[dict] = []

    for idx, ticker in enumerate(POLYGON_TICKERS, start=1):
        logger.info(
            "[Polygon] (%d/%d) Fetching quarterly financials for %s …",
            idx, len(POLYGON_TICKERS), ticker,
        )
        try:
            filings = client.vx.list_stock_financials(
                ticker=ticker,
                timeframe="quarterly",
                limit=POLYGON_QUARTERLY_LIMIT,
                include_sources=False,
            )

            filing_count = 0
            for report in filings:
                row: dict[str, Any] = {
                    "ticker":        ticker,
                    "company_name":  getattr(report, "company_name", None),
                    "cik":           getattr(report, "cik", None),
                    "fiscal_period": getattr(report, "fiscal_period", None),
                    "fiscal_year":   getattr(report, "fiscal_year", None),
                    "start_date":    getattr(report, "start_date", None),
                    "end_date":      getattr(report, "end_date", None),
                    "filing_date":   getattr(report, "filing_date", None),
                }

                fin = getattr(report, "financials", None)

                # ── Income Statement ──────────────────────────────────────
                inc = getattr(fin, "income_statement", None) if fin else None
                row["revenues"]              = _extract_data_point_value(inc, "revenues")
                row["gross_profit"]          = _extract_data_point_value(inc, "gross_profit")
                row["net_income_loss"]       = _extract_data_point_value(inc, "net_income_loss")
                row["operating_income_loss"] = _extract_data_point_value(inc, "operating_income_loss")
                row["cost_of_revenue"]       = _extract_data_point_value(inc, "cost_of_revenue")
                row["basic_eps"]             = _extract_data_point_value(inc, "basic_earnings_per_share")

                # ── Balance Sheet ─────────────────────────────────────────
                bal = getattr(fin, "balance_sheet", None) if fin else None
                row["assets"]              = _extract_data_point_value(bal, "assets")
                row["current_assets"]      = _extract_data_point_value(bal, "current_assets")
                row["current_liabilities"] = _extract_data_point_value(bal, "current_liabilities")
                row["inventory"]           = _extract_data_point_value(bal, "inventory")
                row["liabilities"]         = _extract_data_point_value(bal, "liabilities")
                row["long_term_debt"]      = _extract_data_point_value(bal, "noncurrent_liabilities")

                # ── Cash Flow Statement ───────────────────────────────────
                cf = getattr(fin, "cash_flow_statement", None) if fin else None
                row["net_cash_flow"]                 = _extract_data_point_value(cf, "net_cash_flow")
                row["net_cash_flow_from_operations"] = _extract_data_point_value(cf, "net_cash_flow_from_operating_activities")

                # ── Derived / Computed Metrics ────────────────────────────
                row["gross_profit_margin"] = (
                    row["gross_profit"] / row["revenues"]
                    if row["revenues"] and row["gross_profit"] and row["revenues"] != 0
                    else None
                )
                row["net_profit_margin"] = (
                    row["net_income_loss"] / row["revenues"]
                    if row["revenues"] and row["net_income_loss"] and row["revenues"] != 0
                    else None
                )
                row["inventory_turnover"] = (
                    row["cost_of_revenue"] / row["inventory"]
                    if row["cost_of_revenue"] and row["inventory"] and row["inventory"] != 0
                    else None
                )
                # DSO proxy: (current_assets − inventory) / (revenue / 90 days)
                if (
                    row["current_assets"] and row["inventory"]
                    and row["revenues"] and row["revenues"] != 0
                ):
                    liquid_ca = row["current_assets"] - (row["inventory"] or 0)
                    row["dso_days"] = liquid_ca / (row["revenues"] / 90)
                else:
                    row["dso_days"] = None

                row["current_ratio"] = (
                    row["current_assets"] / row["current_liabilities"]
                    if row["current_assets"] and row["current_liabilities"]
                    and row["current_liabilities"] != 0
                    else None
                )
                row["debt_to_assets"] = (
                    row["liabilities"] / row["assets"]
                    if row["liabilities"] and row["assets"] and row["assets"] != 0
                    else None
                )

                all_records.append(row)
                filing_count += 1

            logger.info("[Polygon] %s: %d quarterly filing(s).", ticker, filing_count)

        except AuthError:
            logger.error(
                "[Polygon] Authentication failed for %s. "
                "Check your POLYGON_API_KEY.", ticker,
            )
            break

        except BadResponse as exc:
            logger.warning("[Polygon] Bad API response for %s: %s. Continuing.", ticker, exc)

        except Exception as exc:
            if "429" in str(exc):
                logger.warning("[Polygon] Rate limit (429) hit for %s. Sleeping 60s to cool down...", ticker)
                time.sleep(60)
            else:
                logger.warning("[Polygon] Unexpected error for %s: %s. Continuing.", ticker, exc)

        finally:
            if idx < len(POLYGON_TICKERS):
                logger.info(
                    "[Polygon] Rate-limit pause: sleeping %d s after %s …",
                    POLYGON_RATE_LIMIT_SLEEP, ticker,
                )
                time.sleep(POLYGON_RATE_LIMIT_SLEEP)

    if not all_records:
        logger.warning("[Polygon] No records retrieved.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    for date_col in ("start_date", "end_date", "filing_date"):
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    logger.info(
        "[Polygon] Total: %d rows across %d ticker(s).",
        len(df), df["ticker"].nunique() if "ticker" in df.columns else "?",
    )
    write_dataframe(df, "raw_polygon", engine)
    return df


# =============================================================================
# ── Component 2: US Census Bureau — M3 Manufacturing Survey ──────────────────
# =============================================================================


def ingest_census(engine) -> pd.DataFrame:
    """
    Pull Manufacturers' Shipments, Inventories, and Orders (M3) data
    from the US Census Bureau's time-series API.

    Endpoint:
        https://api.census.gov/data/timeseries/eits/m3

    Key variables returned:
        cell_value      — Survey measurement value
        error_data      — Standard error / margin of error
        time_slot_date  — YYYY-MM reference period
        seasonally_adj  — "yes"/"no" seasonal adjustment flag
        category_code   — Industry/product category
        data_type_code  — VS / II / NO / IO / BO

    Args:
        engine: SQLAlchemy engine from :func:`db_utils.get_engine`.

    Returns:
        DataFrame of M3 survey records (also written to ``raw_census``).
    """
    api_key = os.getenv("CENSUS_API_KEY", "").strip()
    if not api_key:
        logger.error(
            "[Census] CENSUS_API_KEY is not set in .env. "
            "Skipping Census ingestion."
        )
        return pd.DataFrame()

    params: dict[str, str] = {
        "get":  CENSUS_M3_GET_VARS,
        "time": f"from {CENSUS_M3_START_YEAR}",
        "for":  "us:*",
        "key":  api_key,
    }

    logger.info(
        "[Census] Fetching M3 Manufacturing survey data (from %s) …",
        CENSUS_M3_START_YEAR,
    )

    try:
        resp = _http_get(CENSUS_M3_BASE_URL, params=params)
    except requests.HTTPError as exc:
        logger.error("[Census] HTTP error: %s", exc)
        return pd.DataFrame()
    except RuntimeError as exc:
        logger.error("[Census] All retries exhausted: %s", exc)
        return pd.DataFrame()

    try:
        payload: list[list[str]] = resp.json()
    except requests.JSONDecodeError as exc:
        logger.error("[Census] Failed to parse JSON: %s", exc)
        return pd.DataFrame()

    if not payload or len(payload) < 2:
        logger.warning("[Census] Response contained no data rows.")
        return pd.DataFrame()

    headers = payload[0]
    rows    = payload[1:]
    df = pd.DataFrame(rows, columns=headers)

    for numeric_col in ("cell_value", "error_data"):
        if numeric_col in df.columns:
            df[numeric_col] = pd.to_numeric(df[numeric_col], errors="coerce")

    if "time_slot_date" in df.columns:
        df["period_date"] = pd.to_datetime(
            df["time_slot_date"], format="%Y-%m", errors="coerce"
        )

    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda s: s.str.strip())

    df["ingested_at"] = pd.Timestamp.utcnow()

    logger.info("[Census] Retrieved %d rows of M3 survey data.", len(df))
    write_dataframe(df, "raw_census", engine)
    return df


# =============================================================================
# ── Component 3: OpenSky Network — Flight / Cargo Transit ────────────────────
# =============================================================================


def ingest_opensky(engine) -> pd.DataFrame:
    """
    Pull a snapshot of all current aircraft state vectors from the OpenSky
    Network REST API.

    Authentication:
        Anonymous access is permitted (leave OPENSKY_USERNAME blank).
        Authenticated users receive one extra field (aircraft category).

    Args:
        engine: SQLAlchemy engine from :func:`db_utils.get_engine`.

    Returns:
        DataFrame of aircraft state vectors (written to ``raw_opensky``).
    """
    username = os.getenv("OPENSKY_USERNAME", "").strip()
    password = os.getenv("OPENSKY_PASSWORD", "").strip()

    if username and password:
        auth: tuple[str, str] | None = (username, password)
        logger.info("[OpenSky] Using authenticated access as user '%s'.", username)
    else:
        auth = None
        logger.warning(
            "[OpenSky] Credentials not set — using anonymous access "
            "(10 s rate limit applies)."
        )

    logger.info("[OpenSky] Fetching aircraft state vectors …")

    try:
        resp = _http_get(OPENSKY_STATES_URL, auth=auth)
    except requests.HTTPError as exc:
        logger.error("[OpenSky] HTTP error: %s", exc)
        return pd.DataFrame()
    except RuntimeError as exc:
        logger.error("[OpenSky] All retries exhausted: %s", exc)
        return pd.DataFrame()

    try:
        data: dict = resp.json()
    except requests.JSONDecodeError as exc:
        logger.error("[OpenSky] Failed to parse JSON: %s", exc)
        return pd.DataFrame()

    states: list | None = data.get("states")
    if not states:
        logger.warning("[OpenSky] No aircraft states in response.")
        return pd.DataFrame()

    n_expected_cols = len(OPENSKY_STATE_COLUMNS)
    aligned_rows = [
        state[:n_expected_cols] + [None] * max(0, n_expected_cols - len(state))
        for state in states
    ]

    df = pd.DataFrame(aligned_rows, columns=OPENSKY_STATE_COLUMNS)

    float_cols = [
        "time_position", "last_contact",
        "longitude", "latitude",
        "baro_altitude", "geo_altitude",
        "velocity", "true_track", "vertical_rate",
    ]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ("on_ground", "spi"):
        if col in df.columns:
            df[col] = df[col].astype("boolean")

    if "callsign" in df.columns:
        df["callsign"] = df["callsign"].str.strip().replace("", None)

    df["request_timestamp_utc"] = pd.Timestamp.utcnow()
    df["api_request_time"]      = data.get("time")

    logger.info("[OpenSky] Retrieved %d aircraft state records.", len(df))
    write_dataframe(df, "raw_opensky", engine)
    return df


# =============================================================================
# ── Component 5: World Bank Open Data — Macro & Logistics Indicators ──────────
# =============================================================================


def ingest_worldbank(engine) -> pd.DataFrame:
    """
    Pull macroeconomic and logistics-performance indicators for a set of
    key trading nations from the World Bank Open Data API.

    No API key is required — the World Bank API is fully open.

    The API accepts a semicolon-separated list of ISO-2 country codes so we
    can fetch all 20 countries in a single request per indicator, keeping the
    total number of HTTP calls equal to len(WORLDBANK_INDICATORS).

    Data shape returned:
        One row per (indicator_code, country_code, year).
        The ``value`` column holds the numeric measurement; it may be None for
        years where the World Bank has not yet published data (e.g. LPI
        indicators are biennial).  The cleaning pipeline interpolates these
        gaps to produce a complete annual time series.

    Args:
        engine: SQLAlchemy engine from :func:`db_utils.get_engine`.

    Returns:
        Long-format DataFrame written to ``raw_worldbank``.
    """
    countries_param = ";".join(WORLDBANK_COUNTRIES)
    date_range      = f"{WORLDBANK_START_YEAR}:{WORLDBANK_END_YEAR}"
    all_records: list[dict] = []

    logger.info(
        "[WorldBank] Fetching %d indicator(s) for %d countries "
        "(years %s) …",
        len(WORLDBANK_INDICATORS), len(WORLDBANK_COUNTRIES), date_range,
    )

    for indicator_code, indicator_name in WORLDBANK_INDICATORS.items():
        url = WORLDBANK_BASE_URL.format(
            countries=countries_param,
            indicator=indicator_code,
        )
        params = {
            "format":   "json",
            "per_page": "5000",   # enough to collect all countries × years in one page
            "date":     date_range,
        }

        logger.info("[WorldBank] Fetching indicator: %s (%s) …", indicator_code, indicator_name)

        try:
            resp = _http_get(url, params=params)
        except (requests.HTTPError, RuntimeError) as exc:
            logger.warning(
                "[WorldBank] Failed for indicator %s: %s. Skipping.",
                indicator_code, exc,
            )
            time.sleep(WORLDBANK_INTER_CALL_SLEEP)
            continue

        try:
            payload = resp.json()
        except requests.JSONDecodeError as exc:
            logger.warning("[WorldBank] JSON parse error for %s: %s.", indicator_code, exc)
            time.sleep(WORLDBANK_INTER_CALL_SLEEP)
            continue

        # World Bank returns a two-element list: [metadata_dict, data_list]
        # An error (e.g. invalid indicator) looks like [{"message": [...]}]
        if not isinstance(payload, list) or len(payload) < 2:
            logger.warning(
                "[WorldBank] Unexpected response structure for %s: %s",
                indicator_code, str(payload)[:200],
            )
            time.sleep(WORLDBANK_INTER_CALL_SLEEP)
            continue

        metadata, records = payload[0], payload[1]

        # Detect API-level error messages
        if "message" in metadata:
            logger.warning(
                "[WorldBank] API error for indicator %s: %s",
                indicator_code,
                metadata["message"][0].get("value", "unknown") if metadata["message"] else "unknown",
            )
            time.sleep(WORLDBANK_INTER_CALL_SLEEP)
            continue

        if not records:
            logger.warning("[WorldBank] No data returned for indicator %s.", indicator_code)
            time.sleep(WORLDBANK_INTER_CALL_SLEEP)
            continue

        for rec in records:
            all_records.append({
                "indicator_code":  rec.get("indicator", {}).get("id"),
                "indicator_name":  indicator_name,
                "indicator_label": rec.get("indicator", {}).get("value"),
                "country_code":    rec.get("country",   {}).get("id"),
                "country_name":    rec.get("country",   {}).get("value"),
                "country_iso3":    rec.get("countryiso3code"),
                "date":            rec.get("date"),      # "YYYY" string
                "value":           rec.get("value"),     # numeric or None
                "unit":            rec.get("unit", ""),
                "obs_status":      rec.get("obs_status", ""),
            })

        logger.info(
            "[WorldBank] %s: %d record(s) retrieved.",
            indicator_code, len(records),
        )
        time.sleep(WORLDBANK_INTER_CALL_SLEEP)

    if not all_records:
        logger.warning("[WorldBank] No records retrieved from any indicator.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # Coerce types
    # "date" from World Bank is a 4-digit year string — convert to Jan-1 of that year
    df["date"]  = pd.to_datetime(df["date"].astype(str) + "-01-01", errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df["ingested_at"] = pd.Timestamp.utcnow()

    # Remove aggregate / region rows that the World Bank API sometimes includes
    # alongside country-level data (their country_code is 3+ chars, e.g. "WLD").
    before = len(df)
    df = df[df["country_code"].isin(WORLDBANK_COUNTRIES)].copy()
    dropped = before - len(df)
    if dropped:
        logger.info("[WorldBank] Dropped %d aggregate/region rows.", dropped)

    logger.info(
        "[WorldBank] Total: %d rows across %d indicator(s) and %d country(ies).",
        len(df),
        df["indicator_code"].nunique() if "indicator_code" in df.columns else "?",
        df["country_code"].nunique()   if "country_code"   in df.columns else "?",
    )
    write_dataframe(df, "raw_worldbank", engine)
    return df


# =============================================================================
# ── Component 6: FRED — Supply-Chain Economic Indicators ─────────────────────
# =============================================================================


def ingest_fred(engine) -> pd.DataFrame:
    """
    Pull monthly (and some daily) supply-chain-relevant economic time series
    from the Federal Reserve Bank of St. Louis (FRED) API.

    A free API key is required.  Obtain one instantly at:
        https://fred.stlouisfed.org/docs/api/api_key.html

    Missing values in FRED observations are encoded as the string ``"."``
    (a FRED convention).  These are coerced to NaN here; the cleaning pipeline
    interpolates them.

    Daily series (e.g. WTI crude oil) are resampled to month-end means so
    every series in ``raw_fred`` shares the same monthly frequency.

    Data shape:
        One row per (series_id, date).
        Columns: series_id, series_name, date, value, frequency, units.

    Args:
        engine: SQLAlchemy engine from :func:`db_utils.get_engine`.

    Returns:
        Long-format DataFrame written to ``raw_fred``.
    """
    api_key = os.getenv("FRED_API_KEY", "").strip()
    if not api_key:
        logger.error(
            "[FRED] FRED_API_KEY is not set in .env. Skipping FRED ingestion.\n"
            "  Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html"
        )
        return pd.DataFrame()

    all_records: list[dict] = []

    logger.info(
        "[FRED] Fetching %d series from %s …",
        len(FRED_SERIES), FRED_OBSERVATION_START,
    )

    for series_id, series_name in FRED_SERIES.items():
        params = {
            "series_id":         series_id,
            "api_key":           api_key,
            "file_type":         "json",
            "observation_start": FRED_OBSERVATION_START,
            "sort_order":        "asc",
            "output_type":       "1",   # observations by date
        }

        logger.info("[FRED] Fetching series: %s (%s) …", series_id, series_name)

        try:
            resp = _http_get(FRED_BASE_URL, params=params)
        except (requests.HTTPError, RuntimeError) as exc:
            logger.warning("[FRED] Failed for series %s: %s. Skipping.", series_id, exc)
            time.sleep(FRED_INTER_CALL_SLEEP)
            continue

        try:
            data: dict = resp.json()
        except requests.JSONDecodeError as exc:
            logger.warning("[FRED] JSON parse error for %s: %s.", series_id, exc)
            time.sleep(FRED_INTER_CALL_SLEEP)
            continue

        # FRED wraps results and metadata together
        if "error_code" in data:
            logger.warning(
                "[FRED] API error for series %s: %s",
                series_id, data.get("error_message", "unknown"),
            )
            time.sleep(FRED_INTER_CALL_SLEEP)
            continue

        observations: list = data.get("observations", [])
        if not observations:
            logger.warning("[FRED] No observations returned for series %s.", series_id)
            time.sleep(FRED_INTER_CALL_SLEEP)
            continue

        frequency = data.get("frequency_short", "")
        units     = data.get("units",           "")

        raw_rows = []
        for obs in observations:
            raw_val = obs.get("value", ".")
            # FRED uses "." as the missing-value sentinel
            value = None if raw_val == "." else raw_val
            raw_rows.append({
                "series_id":   series_id,
                "series_name": series_name,
                "date":        obs["date"],
                "value":       value,
                "frequency":   frequency,
                "units":       units,
            })

        # ── Resample daily series to monthly mean ─────────────────────────
        # Daily series like DCOILWTICO would otherwise dwarf monthly series
        # in row count and create alignment headaches in the cleaning step.
        if frequency in ("D", "BD"):
            temp_df = pd.DataFrame(raw_rows)
            temp_df["date"]  = pd.to_datetime(temp_df["date"])
            temp_df["value"] = pd.to_numeric(temp_df["value"], errors="coerce")
            # Resample to month-end, compute mean; keep metadata columns
            temp_df = (
                temp_df
                .set_index("date")
                .resample("ME")[["value"]]
                .mean()
                .reset_index()
            )
            temp_df["series_id"]   = series_id
            temp_df["series_name"] = series_name
            temp_df["frequency"]   = "M"    # re-label as monthly after resampling
            temp_df["units"]       = units
            raw_rows = temp_df.to_dict("records")
            logger.info(
                "[FRED] %s: daily series resampled to %d monthly rows.",
                series_id, len(raw_rows),
            )
        else:
            logger.info("[FRED] %s: %d observation(s).", series_id, len(raw_rows))

        all_records.extend(raw_rows)
        time.sleep(FRED_INTER_CALL_SLEEP)

    if not all_records:
        logger.warning("[FRED] No records retrieved.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    df["date"]  = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df["ingested_at"] = pd.Timestamp.utcnow()

    logger.info(
        "[FRED] Total: %d rows across %d series.",
        len(df),
        df["series_id"].nunique() if "series_id" in df.columns else "?",
    )
    write_dataframe(df, "raw_fred", engine)
    return df


# =============================================================================
# ── Orchestration entry point ─────────────────────────────────────────────────
# =============================================================================


def main() -> None:
    """
    Run all six API ingestion tasks sequentially.

    Each task is independent — a failure in one does not abort the others.
    The final log line reports which tables were successfully written.
    """
    separator = "=" * 65

    logger.info(separator)
    logger.info("Supply Chain Pipeline — API Ingestion Starting")
    logger.info(separator)

    engine = get_engine()
    if not test_connection(engine):
        logger.critical(
            "Cannot reach the PostgreSQL database. "
            "Is docker compose up? Are the .env credentials correct? Exiting."
        )
        return

    results: dict[str, str] = {}

    # ── Task 1: Polygon.io ────────────────────────────────────────────────────
    logger.info("\n%s", "-" * 65)
    logger.info("[1/5] Polygon.io — Quarterly Financial Filings")
    logger.info("-" * 65)
    try:
        df_polygon = ingest_polygon(engine)
        results["raw_polygon"] = f"{len(df_polygon)} rows" if not df_polygon.empty else "EMPTY"
    except Exception as exc:
        logger.error("[Polygon] Fatal error: %s", exc, exc_info=True)
        results["raw_polygon"] = "ERROR"

    # ── Task 2: US Census Bureau ──────────────────────────────────────────────
    logger.info("\n%s", "-" * 65)
    logger.info("[2/5] US Census Bureau — M3 Manufacturing Survey")
    logger.info("-" * 65)
    try:
        df_census = ingest_census(engine)
        results["raw_census"] = f"{len(df_census)} rows" if not df_census.empty else "EMPTY"
    except Exception as exc:
        logger.error("[Census] Fatal error: %s", exc, exc_info=True)
        results["raw_census"] = "ERROR"

    # ── Task 3: OpenSky Network ───────────────────────────────────────────────
    logger.info("\n%s", "-" * 65)
    logger.info("[3/5] OpenSky Network — Aircraft State Vectors")
    logger.info("-" * 65)
    try:
        df_opensky = ingest_opensky(engine)
        results["raw_opensky"] = f"{len(df_opensky)} rows" if not df_opensky.empty else "EMPTY"
    except Exception as exc:
        logger.error("[OpenSky] Fatal error: %s", exc, exc_info=True)
        results["raw_opensky"] = "ERROR"

    # ── Task 4: World Bank Open Data ──────────────────────────────────────────
    logger.info("\n%s", "-" * 65)
    logger.info("[4/5] World Bank — Macro & Logistics Performance Indicators")
    logger.info("-" * 65)
    try:
        df_worldbank = ingest_worldbank(engine)
        results["raw_worldbank"] = f"{len(df_worldbank)} rows" if not df_worldbank.empty else "EMPTY"
    except Exception as exc:
        logger.error("[WorldBank] Fatal error: %s", exc, exc_info=True)
        results["raw_worldbank"] = "ERROR"

    # ── Task 5: FRED ──────────────────────────────────────────────────────────
    logger.info("\n%s", "-" * 65)
    logger.info("[5/5] FRED — Supply-Chain Economic Time Series")
    logger.info("-" * 65)
    try:
        df_fred = ingest_fred(engine)
        results["raw_fred"] = f"{len(df_fred)} rows" if not df_fred.empty else "EMPTY"
    except Exception as exc:
        logger.error("[FRED] Fatal error: %s", exc, exc_info=True)
        results["raw_fred"] = "ERROR"

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("\n%s", separator)
    logger.info("API Ingestion Complete — Table Summary:")
    for table, status in results.items():
        logger.info("  %-25s %s", table, status)
    logger.info(separator)


if __name__ == "__main__":
    main()
