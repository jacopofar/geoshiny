.PHONY: mypy
mypy:
	python3 -m mypy geoshiny

.PHONY: test
test:
	python3 -m pytest --cov=geoshiny --cov-report html

.PHONY: install-test-all
install-test-all:
	rm -rf .venv
	rm -rf htmlcov
	python3 -m venv .venv
	# necessary to ensure the latest pip which runs on Big Sur
	# pip before 2020.3 has issues with it
	# hopefully in the future will not be needed as 2020.3 will be already there
	.venv/bin/python3 -m pip install --upgrade pip
	# NOTE: shapely must be installed like this or it breaks :/
	# also https://github.com/python-poetry/poetry/issues/1316
	.venv/bin/python3 -m pip install --no-binary Shapely -r requirements.txt
	# and now the GDAL binary juggling!
	# GDAL works differently depending on which commands were available in the path when installing it!
	# also, wants numpy installed beforehand, or it installs without errors and then breaks at runtime
	# so, first uninstall GDAL
	.venv/bin/python3 -m pip uninstall -y gdal
	# then reinstall it, now numpy is installed so the effect will be different
	# also here the version is the latest, no matter what was written in the requirements.txt
	# but at this point is a lesser evil
	PATH=.venv/bin:$$PATH .venv/bin/python3 -m pip install --no-binary GDAL GDAL
	# same path consideration needed when running the test
	PATH=.venv/bin:$$PATH .venv/bin/python3 -m pytest --cov=geoshiny --cov-report html

.PHONY: create-test-db
create-test-db:
	docker run --rm --name postgis-test-db -p 15432:5432 -e POSTGRES_PASSWORD=testpassword -d postgis/postgis:13-master
	docker exec postgis-test-db sh -c 'until pg_isready; do echo "Waiting for the DB to be up..."; sleep 4; done'
	# sometimes there's a random restart, especially with low memory. Wait some extra time
	# meh...
	sleep 5
	docker exec -it postgis-test-db /usr/bin/createdb -U postgres osm_data
	docker exec -it postgis-test-db /usr/bin/psql -U postgres -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;" osm_data
	# create test DB data
	docker cp tests/sampledata/rostock_2021-05-01.sql postgis-test-db:/schema.sql
	docker exec postgis-test-db sh -c "psql -U postgres -f /schema.sql osm_data"

.PHONY: delete-test-db
delete-test-db:
	docker kill postgis-test-db

.PHONY: cleanup-and-fail
cleanup-and-fail:
	echo "cleaning up after failure..."
	make delete-test-db
	false

.PHONY: test-from-zero
test-from-zero:
	make create-test-db
	# macOS ships with a vintage Make, so ONESHELL + bash trap cannot be used and this is an alternative
	PGIS_CONN_STR=postgres://postgres:testpassword@localhost:15432/osm_data make install-test-all || make cleanup-and-fail
	make delete-test-db
