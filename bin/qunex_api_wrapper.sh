#!/bin/bash -i

# -- Source the environment
source /opt/qunex/env/qunex_environment.sh

# -- Execute the call
/opt/qunex/bin/qunex.sh ${@:1}
