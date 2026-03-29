#!/bin/bash
set -e

# Ensure that the database is torn down automatically on script exit (whether success or error).
trap 'echo "Tearing down PostgreSQL container..."; podman compose -f data_pipeline/docker-compose.yml down' EXIT

podman compose -f data_pipeline/docker-compose.yml up -d

echo "Waiting for PostgreSQL container to become healthy..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ "$(podman inspect -f '{{.State.Health.Status}}' supply_chain_postgres 2>/dev/null)" != "healthy" ]; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "PostgreSQL did not become healthy in time. Exiting."
        exit 1
    fi
    sleep 2
done
echo "PostgreSQL is healthy and ready!"

# verify the database is reachable
uv run python data_pipeline/test_db.py

# Get raw data from polygon, us census, opensky, worldbank, fred
uv run python data_pipeline/ingest_polygon.py AAPL MSFT AMZN TSLA WMT TGT FDX UPS HON CAT XOM BA
uv run python data_pipeline/ingest_census.py
uv run python data_pipeline/ingest_opensky.py
uv run python data_pipeline/ingest_worldbank.py
uv run python data_pipeline/ingest_fred.py

# Get raw data from UN Comtrade API
uv run python data_pipeline/ingest_comtrade.py --reporters 842,156,276,392 --partners 0 --cmd-codes 8542,8708 --years 2022,2023

# clean up the raw data
uv run python data_pipeline/clean_data.py

echo "Pipeline execution completed successfully!"
# The trap will automatically run `podman compose down` here.
