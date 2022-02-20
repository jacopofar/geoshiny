#!/usr/bin/env bash
#####
# This script runs OUTSIDE docker, and uses pgosm-flex to load a PBF file into postgres
# then generates a dump, which is used later to rebuild a DB from scratch
# Usage: ./database_from_pbf.sh some-file.osm.pbf
#####

# exit on error
set -e

echo "Input file: $1"

docker run --name pgosm --rm -d \
  -v $(pwd):/app/output \
  -e POSTGRES_PASSWORD=secret \
  -p 5459:5432 -d rustprooflabs/pgosm-flex


docker cp sql_flex_dump_from_pbf.sh pgosm:/app

docker exec pgosm sh -c 'until pg_isready; do echo "Waiting for the DB to be up..."; sleep 4; done'

# RAM here is a guess
docker exec pgosm sh -c "python3 docker/pgosm_flex.py --ram 4 --debug --input-file /app/output/$1 --layerset everything --skip-dump"

docker exec pgosm sh -c "pg_dump -U postgres -d pgosm --schema=osm > /app/output/$1.sql"

# the container did generate the SQL dump, remove it
docker stop pgosm

docker run --name postgis-test-db \
  -p 15432:5432 \
  -e POSTGRES_PASSWORD=testpassword \
  -v $(pwd):/input \
  -d postgis/postgis:14-master

docker exec postgis-test-db sh -c 'until pg_isready; do echo "Waiting for the DB to be up..."; sleep 4; done'
# sometimes there's a random restart, especially with low memory. Wait some extra time
# meh...
sleep 5
docker exec -it postgis-test-db /usr/bin/createdb -U postgres osm_data
docker exec -it postgis-test-db /usr/bin/psql -U postgres -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;" osm_data
# ingest back
docker exec postgis-test-db sh -c "psql -U postgres -f /input/$1.sql osm_data"

