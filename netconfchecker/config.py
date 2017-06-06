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
# Either use generic vendor device OS for testing on virtualbox, or use 'network' and devices matching config file/folder name
# Note that for the latter they may be real hardware or a virtual fabric - but essentially configs are loaded to different named devices
DEVICES = {'juniper': {'host': '127.0.0.1', 'port': 2222, 'user':'root',
                       'key': '/Users/ecrewe/projects/opcna/netconf-testing/vagrant/olive/.vagrant/machines/olive1/virtualbox/private_key'},
           'cisco': {'host': '127.0.0.1', 'port': 2222, 'user':'root',
                     'key': '/Users/ecrewe/projects/opcna/netconf-testing/vagrant/ios/.vagrant/machines/ios1/virtualbox/private_key'},
           'network': {'host': 'FILENAME', 'port': 22,
                          'user': 'netconf',
                          'key': '/home/netconf/.ssh/id_rsa.netconf'
                    }
           }
