import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from api_utils import _http_get
from db_utils import get_engine, test_connection, write_dataframe

_ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=False)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

FRED_BASE_URL: str = "https://api.stlouisfed.org/fred/series/observations"
FRED_INTER_CALL_SLEEP: float = 0.5
FRED_OBSERVATION_START: str = "2015-01-01"

FRED_SERIES: dict[str, str] = {
    "PCU3344133441":   "Semiconductor & Related Device Mfg PPI",
    "PCU336110336110": "Automobile Mfg PPI",
    "WPU10":           "Metals and Metal Products PPI",
    "DCOILWTICO":      "Crude Oil Prices: WTI (Daily)",
    "CES3000000001":   "All Employees: Manufacturing",
    "PCU4841248412":   "General Freight Trucking PPI",
}


def ingest_fred(engine) -> pd.DataFrame:
    api_key = os.getenv("FRED_API_KEY", "").strip()
    if not api_key:
        logger.error("[FRED] FRED_API_KEY is not set. Exiting.")
        sys.exit(1)

    all_records: list[dict] = []
    logger.info("[FRED] Fetching %d series from %s …", len(FRED_SERIES), FRED_OBSERVATION_START)

    for series_id, series_name in FRED_SERIES.items():
        params = {
            "series_id":         series_id,
            "api_key":           api_key,
            "file_type":         "json",
            "observation_start": FRED_OBSERVATION_START,
            "sort_order":        "asc",
            "output_type":       "1",
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

        if "error_code" in data:
            logger.warning("[FRED] API error for series %s: %s", series_id, data.get("error_message", "unknown"))
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
            value = None if raw_val == "." else raw_val
            raw_rows.append({
                "series_id":   series_id,
                "series_name": series_name,
                "date":        obs["date"],
                "value":       value,
                "frequency":   frequency,
                "units":       units,
            })

        if frequency in ("D", "BD"):
            temp_df = pd.DataFrame(raw_rows)
            temp_df["date"]  = pd.to_datetime(temp_df["date"])
            temp_df["value"] = pd.to_numeric(temp_df["value"], errors="coerce")
            temp_df = temp_df.set_index("date").resample("ME")[["value"]].mean().reset_index()
            temp_df["series_id"]   = series_id
            temp_df["series_name"] = series_name
            temp_df["frequency"]   = "M"
            temp_df["units"]       = units
            raw_rows = temp_df.to_dict("records")
            logger.info("[FRED] %s: daily series resampled to %d monthly rows.", series_id, len(raw_rows))
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

    logger.info("[FRED] Total: %d rows across %d series.", len(df), df["series_id"].nunique() if "series_id" in df.columns else "?")
    write_dataframe(df, "raw_fred", engine)
    return df


def main():
    engine = get_engine()
    if not test_connection(engine):
        logger.critical("Cannot reach PostgreSQL database. Exiting.")
        sys.exit(1)

    ingest_fred(engine)


if __name__ == "__main__":
    main()
