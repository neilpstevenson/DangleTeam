#!/bin/bash

source "./environment.sh"
source "$VIRTUAL_ENV/bin/activate"
cd "$DANGLE_HOME/danglePython"
python "$DANGLE_HOME/danglePython/approxEngControllerProcess.py"
