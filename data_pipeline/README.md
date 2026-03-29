# Supply Chain Data Pipeline

A modular, production-quality data ingestion and cleaning pipeline for supply-chain intelligence. Pulls raw data from multiple external APIs, loads manual CSV exports, and produces clean, analysis-ready tables in PostgreSQL — with no paid services, no ML modelling, and no forecasting logic.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Directory Structure](#directory-structure)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Environment Setup](#environment-setup)
6. [Database Setup](#database-setup)
7. [Running the Pipeline](#running-the-pipeline)
8. [Component Reference](#component-reference)
9. [Database Tables](#database-tables)
10. [Cleaning Rules](#cleaning-rules)
11. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                 │
│                                                                     │
│  Polygon.io API   Census Bureau   OpenSky Network   OS Hub API      │
│       │                │                │               │           │
│       └────────────────┴────────────────┴───────────────┘           │
│                              │                                      │
│           ingest_polygon.py / ingest_census.py              │
│  ingest_opensky.py / ingest_worldbank.py / ingest_fred.py   │
│                        ingest_comtrade.py                           │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                    ┌───────▼───────┐
                    │  PostgreSQL   │  raw_polygon, raw_census,
                    │  (Docker /    │  raw_opensky, raw_oshub,
                                                       raw_worldbank, raw_fred,
                                                       raw_worldbank, raw_fred,
                    │   Podman)     │  raw_comtrade
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  clean_data   │  Column pruning (>15% null → drop)
                    │     .py       │  Median imputation + was_null flags
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  PostgreSQL   │  processed_polygon, processed_census,
                    │  (Docker /    │  processed_opensky, processed_oshub,
                    │   Podman)     │  processed_comtrade
                    └───────────────┘
```

---

## Directory Structure

```
data_pipeline/
├── docker-compose.yml      # PostgreSQL 15 container definition
├── .env.example            # Template — copy to .env and fill in credentials
├── .env                    # Your local credentials (NEVER commit this)
├── db_utils.py             # SQLAlchemy engine, read/write helpers
├── ingest_api.py           # (Legacy) Monolithic API ingestion script
├── ingest_polygon.py       # Polygon.io parameterized ingestion
├── ingest_census.py        # US Census Bureau M3 ingestion
├── ingest_opensky.py       # OpenSky Network ingestion
├── ingest_worldbank.py     # World Bank macro indicators
├── ingest_fred.py          # FRED economic series
├── ingest_comtrade.py      # UN Comtrade API v1 ingestion
├── clean_data.py           # Null filtering, median imputation, indicator columns
├── test_db.py              # Database smoke test (run after docker compose up)
├── raw_csvs/               # Place manually downloaded Comtrade CSV files here
│   └── .gitkeep
└── README.md               # This file
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) or [Podman](https://podman.io/) | Docker ≥ 24 / Podman ≥ 4 | PostgreSQL container |
| [uv](https://docs.astral.sh/uv/) | ≥ 0.4 | Python dependency management |
| Python | 3.13 (managed by uv) | Runtime |

> **Podman users (Fedora / RHEL):** Use `podman compose` everywhere you see
> `docker compose`. The `docker-compose.yml` uses a fully-qualified image name
> (`docker.io/library/postgres:15-alpine`) so short-name resolution never
> blocks the pull.

---

## Installation

All commands are run from the **repository root** (`YHack/`).

### 1. Install Python dependencies

```bash
uv add pandas polygon-api-client requests pydantic python-dotenv sqlalchemy psycopg2-binary
```

This adds the packages to `pyproject.toml` and installs them into the existing
`.venv` at the repo root. Do **not** create a new virtual environment.

---

## Environment Setup

### 1. Copy the example file

```bash
cd data_pipeline
cp .env.example .env
```

### 2. Fill in your credentials

Open `data_pipeline/.env` in your editor and fill in every value:

```ini
# PostgreSQL — must match docker-compose.yml
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=admin
POSTGRES_PASSWORD=hackathonpassword
POSTGRES_DB=supplychain_db

# Polygon.io  →  https://polygon.io/  (free tier, instant signup)
POLYGON_API_KEY=your_key_here

# US Census Bureau  →  https://api.census.gov/data/key_signup.html  (free, emailed instantly)
CENSUS_API_KEY=your_key_here

# OpenSky Network  →  https://opensky-network.org/  (leave blank for anonymous access)
OPENSKY_USERNAME=your_username
OPENSKY_PASSWORD=your_password

# Open Supply Hub  →  https://opensupplyhub.org/  (free account, token in Profile → API)
OSHUB_API_KEY=your_token_here
```

> **Security:** `.env` is listed in `.gitignore` and must **never** be
> committed to version control. It contains real credentials.

---

## Database Setup

### 1. Start the PostgreSQL container

Run from the repository root, pointing at the compose file inside `data_pipeline/`:

```bash
# Docker
docker compose -f data_pipeline/docker-compose.yml up -d

# Podman
podman compose -f data_pipeline/docker-compose.yml up -d
```

Docker / Podman will pull `postgres:15-alpine` on the first run (≈ 60 MB) and
start the container in the background.

### 2. Verify the container is healthy

```bash
# Docker
docker compose -f data_pipeline/docker-compose.yml ps

# Podman
podman compose -f data_pipeline/docker-compose.yml ps
```

You should see `supply_chain_postgres` with status `Up` (the health check runs
`pg_isready` every 10 seconds — allow ≈ 15 s on first boot).

### 3. Run the database smoke test

```bash
uv run python data_pipeline/test_db.py
```

Expected output: `Results: 17/17 passed — all green ✅`

If any test fails, see [Troubleshooting](#troubleshooting).

### 4. Stop the container when done

```bash
# Keep data volume (normal stop)
docker compose -f data_pipeline/docker-compose.yml down        # Docker
podman compose -f data_pipeline/docker-compose.yml down        # Podman

# Wipe data volume too (clean slate)
docker compose -f data_pipeline/docker-compose.yml down -v     # Docker
podman compose -f data_pipeline/docker-compose.yml down -v     # Podman
```

---

## Running the Pipeline

All scripts are run from the **repository root** with
`uv run python data_pipeline/<script>.py`.

### Recommended execution order

```
1.  docker/podman compose … up -d             start PostgreSQL
2.  uv run python data_pipeline/test_db.py    verify DB is reachable
3.  uv run python data_pipeline/ingest_polygon.py AAPL MSFT ...
4.  uv run python data_pipeline/ingest_census.py
5.  uv run python data_pipeline/ingest_opensky.py
6.  uv run python data_pipeline/ingest_worldbank.py
7.  uv run python data_pipeline/ingest_fred.py
8.  uv run python data_pipeline/ingest_comtrade.py  → raw_comtrade
9.  uv run python data_pipeline/clean_data.py raw_* → processed_*
```

Steps 3 and 4 are independent and can be run in any order or re-run
individually. Step 5 reads whatever raw tables already exist and skips any
that are missing, so partial ingestion runs are safe.

### Individual commands

```bash
# From the repository root (YHack/)

# API ingestion (run individually)
uv run python data_pipeline/ingest_polygon.py AAPL MSFT AMZN TSLA WMT TGT FDX UPS HON CAT XOM BA
uv run python data_pipeline/ingest_census.py
uv run python data_pipeline/ingest_opensky.py
uv run python data_pipeline/ingest_worldbank.py
uv run python data_pipeline/ingest_fred.py

uv run python data_pipeline/ingest_comtrade.py --reporters 842,156,276,392 --partners 0 --cmd-codes 8542,8708 --years 2022,2023

# Data cleaning
uv run python data_pipeline/clean_data.py

# Database smoke test
uv run python data_pipeline/test_db.py
```

### Expected run times (free-tier API keys)

| Script | Typical duration | Main bottleneck |
|--------|-----------------|-----------------|
| `ingest_polygon.py` | 3–5 min | Polygon 12 s rate-limit sleep × tickers |
| `ingest_census.py` | < 10 s | Network |
| `ingest_opensky.py` | < 10 s | Network |
| `ingest_worldbank.py` | < 30 s | Pagination limits |
| `ingest_fred.py` | < 10 s | Network |
| `ingest_comtrade.py` | < 30 s | Network / Pagination |
| `clean_data.py` | < 60 s | Postgres read/write |

---

## Component Reference

### `db_utils.py` — Database Utilities

Singleton module imported by every other script. Not run directly.

| Function | Description |
|----------|-------------|
| `get_engine()` | Creates a SQLAlchemy engine from `.env` credentials |
| `test_connection(engine)` | Validates the DB connection with `SELECT 1` |
| `write_dataframe(df, table, engine)` | Bulk-inserts a DataFrame (multi-row batches) |
| `read_table(table, engine)` | Loads a full Postgres table into a DataFrame |
| `read_query(sql, engine, params)` | Executes a parameterised SELECT query |
| `table_exists(table, engine)` | Returns `True`/`False` |
| `list_tables(engine)` | Returns sorted list of all visible tables |
| `get_row_count(table, engine)` | Fast row count without loading data into memory |

---

### Modular API Ingestion Scripts

Pulls from external APIs sequentially. All share a single `_http_get()`
helper in `api_utils.py` that implements retry-with-backoff.

#### 1. Polygon.io → `raw_polygon` (`ingest_polygon.py`)

- **Endpoint:** `GET /vX/reference/financials`
- **Tickers:** Passed dynamically via script arguments.
  `uv run python data_pipeline/ingest_polygon.py AAPL MSFT AMZN TSLA WMT`
- **Metrics extracted per quarter:**
  - *Income statement:* revenues, gross_profit, net_income_loss,
    operating_income_loss, cost_of_revenue, basic_eps
  - *Balance sheet:* assets, current_assets, current_liabilities,
    inventory, liabilities, long_term_debt
  - *Cash flow:* net_cash_flow, net_cash_flow_from_operations
- **Derived metrics computed locally:**
  - `gross_profit_margin` = gross_profit / revenues
  - `net_profit_margin` = net_income_loss / revenues
  - `inventory_turnover` = cost_of_revenue / inventory
  - `dso_days` = (current_assets − inventory) / (revenues / 90)
  - `current_ratio` = current_assets / current_liabilities
  - `debt_to_assets` = liabilities / assets
- **Rate limit:** `time.sleep(12)` between every ticker (≤ 5 calls/min free tier)

#### 2. US Census Bureau M3 → `raw_census` (`ingest_census.py`) (`ingest_census.py`)

- **Endpoint:** `https://api.census.gov/data/timeseries/eits/m3`
- **Survey:** Manufacturers' Shipments, Inventories, and Orders
- **Data types pulled:**
  - `VS` — Value of Shipments
  - `II` — Inventories
  - `NO` — New Orders
  - `BO` — Backlog of Orders
  - `IO` — Inventory-to-Orders ratio
- **History:** 2018 → present (configurable via `CENSUS_M3_START_YEAR`)
- **Free:** yes, API key only needed for higher rate limits

#### 3. OpenSky Network → `raw_opensky` (`ingest_opensky.py`) (`ingest_opensky.py`)

- **Endpoint:** `https://opensky-network.org/api/states/all`
- **Data:** Live snapshot of all tracked aircraft — ICAO24, callsign,
  origin country, lat/lon, altitude, velocity, on-ground flag, vertical rate
- **Auth:** HTTP Basic Auth (optional). Leave `OPENSKY_USERNAME` blank in
  `.env` to use anonymous access (still works, slightly lower rate limit).
- **Use case:** Proxy for aggregate air-cargo and commercial transit activity

#### 5. World Bank & FRED → `raw_worldbank` & `raw_fred` (`ingest_worldbank.py` / `ingest_fred.py`)
- Independent modular scripts pulling time-series indicator data.

---

#### 6. UN Comtrade → `raw_comtrade` (`ingest_comtrade.py`)
- Independent script pulling annual global trade data from the new UN Comtrade API v1.
- Fully parameterized natively via CLI to accept target reporters, partners, HS codes, and years.
- Example: `uv run python data_pipeline/ingest_comtrade.py --reporters 842 --cmd-codes 8542`

---

### `clean_data.py` — Data Cleaning Pipeline

Reads every `raw_*` table and writes a `processed_*` counterpart.

See [Cleaning Rules](#cleaning-rules) for the full specification.

---

### `test_db.py` — Database Smoke Test

Runs 17 assertions against a live PostgreSQL instance to verify that
`db_utils.py` works end-to-end before any ingestion scripts are run.

Tests covered:
1. Engine creation
2. Connectivity (`SELECT 1`)
3. `write_dataframe()` — correct row count returned
4. `table_exists()` — positive and negative cases
5. `list_tables()` — type and membership
6. `get_row_count()` — exact count
7. `read_table()` — round-trip row count, column presence, null preservation (numeric and string), value correctness
8. `read_query()` — parameterised SQL, value accuracy
9. Append mode — row count doubles correctly
10. Cleanup — test table dropped cleanly

---

## Database Tables

### Raw tables (written by ingest scripts)

| Table | Source script | Key columns |
|-------|--------------|-------------|
| `raw_polygon` | `ingest_polygon.py` | ticker, end_date, revenues, inventory, inventory_turnover, dso_days, debt_to_assets |
| `raw_census` | `ingest_census.py` | time_slot_date, data_type_code, category_code, cell_value, seasonally_adj |
| `raw_opensky` | `ingest_opensky.py` | icao24, callsign, origin_country, latitude, longitude, baro_altitude, on_ground |
| `raw_worldbank` | `ingest_worldbank.py` | date, indicator_id, country_id, value |
| `raw_fred` | `ingest_fred.py` | date, series_id, series_name, value |
| `raw_comtrade` | `ingest_comtrade.py` | reporter, partner, commodity_code, trade_value_usd, netweight_kg, ref_year |

### Processed tables (written by `clean_data.py`)

Each `processed_*` table mirrors its `raw_*` source with:
- High-null columns (> 15 % null) removed entirely
- Remaining numeric nulls filled with column medians
- A boolean `<col>_was_null` indicator column inserted immediately to the
  right of each imputed column

---

## Cleaning Rules

The cleaning pipeline in `clean_data.py` applies a rigorous time-series alignment:

### Stage 1 — Special Column Prep & Pruning
- Normalizes date columns across sources.
- Drops columns with >15% missing values (excluding primary time/group keys).

### Stage 2 — Time-Series Alignment & Imputation
- Groups data by primary entity keys (e.g., `ticker`, `series_id`, `country_id`).
- Reindexes each group to a consistent frequency between its min and max dates.
- Applies linear interpolation for numeric gaps, then forward/backfill, then global medians/modes to guarantee **zero nulls remain**.

**What is NOT imputed:**
- String / categorical columns (e.g. country names, company names, HS codes)
- Boolean columns
- Datetime columns

---

## Troubleshooting

### `CRITICAL: Cannot reach the PostgreSQL database`
- Confirm the container is running:
  ```bash
  docker compose -f data_pipeline/docker-compose.yml ps   # Docker
  podman compose -f data_pipeline/docker-compose.yml ps   # Podman
  ```
- Verify that `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` in
  `data_pipeline/.env` match the values the container was initialised with.
- Check port 5432 is not in use by another process:
  ```bash
  ss -tlnp | grep 5432
  ```
- If you previously ran the container with different credentials, the old data
  volume will refuse the new password. Wipe it and restart:
  ```bash
  podman compose -f data_pipeline/docker-compose.yml down -v
  podman compose -f data_pipeline/docker-compose.yml up -d
  ```

### `FATAL: password authentication failed for user "..."`
The container's data volume was initialised with a different password than
what `.env` specifies. See the "wipe and restart" step above.

### `short-name resolution enforced` (Podman on Fedora / RHEL)
The `docker-compose.yml` already uses the fully-qualified image name
`docker.io/library/postgres:15-alpine` to avoid this. If you see it anyway,
confirm you are using the `docker-compose.yml` inside `data_pipeline/` and not
a different one.

### `ERROR: relation "raw_polygon" does not exist`
The raw table has not been created yet. Run `ingest_api.py` first, then
re-run `clean_data.py`.

### `[Polygon] Authentication failed`
Your `POLYGON_API_KEY` in `data_pipeline/.env` is invalid or still set to the
placeholder value. Sign up for a free key at <https://polygon.io/>.

### `[Census] HTTP error fetching M3 data`
- Verify `CENSUS_API_KEY` is set and not the placeholder value.
- The Census API occasionally has maintenance windows — wait a few minutes and
  retry.

### `[OSHub] OSHUB_API_KEY is not set`
Generate a token at <https://opensupplyhub.org/> (Profile → API Key) and
paste it into `data_pipeline/.env` as `OSHUB_API_KEY=`.

### `[Comtrade] COMTRADE_API_KEY is not set`
Set your Free Basic UN Comtrade API Key in `data_pipeline/.env` to securely fetch global trade data via API.

### `uv run` cannot find dependencies
Make sure you ran `uv add ...` from the **repo root** (`YHack/`), not from
inside `data_pipeline/`. The `.venv` lives at `YHack/.venv`.

### Port 5432 already in use
Either stop the conflicting service, or change `POSTGRES_PORT` in
`data_pipeline/.env` to a free port (e.g. `5433`) and update the `ports`
mapping in `docker-compose.yml` to `5433:5432`.