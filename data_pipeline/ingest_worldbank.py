import logging
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

WORLDBANK_BASE_URL: str = "http://api.worldbank.org/v2/country/all/indicator"
WORLDBANK_INTER_CALL_SLEEP: float = 1.0

WORLDBANK_COUNTRIES: set[str] = {
    "USA", "CHN", "DEU", "JPN", "IND", "GBR", "FRA", "BRA", "ITA", "CAN",
    "MEX", "KOR", "AUS", "ESP", "IDN", "VNM", "THA", "MYS", "SGP", "TWN"
}

WORLDBANK_INDICATORS: dict[str, str] = {
    "NY.GDP.MKTP.CD":   "gdp_current_usd",
    "NE.TRD.GNFS.ZS":   "trade_pct_gdp",
    "LP.LPI.OVRL.XQ":   "logistics_performance_index", # LPI overal score
    "TX.VAL.TECH.MF.ZS":"high_tech_exports_pct",
    "IS.SHP.GCON.VW":   "container_port_traffic_teu",
    "IS.AIR.GOOD.MT.K1":"air_freight_million_ton_km",
    "TM.TAX.MANF.SM.AR.ZS": "tariff_rate_mfg_pct",
    "IQ.CPA.TRAD.XQ":   "cpa_trade_rating",
    "IC.EXP.CSBC.CD":   "cost_to_export_border_compliance_usd",
    "IC.IMP.CSBC.CD":   "cost_to_import_border_compliance_usd",
    "IE.PPI.ENGY.CD":   "ppi_energy_investment_usd",
    "SL.TLF.TOTL.IN":   "labour_force_total",
    "NV.IND.MANF.ZS":   "manufacturing_pct_gdp",
}

def ingest_worldbank(engine) -> pd.DataFrame:
    all_records = []
    logger.info("[WorldBank] Fetching %d macroeconomic indicators …", len(WORLDBANK_INDICATORS))

    for indicator_code, alias in WORLDBANK_INDICATORS.items():
        logger.info("[WorldBank] Fetching indicator: %s (%s) …", indicator_code, alias)

        params = {
            "format": "json",
            "per_page": 1000, 
            "page": 1,
        }

        while True:
            url = f"{WORLDBANK_BASE_URL}/{indicator_code}"
            try:
                resp = _http_get(url, params=params)
            except (requests.HTTPError, RuntimeError) as exc:
                logger.error("[WorldBank] Failed fetching page %d for %s: %s", params["page"], indicator_code, exc)
                break

            try:
                data = resp.json()
            except requests.JSONDecodeError as exc:
                logger.error("[WorldBank] JSON parse error: %s", exc)
                break

            if len(data) < 2:
                logger.warning("[WorldBank] Unexpected response structure for %s.", indicator_code)
                break

            metadata = data[0]
            records = data[1]

            if not records:
                break

            for rec in records:
                all_records.append({
                    "indicator_code":  indicator_code,
                    "indicator_alias": alias,
                    "country_code":    rec.get("countryiso3code", ""),
                    "country_name":    (rec.get("country") or {}).get("value", ""),
                    "date":            rec.get("date", ""),
                    "value":           rec.get("value", None),
                    "unit":            rec.get("unit", ""),
                    "obs_status":      rec.get("obs_status", ""),
                })

            if params["page"] >= metadata.get("pages", 1):
                break

            params["page"] += 1
            time.sleep(WORLDBANK_INTER_CALL_SLEEP)
            
        logger.info("[WorldBank] %s: Fetched.", indicator_code)
        time.sleep(WORLDBANK_INTER_CALL_SLEEP)

    if not all_records:
        logger.warning("[WorldBank] No records retrieved.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    df["date"]  = pd.to_datetime(df["date"].astype(str) + "-01-01", errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["ingested_at"] = pd.Timestamp.utcnow()

    before = len(df)
    df = df[df["country_code"].isin(WORLDBANK_COUNTRIES)].copy()
    dropped = before - len(df)
    if dropped:
        logger.info("[WorldBank] Dropped %d aggregate/region rows.", dropped)

    logger.info("[WorldBank] Total: %d rows.", len(df))
    write_dataframe(df, "raw_worldbank", engine)
    return df


def main():
    engine = get_engine()
    if not test_connection(engine):
        logger.critical("Cannot reach PostgreSQL database. Exiting.")
        sys.exit(1)

    ingest_worldbank(engine)


if __name__ == "__main__":
    main()
