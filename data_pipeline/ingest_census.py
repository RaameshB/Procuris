import logging
import os
import sys
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from api_utils import _http_get
from db_utils import get_engine, test_connection, write_dataframe

_ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CENSUS_M3_BASE_URL: str = "https://api.census.gov/data/timeseries/eits/m3"
CENSUS_M3_GET_VARS: str = (
    "cell_value,"       
    "error_data,"       
    "time_slot_date,"   
    "seasonally_adj,"   
    "category_code,"    
    "data_type_code,"   
    "time_slot_id"      
)
CENSUS_M3_START_YEAR: str = "2010"


def ingest_census(engine) -> pd.DataFrame:
    api_key = os.getenv("CENSUS_API_KEY", "").strip()
    if not api_key:
        logger.error("[Census] CENSUS_API_KEY is not set. Exiting.")
        sys.exit(1)

    params: dict[str, str] = {
        "get":  CENSUS_M3_GET_VARS,
        "time": f"from {CENSUS_M3_START_YEAR}",
        "for":  "us:*",
        "key":  api_key,
    }

    logger.info("[Census] Fetching M3 Manufacturing survey data (from %s) …", CENSUS_M3_START_YEAR)

    try:
        resp = _http_get(CENSUS_M3_BASE_URL, params=params)
    except requests.HTTPError as exc:
        logger.error("[Census] HTTP error: %s", exc)
        sys.exit(1)
    except RuntimeError as exc:
        logger.error("[Census] All retries exhausted: %s", exc)
        sys.exit(1)

    try:
        payload = resp.json()
    except requests.JSONDecodeError as exc:
        logger.error("[Census] Failed to parse JSON: %s", exc)
        sys.exit(1)

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
        df["period_date"] = pd.to_datetime(df["time_slot_date"], format="%Y-%m", errors="coerce")

    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda s: s.str.strip())
    df["ingested_at"] = pd.Timestamp.utcnow()

    logger.info("[Census] Retrieved %d rows of M3 survey data.", len(df))
    write_dataframe(df, "raw_census", engine)
    return df


def main():
    engine = get_engine()
    if not test_connection(engine):
        logger.critical("Cannot reach PostgreSQL database. Exiting.")
        sys.exit(1)

    ingest_census(engine)


if __name__ == "__main__":
    main()
