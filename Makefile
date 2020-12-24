mypy:
	python3 -m mypy geocrazy

test:
	python3 -m pytest --cov=geocrazy --cov-report html

install-test-all:
	rm -rf .venv
	python3 -m venv .venv
	# necessary to ensure the latest pip which runs on Big Sur
	# pip before 2020.3 has issues with it
	# hopefully in the future will not be needed as 2020.3 will be already there
	.venv/bin/python3 -m pip install --upgrade pip
	# NOTE: shapely must be installed like this or it breaks :/
	# also https://github.com/python-poetry/poetry/issues/1316
	.venv/bin/python3 -m pip install --no-binary Shapely -r requirements.txt
	.venv/bin/python3 -m pytest --cov=geocrazy --cov-report html
