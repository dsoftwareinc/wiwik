#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$SCRIPT_DIR/.."
echo "[reset.sh] Activating virtualenv"
source "$BASE_DIR/.venv/bin/activate" || (echo "Couldn't activate virtualenv" && exit)
cd "$BASE_DIR/forum" || exit
coverage run --source='.' manage.py test --no-logs

DATE_STR=$(date +"%Y-%m-%d--%H-%M")
COVERAGE_REPORT_FILE="$BASE_DIR/coverage_report.txt"
echo "Generating coverage report file $COVERAGE_REPORT_FILE"
echo "coverage report for $DATE_STR" >"$COVERAGE_REPORT_FILE"
EXCLUDE_FROM_COVERAGE='"*/tests/*","manage.py","*/migrations/*"'
coverage report --omit="$EXCLUDE_FROM_COVERAGE" >> "$COVERAGE_REPORT_FILE"
