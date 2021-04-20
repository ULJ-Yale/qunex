#!/bin/bash -i
# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# -- Source the environment
source /opt/qunex/env/qunex_environment.sh

# -- Execute the call
/opt/qunex/bin/qunex.sh ${@:1}
