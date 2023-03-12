install: requirements.txt
	pip-sync

requirements.txt: pyproject.toml
	pip-compile pyproject.toml --extra dev --extra docs --resolver=backtracking

lock:
	make requirements.txt --always-make

lint:
	isort --check --diff .
	black --check --diff .
	ruff .
	pyright .

format:
	isort .
	black .

test:
	pytest

cov:
	pytest --cov-report term --cov-report xml

build:
	python -m build

build-doc:
	mkdocs build