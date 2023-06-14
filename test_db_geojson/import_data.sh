#!/bin/bash

# Set environment variables
export POSTGRES_PASSWORD=postgis
export POSTGRES_USER=postgis
export POSTGRES_DB=mydatabase

# Wait for the Postgres service to start up
until psql -h "localhost" -U "$POSTGRES_USER" -c '\q'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Postgres is up - executing command"

# Create the database and enable PostGIS extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE $POSTGRES_DB;
  \c $POSTGRES_DB
  CREATE EXTENSION postgis;
EOSQL

# Restart Postgres
#sudo systemctl restart postgresql

# Import the GeoJSON data
#ogr2ogr -f PostgreSQL PG:"dbname=$POSTGRES_DB user=$POSTGRES_USER password=$POSTGRES_PASSWORD" /data/indice3ans_epsg_4326_superlight.geojson