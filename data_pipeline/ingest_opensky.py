import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
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


OPENSKY_BASE_URL: str = "https://opensky-network.org/api"

def ingest_opensky(engine) -> pd.DataFrame:
    username = os.getenv("OPENSKY_USERNAME", "").strip()
    password = os.getenv("OPENSKY_PASSWORD", "").strip()
    
    auth = (username, password) if (username and password) else None
    if auth:
        logger.info("[OpenSky] Credentials found. Using authenticated access.")
    else:
        logger.info("[OpenSky] No credentials found in .env. Falling back to anonymous access.")

    url = f"{OPENSKY_BASE_URL}/states/all"
    logger.info("[OpenSky] Fetching current aircraft states globally …")

    try:
        resp = _http_get(url, auth=auth)
    except requests.HTTPError as exc:
        logger.error("[OpenSky] HTTP error: %s", exc)
        sys.exit(1)
    except RuntimeError as exc:
        logger.error("[OpenSky] All retries exhausted: %s", exc)
        sys.exit(1)

    try:
        data = resp.json()
    except requests.JSONDecodeError as exc:
        logger.error("[OpenSky] Failed to parse JSON: %s", exc)
        sys.exit(1)

    states = data.get("states", [])
    if not states:
        logger.warning("[OpenSky] Response contained no state vectors. (Possible rate limit or empty sky?)")
        return pd.DataFrame()

    columns = [
        "icao24", "callsign", "origin_country", "time_position",
        "last_contact", "longitude", "latitude", "baro_altitude",
        "on_ground", "velocity", "true_track", "vertical_rate",
        "sensors", "geo_altitude", "squawk", "spi", "position_source"
    ]
    if auth:
        columns.append("category")

    rows = []
    for s in states:
        if len(s) < len(columns):
            row = s + ([None] * (len(columns) - len(s)))
        else:
            row = s[:len(columns)]
        rows.append(row)

    df = pd.DataFrame(rows, columns=columns)

    if "callsign" in df.columns:
        df["callsign"] = df["callsign"].str.strip()

    for ts_col in ("time_position", "last_contact"):
        if ts_col in df.columns:
            df[ts_col] = pd.to_datetime(df[ts_col], unit="s", errors="coerce", utc=True)

    df["ingested_at"] = pd.Timestamp.utcnow()

    logger.info("[OpenSky] Retrieved %d state vectors.", len(df))
    write_dataframe(df, "raw_opensky", engine)
    return df


def main():
    engine = get_engine()
    if not test_connection(engine):
        logger.critical("Cannot reach PostgreSQL database. Exiting.")
        sys.exit(1)

    ingest_opensky(engine)


if __name__ == "__main__":
    main()
