#!/bin/bash
set -eu -o pipefail

export COVERAGE_FILE=/output/.coverage

cd src
/app/venv/bin/python -m coverage run -m pytest -vv --junit-xml=/output/report.xml
/app/venv/bin/python -m coverage report
/app/venv/bin/python -m coverage xml -o /output/coverage.xml

