#!/usr/bin/env python
# encoding: utf-8

import greetings


arglist = [['# ---- Plugin settings'],
           ['p_name', 'Somebody', str, "The name to process"]
]


tomap = {'p_old_name': 'p_name'}

deprecated_parameters = {'p_last_name': 'p_name'}

calist = [['pga', 'greet_all',greetings.greet_all, "Greet all the sesions"]]
