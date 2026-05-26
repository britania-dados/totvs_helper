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
	powershell -Command "foreach ($d in @('build','build_64b','build_32b','dist')) { if (Test-Path $d) { Remove-Item -Recurse -Force $d } }; if (Test-Path packaging/windows_version_info.build.txt) { Remove-Item -Force packaging/windows_version_info.build.txt }"
