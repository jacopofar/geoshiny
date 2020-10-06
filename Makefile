mypy:
	python3 -m mypy tilesgis

test:
	python3 -m pytest --cov=tilesgis --cov-report html
