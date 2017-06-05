#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# File: exceptions.py
#
"""
Main module Exceptions file

Put your exception classes here
"""

__author__ = 'Ed Crewe <edmundcrewe@gmail.com>'
__docformat__ = 'plaintext'
__date__ = '2016-05-19'


class LoadNotOKError(Exception):

    def __init__(self, expression=None, message=None):
        self.expression = expression
        self.message = message

class DoneWithDevice(Exception): 

    def __init__(self, logger=None):
        if logger:
            return logger.debug('Finished with device')
