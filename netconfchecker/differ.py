#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_diff_switches
----------------------------------
Tests for diff of outputs from two different commits of netconf-generator
"""
import logging
import os
import shutil
import time

from netconfchecker.switch_data import SwitchData

LOGGER_BASENAME='generator_diff'

class DiffCheck():
    """Check the difference between two versions of a config file - 
       without recourse to device VM or other vendor specific overhead.
    """

    def __init__(self, src, target, match='exact'):
        """Point to two locations for conf comparison
           Expect folders and replicated file structure, but can just use two files also
        """
        self.src = src
        self.target = target
        self.match = match
        self.switch = SwitchData()
        self.logfile =  'switchdiff.log' 
        
    def compare_templates(self, match='exact'):
        """Compare templates for commit1 and commit2 (src and target) for specified step - eg. switches, firewall or dhcp"""
        fail_msg = ''
        flag_matched = 0
        if match == 'exact':
            # Test full run of all templates from LA are in NG and are exactly the same - not sure this will ever be the case!
            if os.path.isdir(self.src):
                src_switches = os.listdir(self.src)
                target_switches = os.listdir(self.target)
                # First test we created the same number of templates
                assert len(src_switches)==len(target_switches)
                # Now diff them if we get past that test ...
                for tmpl in src_switches:
                    src_tmpl = os.path.join(self.src, tmpl)
                    target_tmpl = os.path.join(self.target, tmpl)
                    src = self.switch.get_data(src_tmpl)
                    if os.path.exists(target_tmpl):
                        flag_matched += 1
                        target = self.switch.get_data(target_tmpl)
                        diffs, msg = self.switch.diff_dict(src, target)
                        fail_msg += msg
                if not flag_matched:
                    fail_msg += 'We didnt match any configs between new and fixtures'
            else:
                src = self.switch.get_data(self.src)
                target = self.switch.get_data(self.target)
                diffs, fail_msg = self.switch.diff_dict(src, target)
        if not fail_msg:
            self.write_log('\nPASS: Switches step - Matched %s switch configs' % flag_matched)
        return fail_msg
            
    def write_log(self, msg):
        with open(self.logfile, 'a+') as logfh:
            logfh.write('%s\n' % msg)

    def run(self):
        """Run switches for commit 2 and check outputs are created"""
        diff = self.compare_templates(self.match)
        if diff:
            self.write_log('\n### test_106 Diff found for switches step ###\n %s' % diff)
        assert not diff, '\n\n### test_106 Diff found for database at racks step written to %s ###\n' % self.logfile

