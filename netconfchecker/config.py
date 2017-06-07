"""Globals that are set in environment"""
import logging
import os

HANDLER = logging.StreamHandler()
ENV = {}

# General enviroment paths for python, lib and tmp
ENV['LD_LIBRARY_PATH'] = "/usr/local/lib"
ENV['TMPDIR'] = "~/tmp"

### Devices ####
ENV['DEVICE'] = os.environ.get('DEVICE', 'juniper')
KEY_HOME = '/'
ANSIBLE_PFILE = ''
PKG_PATH = os.path.realpath(__file__)
PKG_PATH = '/'.join(PKG_PATH.split('/')[:-2])
VAGRANT_PATH = os.environ.get('VAGRANT_PATH', PKG_PATH)
# Either use generic vendor device OS for testing on virtualbox, or use 'network' and devices matching config file/folder name
# Note that for the latter they may be real hardware or a virtual fabric - but essentially configs are loaded to different named devices
DEVICES = {'juniper': {'host': '127.0.0.1', 'port': 2222, 'user':'root',
                       'key': '%s/vagrant/juniper/.vagrant/machines/olive1/virtualbox/private_key' % VAGRANT_PATH},
           'cisco': {'host': '127.0.0.1', 'port': 2222, 'user':'root',
                     'key': '%s/vagrant/cisco/.vagrant/machines/ios1/virtualbox/private_key' % VAGRANT_PATH},
           'network': {'host': 'FILENAME', 'port': 22,
                          'user': 'netconf',
                          'key': '/home/netconf/.ssh/id_rsa.netconf'
                    }
           }
