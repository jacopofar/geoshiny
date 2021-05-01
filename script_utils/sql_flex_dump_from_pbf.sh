#!/bin/bash
# This script is designed to run INSIDE the pgosm-flex container
# Run with:
#   ./sql_flex_dump_from_pbf.sh \
#       /app/input/filename.pbf \
#       4000 \
#       run-all
#
# $1 - the PBF file to ingest
# $2 - Cache (mb) - e.g. 4000
# $3 - Layers to load - must match flex-config/$3.lua and flex-config/$3.sql

SQITCH_PATH=/app/db/
OUT_PATH=/app/output/

# ISO 639 for the language to use when localized names are available
export PGOSM_LANGUAGE=en

function wait_postgres_is_up {
  until pg_isready; do
    echo "Waiting for the DB to be up..."
    sleep 4
  done
}

echo ""
echo "---------------------------------"
echo "Start PgOSM-Flex processing"
echo "Input file: $1"
echo "Cache: $2"
echo "PgOSM Flex Style: $3"


if [ -f /app/input/$1 ]; then
    echo "$1 will be imported."
else
    echo "$1 does not exist in /app/input/.  Aborting..."
    exit 1
fi


if [ -z $PGOSM_DATA_SCHEMA_ONLY ]; then
  echo "DATA_SCHEMA_ONLY NOT SET"
  DATA_SCHEMA_ONLY=false
else
  DATA_SCHEMA_ONLY=$PGOSM_DATA_SCHEMA_ONLY
  echo "DATA_SCHEMA_ONLY set to $DATA_SCHEMA_ONLY"
fi

if [ -z $PGOSM_DATA_SCHEMA_NAME ]; then
  echo "PGOSM_DATA_SCHEMA_NAME NOT SET"
  DATA_SCHEMA_NAME="osm"
else
  DATA_SCHEMA_NAME=$PGOSM_DATA_SCHEMA_NAME
fi
echo "DATA_SCHEMA_NAME will be $DATA_SCHEMA_NAME"

wait_postgres_is_up

# the DB seems to go down after being ready (?) for an instant, probably a low memory issue
sleep 5
wait_postgres_is_up


echo "Create empty pgosm database with extensions..."
psql -U postgres -c "DROP DATABASE IF EXISTS pgosm;"
psql -U postgres -c "CREATE DATABASE pgosm;"
psql -U postgres -d pgosm -c "CREATE EXTENSION postgis;"
psql -U postgres -d pgosm -c "CREATE SCHEMA osm;"

echo "Deploy schema via Sqitch..."
cd $SQITCH_PATH
su -c "sqitch deploy db:pg:pgosm" postgres
echo "Loading US Roads helper data"
psql -U postgres -d pgosm -f data/roads-us.sql


REGION="$1--$2"
echo "Setting PGOSM_REGION to $REGION"
export PGOSM_REGION=$REGION

osm2pgsql --version

echo "Running osm2pgsql..."
cd /app/flex-config
osm2pgsql -U postgres --create --slim --drop \
  --cache $2 \
  --output=flex --style=./$3.lua \
  -d pgosm /app/input/$1

if [ $DATA_SCHEMA_NAME != "osm" ]; then
    echo "Changing schema name from osm to $DATA_SCHEMA_NAME"
    psql -U postgres -d pgosm \
      -c "ALTER SCHEMA osm RENAME TO $DATA_SCHEMA_NAME;"
fi

cd /app

OUT_NAME="pgosm-flex-$1.sql"
OUT_PATH="/app/output/$OUT_NAME"

if $DATA_SCHEMA_ONLY; then
  echo "Running pg_dump, only data schema..."
  pg_dump -U postgres -d pgosm \
     --schema=$DATA_SCHEMA_NAME > $1.sql
else
  echo "Running pg_dump including pgosm schema..."
  pg_dump -U postgres -d pgosm \
     --schema=$DATA_SCHEMA_NAME --schema=pgosm > /app/output/$1.sql
fi

echo "PgOSM processing complete. Final output file: $1.sql"

