mypy:
	python3 -m mypy tilesgis

test:
	python3 -m pytest --cov=tilesgis --cov-report html

install-test-all:
	rm -rf .venv
	python3 -m venv .venv
	# NOTE: shapely must be installed like this or it breaks :/
	# also https://github.com/python-poetry/poetry/issues/1316
	.venv/bin/python3 -m pip install --no-binary Shapely -r requirements.txt
	.venv/bin/dotenv .venv/bin/python3 -m pytest --cov=tilesgis --cov-report html
