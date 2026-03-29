import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from polygon import RESTClient as PolygonRESTClient
from polygon.exceptions import AuthError, BadResponse

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

POLYGON_RATE_LIMIT_SLEEP: int = 12
POLYGON_QUARTERLY_LIMIT: int = 100


def _extract_data_point_value(obj: Any, attr: str) -> float | None:
    data_point = getattr(obj, attr, None)
    if data_point is None:
        return None
    return getattr(data_point, "value", None)


def ingest_polygon(engine, tickers: list[str]) -> pd.DataFrame:
    api_key = os.getenv("POLYGON_API_KEY", "").strip()
    if not api_key:
        logger.error("[Polygon] POLYGON_API_KEY is not set. Exiting.")
        sys.exit(1)

    try:
        client = PolygonRESTClient(api_key)
    except Exception as exc:
        logger.error("[Polygon] Failed to create Polygon client: %s", exc)
        sys.exit(1)

    all_records: list[dict] = []

    for idx, ticker in enumerate(tickers, start=1):
        logger.info("[Polygon] (%d/%d) Fetching quarterly financials for %s …", idx, len(tickers), ticker)
        try:
            filings = client.vx.list_stock_financials(
                ticker=ticker,
                timeframe="quarterly",
                limit=POLYGON_QUARTERLY_LIMIT,
                include_sources=False,
            )

            filing_count = 0
            for report in filings:
                row = {
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
                inc = getattr(fin, "income_statement", None) if fin else None
                row["revenues"]              = _extract_data_point_value(inc, "revenues")
                row["gross_profit"]          = _extract_data_point_value(inc, "gross_profit")
                row["net_income_loss"]       = _extract_data_point_value(inc, "net_income_loss")
                row["operating_income_loss"] = _extract_data_point_value(inc, "operating_income_loss")
                row["cost_of_revenue"]       = _extract_data_point_value(inc, "cost_of_revenue")
                row["basic_eps"]             = _extract_data_point_value(inc, "basic_earnings_per_share")

                bal = getattr(fin, "balance_sheet", None) if fin else None
                row["assets"]              = _extract_data_point_value(bal, "assets")
                row["current_assets"]      = _extract_data_point_value(bal, "current_assets")
                row["current_liabilities"] = _extract_data_point_value(bal, "current_liabilities")
                row["inventory"]           = _extract_data_point_value(bal, "inventory")
                row["liabilities"]         = _extract_data_point_value(bal, "liabilities")
                row["long_term_debt"]      = _extract_data_point_value(bal, "noncurrent_liabilities")

                cf = getattr(fin, "cash_flow_statement", None) if fin else None
                row["net_cash_flow"]                 = _extract_data_point_value(cf, "net_cash_flow")
                row["net_cash_flow_from_operations"] = _extract_data_point_value(cf, "net_cash_flow_from_operating_activities")

                row["gross_profit_margin"] = (row["gross_profit"] / row["revenues"]) if row["revenues"] and row["gross_profit"] and row["revenues"] != 0 else None
                row["net_profit_margin"] = (row["net_income_loss"] / row["revenues"]) if row["revenues"] and row["net_income_loss"] and row["revenues"] != 0 else None
                row["inventory_turnover"] = (row["cost_of_revenue"] / row["inventory"]) if row["cost_of_revenue"] and row["inventory"] and row["inventory"] != 0 else None
                
                if row["current_assets"] and row["inventory"] and row["revenues"] and row["revenues"] != 0:
                    liquid_ca = row["current_assets"] - (row["inventory"] or 0)
                    row["dso_days"] = liquid_ca / (row["revenues"] / 90)
                else:
                    row["dso_days"] = None

                row["current_ratio"] = (row["current_assets"] / row["current_liabilities"]) if row["current_assets"] and row["current_liabilities"] and row["current_liabilities"] != 0 else None
                row["debt_to_assets"] = (row["liabilities"] / row["assets"]) if row["liabilities"] and row["assets"] and row["assets"] != 0 else None

                all_records.append(row)
                filing_count += 1

            logger.info("[Polygon] %s: %d quarterly filing(s).", ticker, filing_count)

        except AuthError:
            logger.error("[Polygon] Authentication failed for %s. Check your POLYGON_API_KEY.", ticker)
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
            if idx < len(tickers):
                logger.info("[Polygon] Rate-limit pause: sleeping %d s after %s …", POLYGON_RATE_LIMIT_SLEEP, ticker)
                time.sleep(POLYGON_RATE_LIMIT_SLEEP)

    if not all_records:
        logger.warning("[Polygon] No records retrieved.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    for date_col in ("start_date", "end_date", "filing_date"):
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    logger.info("[Polygon] Total: %d rows across %d ticker(s).", len(df), df["ticker"].nunique() if "ticker" in df.columns else "?")
    write_dataframe(df, "raw_polygon", engine)
    return df


def main():
    parser = argparse.ArgumentParser(description="Ingest Polygon.io Financials")
    parser.add_argument("tickers", nargs="+", help="One or more stock tickers to ingest (e.g. AAPL MSFT)")
    args = parser.parse_args()

    engine = get_engine()
    if not test_connection(engine):
        logger.critical("Cannot reach PostgreSQL database. Exiting.")
        sys.exit(1)

    ingest_polygon(engine, args.tickers)


if __name__ == "__main__":
    main()
