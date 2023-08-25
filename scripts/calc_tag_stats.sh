#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$SCRIPT_DIR/.."
echo "[reset.sh] Activating virtualenv"
source env/bin/activate || (echo "Couldn't activate virtualenv" && exit)
cd "$BASE_DIR/forum" || exit
python manage.py update_tags_stats
cd "$BASE_DIR" || exit
