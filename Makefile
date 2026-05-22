.PHONY: lint format test typecheck build clean

lint:
	python -m ruff check .

format:
	python -m black .

test:
	python -m pytest

typecheck:
	python -m mypy src

build:
	powershell -ExecutionPolicy Bypass -File "scripts/build_exe.ps1"

clean:
	powershell -Command "if (Test-Path build) { Remove-Item -Recurse -Force build }; if (Test-Path dist) { Remove-Item -Recurse -Force dist }"
