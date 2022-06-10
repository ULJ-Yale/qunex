#!/usr/bin/env python
# encoding: utf-8

def print_hello(name=None):
    '''
    print_hello [name]

    If name is provided, the function greets you, otherwise it asks you for your name.
    '''

    if name is None:
        print("Hi! Can you please tell me your name?")

    else:
        print("Hi %s! Nice to meet you!" % name)

commands = {'print_hello' : { 'com': print_hello, 'args': ('name',)}}
