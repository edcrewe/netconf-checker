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
from netconfchecker.device_manager import DeviceManager

__author__ = 'Ed Crewe <edmundcrewe@gmail.com>'
__docformat__ = 'plaintext'
__date__ = '2017-02-09'

# This is the main prefix used for logging
LOGGER_BASENAME = 'netconftest.device_manager'
LOGGER = logging.getLogger(LOGGER_BASENAME)

class JuniperManager(DeviceManager):
    """Manages a racks switches or a single switch for configuration"""
    vendor = 'juniper'
    devices = {}
    junos_ignore = ['warning: mgd: statement has no contents; ignored',
                    'error: error recovery ignores input until this point']

    def setup_device(self, config, name=None):
        """Configure a dictionary of device settings for connecting from config or supplied dictionary"""
        if config['key'].endswith('yaml'):
            # Assume it is an Ansible vault encrypted key
            config['key'] = self.decrypt_key(config['key'])
        key_path = os.path.join(KEY_HOME, config['key'])
        if not os.path.exists(key_path):
            raise Exception('VM key file is missing at %s' % key_path)
        if not name:
            name = config['host']
        self.devices[name] = Device(host=config['host'], user=config['user'],
                                    ssh_private_key_file=key_path, port=config['port'])

    def decrypt_key(self, crypt_file):
        """Use to decrypt Ansible vault files"""
        crypt_path = os.path.join(KEY_HOME, crypt_file)
        decrypt_cmd = 'ansible-vault decrypt --vault-password-file=%s %s' % (ANSIBLE_PFILE, crypt_path)
        raise Exception('NOT IMPLEMENTED YET, SINCE VAULT NOT DEPLOYED YET\n%s' % decrypt_cmd)
        os.system(decrypt_cmd)
    
    def summary_info(self, device):
        """Log in to a device and return success, summary info / error"""
        device.open()
        element = device.rpc.get_route_summary_information()
        try:
            return True, self.parser(element)
        except Exception as err:
            msg = "Failed to parse config load response"
            return False, ': '.join((msg, err))

    def load_template_config(self, device,
                             template_path, fmt='text'): 
        """Load templated config with "load merge".

        Given a template_path do:
            load merge of the templated config,
            commit,
            and check the results.

        Return True if the config was committed successfully, False otherwise.
        """
        commit = False
        connect_error = self.open_device_config(device)
        if connect_error:
            return connect_error
        err = self.load_template_config(self, device, template_path, fmt)
        if err:
            return err
        else:
            self.commit_template_config(device, check_only=False)
            commit = True
        self.close_device_config(device)
        return commit

    def junos_error(self, err):
        """Handle detailed error from Junos

        Make it one line and remove junos_ignore list of msgs
        """
        error = repr(err)
        for ignore in self.junos_ignore:
            error = error.replace(ignore, '')
        error = error.replace('\n', ' ')
        error = error.replace('  ', ' ')        
        return error
        
    def check_template_config(self, device=None,
                              template_path='', fmt='text', mode='normal'): 
        """Load templated config with "load merge".

        device.open()
        devconf = Config(device)
        devconf.lock()
        devconf.load(path=template, merge=True)
        return devconf.commit_check()

        Return error if the commit check or merge returns one
        """
        # use first of configured devices if none specified
        if not device:
            device = self.devices['vsrx1']
        connect_error = self.open_device_config(device)
        if connect_error:
            return connect_error
        commit_error = ''
        load_error = self.load_template_config(device, template_path)
        if load_error:
            return load_error
        else:
            commit_error = self.commit_template_config(device, check_only=True)
        self.close_device_config(device)
        return commit_error
    
    def commit_template_config(self, device, check_only=False):
        """Commit template config or commit check only and return the error if there is one"""
        success = False
        if device and getattr(device, 'cu'):
            try:
                if check_only:
                    success = device.cu.commit_check()
                    # rollback the change we made to the candidate config
                    # otherwise it can block subsequent use of private, exlusive or batch edit mode
                    device.cu.rollback(rb_id=1)
                    device.cu.commit()
                    device.close()
                else:
                    success = device.cu.commit(comment="Configuration edit by %s" % LOGGER_BASENAME)
            except (jnpr.junos.exception.RpcError,
                    jnpr.junos.exception.ConnectError,
                    LoadNotOKError(message='Device RPC open configuration failed')) as err:
                return repr(err).replace('\n', ' ')
            except Exception as err:
                return "Error occurred committing configuration: %s" % err
        if not success:
            if check_only:
                return "Error commit check failed"
            else:
                return "Error commit failed"                
        return ''
            
    def open_device_config(self, device):
        """Bind config class to device and open the device"""
        if not hasattr(device, 'cu'):
            device.bind(cu=Config)
        try:
            device.open()
            return ''
        except (jnpr.junos.exception.RpcError,
                jnpr.junos.exception.ConnectError,
                LoadNotOKError(message='Device RPC open configuration failed')) as err:
            return 'Device RPC failed: %s' % err                    
        except:
            return "Unknown error occurred loading configuration."
    
    def close_device_config(self, device):
        """Close device opened by load_template_config"""
        try:
            device.rpc.close_configuration()
            return True
        except jnpr.junos.exception.RpcError as err:
            self.logger(err)
        return False
        
    def load_template_config(self, device,
                              template_path,
                              fmt='text', mode='normal'):
        """Open device and merge template config returning any error if it occurs

        Note that the device mode effects the level of load and commit validation performed.
        So private mode seems to perform the highest level of validation

        If fmt is not supplied then it will work it out based on file extention so .conf.part needs fmt
        If merge works then it returns an XML reponse parsable to {'load-configuration-results': {'ok': u''}}
        """
        if not os.path.exists(template_path):
            msg = 'Template not found %s' % template_path
            return msg
        resp = 'Could not load config to device'
        try:
            if mode == 'exclusive':
                device.cu.lock()
            if mode == 'private':
                device.rpc.open_configuration(private=True)
            elif mode == 'dynamic':
                device.rpc.open_configuration(dynamic=True)
            elif mode == 'batch':
                device.rpc.open_configuration(batch=True)
            else:
                device.rpc.open_configuration()                
        except jnpr.junos.exception.RpcError as err:
            if not (err.rpc_error['severity'] == 'warning' and
                    'uncommitted changes will be discarded on exit' in
                    err.rpc_error['message']):
                return 'Config open failed on device: %s' % err.rpc_error['message']
        try:
            element = device.cu.load(path=template_path,
                                     format=fmt,
                                     merge=True)
            try:
                resp = self.parser(element)
            except Exception as err:
                msg = "Failed to parse config load response"
                return ': '.join((msg, err))
            if mode == 'exclusive':
                device.cu.unlock()
        except Exception as err:
            return self.junos_error(err)
        # sometimes seems to return empty response for success    
        if resp and str(resp).find("{'ok':")==-1:
            return 'Junos load response: %s' % resp
        # DEBUG print 'Successful load: %s' % template_path
        return ''

