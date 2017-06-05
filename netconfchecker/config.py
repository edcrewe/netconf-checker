"""Globals that are set in environment"""
import logging
import os

HANDLER = logging.StreamHandler()
ENV = {}

# General enviroment paths for python, lib and tmp
ENV['LD_LIBRARY_PATH'] = "/usr/local/lib"
ENV['TMPDIR'] = "~/tmp"

### Devices ####
ENV['DEVICE'] = os.environ.get('DEVICE', 'olive1')
KEY_HOME = '/'
ANSIBLE_PFILE = ''
# use docker host ip route show instead of 127.0.0.1 '172.17.0.2' 
DEVICES = {'olive1': {'host': '127.0.0.1', 'port': 2222, 'user':'root',
                     'key': '/Users/ecrewe/devicesvm/netconf-testing/vagrant/olive/.vagrant/machines/olive1/virtualbox/private_key'},
           'realfabric': {'host': 'FILENAME', 'port': 22,
                          'user': 'netconf',
                          'key': '/home/netconf/.ssh/id_rsa.netconf'
                    }
           }
