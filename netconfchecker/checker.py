#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run config validation
"""
import logging
import os
import shutil
import sys
from jnpr.junos.exception import ConnectClosedError

from netconfchecker.juniper.device_manager import DeviceManager
from netconfchecker.config import DEVICES


class CommitCheck():
    """Test class for inputbuilder use A-Z module name prefix for sequence"""
    tmpl_types = ['leaf', 'spine', 'fabric', 'dci', 'tr']
    templates = []
    configs = []
    fail_fast = False
    marker = '----'
    many_devices = False
    

    def __init__(self, path=""):
        """
        Set up environment, fixtures and run functional cmd.

        All our tests check its outputs - and it takes a while, so lets just run it once.
        This is where you can setup things that you use throughout the tests. 
        This method is called before all tests
        """
        if not path:
            path = '/Users/ecrewe/tmp'
        # Setup templates
        self.data_path = path 
        self.get_templates(path)
        # Setup device(s)
        self.device_name = os.environ.get('DEVICE', 'juniper') 
        self.manager = DeviceManager()
        if not DEVICES.has_key(self.device_name):
            raise Exception('There is no config for device %s' % self.device_name)
        config = DEVICES[self.device_name]
        if config['host'] == 'FILENAME':
            self.many_devices = True
            for template in self.list_templates():
                config['host'] = self._get_device_name(template)
                try:
                    self.manager.setup_device(config, config['host'])
                except:
                    pass
            if self.manager.devices:
                self.manager.devices[self.device_name] = self.manager.devices[self.manager.devices.keys()[0]]
        else:
            self.manager.setup_device(config, self.device_name)
                
    def get_templates(self, path):
        """Check we have generated all the configs"""
        self.tmp_path = path
        self.use_fixtures = False
        if self.use_fixtures:
            #FIXME - Note this can remove templates that were built by other means - be better to use different path for fixtures?
            if os.path.exists(self.tmp_path):
                shutil.rmtree(self.tmp_path)
            self.extract_fixture()
        self.templates = self.list_templates()
        self.sample_templates = self.list_templates(sample=True, parts=True)
        
    def list_templates(self, sample=False, parts=False):
        """run integrator build.sh (could skip final rpm part but it doesnt add much to the time so maybe just use build.sh)"""
        tmp_path = self.tmp_path
        if parts and not self.use_fixtures:
            tmp_path = tmp_path.replace('/templates', '/tmp')
        if not os.path.exists(tmp_path):
            return []
        templates = []
        all_templates = [os.path.join(tmp_path, tmpl) for tmpl in os.listdir(tmp_path)]
        for tmpl_type in self.tmpl_types:
            for template in all_templates:
                if template.find('-%s-' % tmpl_type) > -1:
                    templates.append(template)
                    if sample:
                        break
        return templates
        
    def report(self, results):
        """Generate notification report"""
        output = ''
        count = 1
        countstr = '%s. ' % count        
        for line in results:
            if line == self.marker:
                count += 1
                countstr = '%s. ' % count
            else:
                output += '%s%s\n' % (countstr, line)
                countstr = ''
        print output
        return output
    
    def check_template(self, device, template, mode='normal', check_only=True):
        """Try loading and committing a template and get back any fail status

        For report want parent folder and template name - so identifies part or composite templates
        """
        results = self._load_template(device, template, mode)
        if not results:
            results.extend(self._commit_template(device, template, check_only))
        return results

    def _load_template(self, device, template, mode):    
        results = []
        try:
            template_name = '/'.join(template.split('/')[-2:])
        except:
            template_name = template
        try:
            self.manager.close_device_config(device)
        except:
            pass
        
	try:
            load_error = self.manager.merge_template_config(device, template, 'text', mode) 
	except ConnectClosedError, err: 
            self.manager.open_device_config(device) 
	    load_error = self.manager.merge_template_config(device, template, 'text', mode)
        if load_error:
            results.append('LOAD FAIL %s: %s' % (device.facts['hostname'], template_name))
            results.append(load_error)
        return results
    
    def _commit_template(self, device, template, check_only=True):
        results = []
        commit_error = self.manager.commit_template_config(device, check_only)
        if commit_error:
            results.append('COMMIT FAIL %s: %s' % (device.facts['hostname'], template))
            results.append(commit_error)
        try:
            self.manager.close_device_config(device)
        except:
            pass
        return results

    @staticmethod
    def _get_device_name(template):
        if template.find('/') > -1:
            pathlist = template.split('/')
            return pathlist[-1].replace('.conf', '')
        else:
            return template
        
    def get_device(self, name=''):
        """Connect to named device if supplied else test everything on same device"""
        if name:
            name = self._get_device_name(name)
        else:
            name = self.device_name
        # Assume if there is no specific device related to a template name, just load to the default test device
        if not self.manager.devices.has_key(name):
            name = self.device_name
        device = self.manager.devices[name] 
        # Use cu attribute as a marker that the device is already open ... if no cu, open it
        # if not hasattr(device, 'cu'):
        try:
            connect_error = self.manager.open_device_config(device)
        except Exception, connect_error:
            pass
        if connect_error:
            raise Exception(connect_error)
        return device

    def check_templates(self, templates, mode):
        """Run a check of all templates passed in using the config edit mode specified"""
        results = []
        try:
            device = self.get_device(self.device_name)
            # DEBUG results.append('Device Connect SUCCESS: %s' % self.device_name)
        except:
            results.append('Default device Connect FAIL: %s' % self.device_name)            
            device = None
        assert device, "no device setup"
        for template in templates:
            # Lets not test the type sample templates twice - except we should in case they are empty
            # if template not in self.sample_templates:
            if self.many_devices:
                try:
                    device = self.get_device(template)
                    # results.append('Device Connect SUCCESS: %s' % device.facts['hostname'])
                except Exception, connect_error:
                    results.append('Device Connect FAIL: %s - %s' % (self._get_device_name(template), connect_error))
		    continue # Do not try and load to different device if many_devices test
            fails = self.check_template(device, template, mode)
            if fails:
                results.extend(fails)
                results.append(self.marker)
                if self.fail_fast:
                    assert not fails
        report = self.report(results)
        if not report.count(' FAIL')==0:
            print '%s load and %s commit fails were found' % (report.count('LOAD FAIL'),
                                                                     report.count('COMMIT FAIL'))

    def run(self):
        """Run the full process of load and commit check and diff if available for report"""
        self.check_templates_available()
        self.check_device_available()
        self.check_parts_for_each_type()
        self.check_config_diff()        
        
    def check_templates_available(self):
        """Test that the templates are ready for loading

        Note we may always have templates from fixture
        so to check if build works, count sample parts tmp folders
        """
        assert len(self.templates)>5, 'Should be at least 5 templates found to load and check for a unit at %s' % self.tmp_path
    
    def check_device_available(self):
        """Test that we can connect to the device being used for commit checking"""
        try:
            device = self.get_device()
            connect_error = None
        except Exception, connect_error:
            pass
        assert not connect_error, connect_error
        try:
            success, info = self.manager.summary_info(device)
        except Exception, err:
            info = err
            success = False
        assert success, info
        # DEBUG raise Exception(info)
        if not success:
            raise Exception(info)
    
    def check_parts_for_each_type(self):
        """Load and commit check each part of each type of config
        
        Get sample config fails in detail first
        """
        templates = self.sample_templates
        if templates==[]:
            print 'No parts templates so check parts for each switch type tests are skipped'
        results = []
        device = self.get_device(self.device_name)
        assert device            
        for template_parts in templates:
            fails = []
            parts = os.listdir(template_parts)
            if parts:
                if self.many_devices:
                    device = self.get_device(template_parts)
                for template in parts:
                    fail = self._load_template(device, os.path.join(template_parts, template), 'normal')
                    if fail:
                        fails.extend(fail)
            else:
                raise Exception('No template found in parts directory for %s' % template_parts)
            # commit check after all parts loaded        
            fail = self._commit_template(device, os.path.join(template_parts, template))
            if fail:
                fails.extend(fail)
            if fails:
                results.extend(fails)
                results.append(self.marker)
                # Fail at first failing set of parts templates
                if self.fail_fast:
                    report = self.report(fails)
                    assert not fails, 'Check of parts for sample %s template failed' % template_parts.split('/')[-1]
        report = self.report(results)
            # If our sample's are failing for parts, likely all will fail - so fail fast for check all
            # self.fail_fast = True
        if report.count(' FAIL')==0:
               print '%s load and %s commit fails were found' % (report.count('LOAD FAIL'),
               report.count('COMMIT FAIL'))

    def check_config_diff(self):
        """Load the config to the each sample device and confirm that they are the correct host and 
           that there is no diff between the candidate and host config
           Note: this should fail for the single vendor switch VMs 
        """
        templates = self.list_templates(sample=True, parts=False)
        results = []
        for template in templates:
            try:
                device = self.get_device(template)
            except Exception, connect_error:
                results.append('Device Connect FAIL: %s - %s' % (self._get_device_name(template), connect_error))
            template_hostname = self._get_device_name(template).split('.')[0]
            if self._load_template(device, template, 'normal'):
                results.append('Could not config diff device due to load error for %s' % template_hostname)
            else:
                fulldiff = device.cu.diff()
                match = '+  host-name'  
                if fulldiff.find(match)>-1:
                    hostname = fulldiff.split(match)[1]
                    hostname = hostname.split(';', 1)[0]
                    results.append('Config being loaded is %s not the correct one for this host: %s' % (template_hostname,
                                                                                                        hostname))
        report = self.report(results) 
        if not report.count(' FAIL'):
            print '%s load and %s commit fails were found' % (report.count('LOAD FAIL'),
                                                                     report.count('COMMIT FAIL'))
        
    def commit_check_normal(self):
        """Load and commit check every composite config - fail fast by default"""
        self.check_templates(self.templates, 'normal')

        
