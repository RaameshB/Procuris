import argparse
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

COMTRADE_API_URL: str = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
COMTRADE_INTER_CALL_SLEEP: float = 2.0


def ingest_comtrade(engine, reporters: str, partners: str, cmd_codes: str, years: str) -> pd.DataFrame:
    api_key = os.getenv("COMTRADE_API_KEY", "").strip()
    if not api_key:
        logger.error("[Comtrade] COMTRADE_API_KEY is not set. Exiting.")
        sys.exit(1)

    headers = {"Ocp-Apim-Subscription-Key": api_key}
    all_records: list[dict] = []

    # API docs recommend pulling years individually or 2 at a time if data limits trigger
    # But for targeted HS codes, multiple years should be fine. We will split just in case.
    year_list = [y.strip() for y in years.split(",") if y.strip()]
    
    for year in year_list:
        logger.info("[Comtrade] Fetching HS codes %s for year %s …", cmd_codes, year)
        params = {
            "reporterCode": reporters,
            "partnerCode": partners,
            "cmdCode": cmd_codes,
            "period": year,
            "flowCode": "M,X", # Imports and Exports
            "format": "JSON"
        }

        try:
            resp = _http_get(COMTRADE_API_URL, params=params, headers=headers)
        except (requests.HTTPError, RuntimeError) as exc:
            logger.error("[Comtrade] Failed fetching data for year %s: %s", year, exc)
            continue

        try:
            data = resp.json()
        except requests.JSONDecodeError as exc:
            logger.error("[Comtrade] JSON parse error: %s", exc)
            continue

        dataset = data.get("data", [])
        if not dataset:
            logger.info("[Comtrade] No data returned for year %s.", year)
            time.sleep(COMTRADE_INTER_CALL_SLEEP)
            continue

        for rec in dataset:
            all_records.append({
                "reporter":       rec.get("reporterDesc", ""),
                "reporter_code":  rec.get("reporterCode"),
                "partner":        rec.get("partnerDesc", ""),
                "partner_code":   rec.get("partnerCode"),
                "commodity_code": rec.get("cmdCode", ""),
                "commodity_desc": rec.get("cmdDesc", ""),
                "flow_code":      rec.get("flowCode", ""),
                "trade_value_usd":rec.get("primaryValue"),
                "netweight_kg":   rec.get("netWgt"),
                "qty":            rec.get("qty"),
                "qty_unit":       rec.get("qtyUnitDesc"),
                "ref_year":       rec.get("period"), 
            })

        logger.info("[Comtrade] Fetched %d records for year %s.", len(dataset), year)
        time.sleep(COMTRADE_INTER_CALL_SLEEP)

    if not all_records:
        logger.warning("[Comtrade] No records retrieved across all specified years.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    df["trade_value_usd"] = pd.to_numeric(df["trade_value_usd"], errors="coerce")
    df["netweight_kg"]    = pd.to_numeric(df["netweight_kg"], errors="coerce")
    df["qty"]             = pd.to_numeric(df["qty"], errors="coerce")
    df["ingested_at"]     = pd.Timestamp.utcnow()

    logger.info("[Comtrade] Total: %d rows.", len(df))
    write_dataframe(df, "raw_comtrade", engine)
    return df


def main():
    parser = argparse.ArgumentParser(description="Ingest UN Comtrade Data via API v1")
    parser.add_argument("--reporters", default="842,156,276,392", help="Comma-sep reporter codes (default: US, CN, DE, JP)")
    parser.add_argument("--partners", default="0", help="Comma-sep partner codes (default: 0 for World)")
    parser.add_argument("--cmd-codes", default="8542,8708", help="Comma-sep HS codes (default: Semiconductors 8542, Auto Parts 8708)")
    parser.add_argument("--years", default="2020,2021,2022,2023", help="Comma-sep years")
    
    args = parser.parse_args()

    engine = get_engine()
    if not test_connection(engine):
        logger.critical("Cannot reach PostgreSQL database. Exiting.")
        sys.exit(1)

    ingest_comtrade(engine, args.reporters, args.partners, args.cmd_codes, args.years)


if __name__ == "__main__":
    main()
