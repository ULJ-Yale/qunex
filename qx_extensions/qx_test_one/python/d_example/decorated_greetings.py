#!/usr/bin/env python
# encoding: utf-8

from general.extensions import qx_process
from processing.core import *


@qx_process()
def hello_bold(sinfo, options, magic_number: int = 0, overwrite=False, thread=0, p_name: str = "Name"):
    '''Hello Bold
    '''

    doOptionsCheck(options, sinfo, 'hello_bold')

    print(f"hello {p_name}: {magic_number}")
    return ("Done", (sinfo['id'], "boldly done", 0))
