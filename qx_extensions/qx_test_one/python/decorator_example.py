#!/usr/bin/env python
# encoding: utf-8

from general.extensions import qx


@qx()
def simple_hello(name=None):
    '''
    print_hello [name]

    If name is provided, the function greets you, otherwise it asks you for your name.
    '''

    if name is None:
        name = "You"
    print(f"Hello {name}")
