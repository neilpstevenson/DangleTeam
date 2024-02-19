#!/bin/bash
 
# This runs as root, so need to ensure shared memory is globally writable
umask 000

source "./environment.sh"
source "$VIRTUAL_ENV/bin/activate"
cd "$DANGLE_HOME/danglePython"
python "$DANGLE_HOME/danglePython/displayEyesProcess.py"
