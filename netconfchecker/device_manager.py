#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# File: device_manager.py
"""
API for jnpr pyez library to talk to one or more devices
"""

import os
import sys
import logging
import logging.handlers
import logging.config
from ncclient import manager as ncmanager

import jnpr.junos.exception
from jnpr.junos import Device
from jnpr.junos.utils.config import Config

import jxmlease

from netconfchecker.exceptions import DoneWithDevice, LoadNotOKError
from netconfchecker.config import KEY_HOME, DEVICES

__author__ = 'Ed Crewe <edmundcrewe@gmail.com>'
__docformat__ = 'plaintext'
__date__ = '2017-02-09'

# This is the main prefix used for logging
LOGGER_BASENAME = 'netconftest.device_manager'
LOGGER = logging.getLogger(LOGGER_BASENAME)

class DeviceManager(object):
    """ABC for device manager lib for juniper or cisco etc - see subfolders"""
    vendor = None
    devices = {}
    
    def __init__(self, loglevel='CRITICAL'):
        """Set up the devices metadata ready for login"""
        self.parser = jxmlease.EtreeParser()
        self.logger = logging.getLogger('{base}.{suffix}'.format(base=LOGGER_BASENAME, suffix=self.__class__.__name__))
        ch = logging.StreamHandler(sys.stdout)
        self.loglevel = loglevel
        ch.setLevel(self.loglevel)
        ### Default ncclient logging is too verbose so set it to same level as this class
        ncmanager.logger.setLevel(self.loglevel)
        ncmanager.transport.ssh.logger.setLevel(self.loglevel)
        ncmanager.transport.session.logger.setLevel(self.loglevel)        
        ncmanager.operations.rpc.logger.setLevel(self.loglevel)        
        ###
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

