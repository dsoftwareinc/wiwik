#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$SCRIPT_DIR/.."
cd "$BASEDIR" || exit
source "$BASEDIR/env/bin/activate"
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export ENVIRONMENT=prod
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES # https://stackoverflow.com/questions/50168647/multiprocessing-causes-python-to-crash-and-gives-an-error-may-have-been-in-progr/52230415
python $BASEDIR/forum/manage.py rqworker cron default
deactivate