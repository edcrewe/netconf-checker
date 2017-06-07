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

from netconfchecker.juniper.manager import JuniperManager
from netconfchecker.config import DEVICES


class CommitCheck():
    """Test class for inputbuilder use A-Z module name prefix for sequence"""
    full_templates = []
    part_templates = []
    configs = []
    fail_fast = False
    marker = '----'
    many_devices = False
    
    def __init__(self, paths=[]):
        """
        Set up environment, fixtures and run functional cmd.

        All our tests check its outputs - and it takes a while, so lets just run it once.
        This is where you can setup things that you use throughout the tests. 
        This method is called before all tests
        """
        if not paths:
            print "You must supply one or more paths to the config files folder(s)"
            return
        # Setup templates
        self.paths = paths 
        self.get_templates(paths)
        # Setup device(s)
        self.device_name = os.environ.get('DEVICE', 'juniper') 
        self.juniper = JuniperManager()
        if not DEVICES.has_key(self.device_name):
            raise Exception('There is no config for device %s' % self.device_name)
        config = DEVICES[self.device_name]
        if config['host'] == 'FILENAME':
            self.many_devices = True
            for template in self.list_templates():
                config['host'] = self._get_device_name(template)
                try:
                    self.juniper.setup_device(config, config['host'])
                except:
                    pass
            if self.juniper.devices:
                self.juniper.devices[self.device_name] = self.juniper.devices[self.juniper.devices.keys()[0]]
        else:
            self.juniper.setup_device(config, self.device_name)
                
    def get_templates(self, paths):
        """Check we have got all the configs
           If there is one config per device they should be named by the device hostname with a suffix such as .conf
           If there is more than one config per device then they can be named whatever but should be in a folder named by the device hostname
           On that basis there are two lists of paths that should be handled, full or partial config ones
           If there are both types, then only if the full config load fails will the partial configs be checked
        """
        self.use_fixtures = False
        if self.use_fixtures:
            #FIXME - Note this can remove templates that were built by other means - be better to use different path for fixtures?
            if os.path.exists(self.path_parts):
                shutil.rmtree(self.path_parts)
            self.extract_fixture()

        self.list_templates(paths)
        
    def list_templates(self, paths):
        """run integrator build.sh (could skip final rpm part but it doesnt add much to the time so maybe just use build.sh)"""
        self.full_templates = []
        self.part_templates = []        
        for path in paths:
            for filefolder in os.listdir(path):
                if filefolder.startswith('.') or filefolder.endswith('~'):
                    continue
                fullpath = os.path.join(path, filefolder)
                if os.path.isdir(fullpath):
                    self.part_templates.append(fullpath)
                else:
                    self.full_templates.append(fullpath)
        return
        
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
        vendor, fmt = self.get_config_type(template)
        manager = None
        load_error = None
        if vendor:
            if vendor == 'empty':
                load_error = 'Template %s is empty so it is not loaded' % template_name
            else:
                manager = getattr(self, vendor, None)
        else:
            load_error = 'Cannot determine vendor from template %s' % vendor
        if not manager:
            if not load_error:
                load_error = 'Cannot load template %s to device - it is for %s - there is no device manager for %s' % (template_name, vendor, vendor)
        else:
            try:
                manager.close_device_config(device)
            except:
                pass
            try:
                load_error = manager.load_template_config(device, template, fmt, mode) 
            except ConnectClosedError, err: 
                manager.open_device_config(device) 
                load_error = manager.load_template_config(device, template, fmt, mode)
        if load_error:
            results.append('LOAD FAIL %s: %s' % (device.facts['hostname'], template_name))
            results.append(load_error)
        return results
    
    def _commit_template(self, device, template, check_only=True):
        results = []
        commit_error = self.juniper.commit_template_config(device, check_only)
        if commit_error:
            results.append('COMMIT FAIL %s: %s' % (device.facts['hostname'], template))
            results.append(commit_error)
        try:
            self.juniper.close_device_config(device)
        except:
            pass
        return results

    def get_config_type(self, template):
        """Work out the type of the config and the vendor"""
        config = None
        if os.path.exists(template):
            with open(template) as fileh:
                config = fileh.read()
                config = config.strip()
        if not config:
            return 'empty', None
        else:
            ### Check for native conf formats first ... its quicker
            if config.startswith('{') or config.startswith('['):
                if config.find("juniper") > -1:
                    return "juniper", "json"
                elif config.find("cisco") > -1:
                    return "cisco", "json"
                else:
                    return "unknown", "json"
            # TODO try full json, yaml and jxmlease load and then find vendor identifiers
            # note that this is not straight forward since it could be Yang or Native but in any of these formats
            if config.startswith("<"):
                if config.find("xmlns:junos") > -1:
                    return "juniper", "xml"
                else:
                    return "unknown", "xml"
            if config.find('{') > -1:
               return "juniper", "text"
            if config.count("!\n") > 1 or config.count(" - ") > -1:
                return "cisco", "text"
            # DEBUG: return config, "unknown"
        return None, None
            
    @staticmethod
    def _get_device_name(template):
        """Assume that full configs are host_name.ext so remove the extension
           Partial configs are in a folder named as host_name so just return it
        """
        if template.find('/') > -1:
            pathlist = template.split('/')
            return '.'.join(pathlist[-1].split('.')[-1])
        else:
            return template
        
    def get_device(self, name=''):
        """Connect to named device if supplied else test everything on same device"""
        if name:
            name = self._get_device_name(name)
        else:
            name = self.device_name
        # Assume if there is no specific device related to a template name, just load to the default test device
        if not self.juniper.devices.has_key(name):
            name = self.device_name
        device = self.juniper.devices[name] 
        # Use cu attribute as a marker that the device is already open ... if no cu, open it
        # if not hasattr(device, 'cu'):
        try:
            connect_error = self.juniper.open_device_config(device)
        except Exception, connect_error:
            pass
        if connect_error:
            raise Exception(connect_error)
        return device

    def check_templates(self, templates, mode='normal', skip=[], parts=False):
        """Run a check of all templates passed in using the config edit mode specified"""
        results = []
        passed = []
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
            device_name = self._get_device_name(template)
            if device_name not in skip:
                if self.many_devices:
                    try:
                        device = self.get_device(template)
                        # results.append('Device Connect SUCCESS: %s' % device.facts['hostname'])
                    except Exception, connect_error:
                        results.append('Device Connect FAIL: %s - %s' % (device_name, connect_error))
                        continue # Do not try and load to different device if many_devices test
                if parts:
                    part_templates = [os.path.join(template, tmpl) for tmpl in os.listdir(template)]
                else:
                    part_templates = [template]
                for template in part_templates:
                    fails = self.check_template(device, template, mode)
                    if fails:
                        results.extend(fails)
                        results.append(self.marker)
                        if self.fail_fast:
                            assert not fails
                    else:
                        if not parts:
                            passed.append(device_name)
        report = self.report(results)
        if parts:
            conf_type = "%s devices partial" % len(self.part_templates)
        else:
            conf_type = "%s devices full" % len(self.full_templates)
        if report.count(' FAIL')==0:
            print "All %s configs passed load and commit checks" % conf_type
        else:
            print 'For %s configs %s load and %s commit fails were found' % (conf_type,
                                                                             report.count('LOAD FAIL'),
                                                                             report.count('COMMIT FAIL'))
        return passed
            
    def run(self):
        """Run the full process of load and commit check and diff if available for report"""
        self.check_templates_available()
        self.check_device_available()
        passed = self.check_templates(self.full_templates)
        if self.part_templates:
            print self.marker
            self.check_templates(self.part_templates, skip=passed, parts=True)
        
    def check_templates_available(self):
        """Test that the templates are ready for loading

        Note we may always have templates from fixture
        so to check if build works, count sample parts tmp folders
        """
        assert len(self.full_templates) + len(self.part_templates)>1, 'Should be at least 2 templates found to load and check at %s' % self.paths
    
    def check_device_available(self):
        """Test that we can connect to the device being used for commit checking"""
        try:
            device = self.get_device()
            connect_error = None
        except Exception, connect_error:
            pass
        assert not connect_error, connect_error
        try:
            success, info = self.juniper.summary_info(device)
        except Exception, err:
            info = err
            success = False
        assert success, info
        # DEBUG raise Exception(info)
        if not success:
            raise Exception(info)
    
    def check_parts_for_switch_types(self, skip=[], types=['-leaf-', '-spine-', '-fabric-', '-dci-', '-tr-']):
        """Load and commit check each part of each type of config 
           Assumes that the switches have host names with an identifying type in them
           Use to get sample config fails in detail first
        """
        templates = []
        for tmpl_type in self.tmpl_types:
            for template in self.part_templates:
                if template.find('%s' % tmpl_type) > -1:
                    templates.append(template)
                    break
        if templates==[]:
            print 'No parts templates match the supplied types, so check parts for each switch type tests are skipped'
        results = []
        device = self.get_device(self.device_name)
        for template_parts in templates:
            if template_parts not in skip:
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
        

        
