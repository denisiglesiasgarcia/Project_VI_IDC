#!/bin/bash

# Wait for PostgreSQL to start
until pg_isready -U postgres; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Starting import..."

# Import data into PostgreSQL
ogr2ogr -f "PostgreSQL" PG:"dbname=postgres user=postgres password=docker" "/data/indice3ans_epsg_4326_superlight.geojson"

echo "Import completed."

# Keep container running
sleep infinity