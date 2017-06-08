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
        """Compare templates for src and target, eg commit1 and commit2, for specified step - eg. switches, firewall or dhcp"""
        fail_msg = ''
        count_matched = 0
        count_failed = 0
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
                        count_matched += 1
                        target = self.switch.get_data(target_tmpl)
                        diffs, msg = self.switch.diff_dict(src, target)
                        fail_msg += msg
                        if diffs:
                            count_failed += 1
                if not count_matched:
                    fail_msg += 'We didnt match any configs between %s and %s' % (self.src, self.target)
            else:
                count_matched = 1
                src = self.switch.get_data(self.src)
                target = self.switch.get_data(self.target)
                diffs, fail_msg = self.switch.diff_dict(src, target)
                if diffs:
                    count_failed = 1
        if fail_msg:
            msg = 'FAIL: Failed to match %s pairs of %s configs' % (count_failed, count_matched)
        else:
            msg = 'PASS: Matched %s pairs of configs' % count_matched
        self.write_log(msg + fail_msg)
        return msg
            
    def write_log(self, msg):
        with open(self.logfile, 'a+') as logfh:
            logfh.write('%s\n' % msg)

    def run(self):
        """Run switches for commit 2 and check outputs are created"""
        print self.compare_templates(self.match)
        print "See the log at %s" % self.logfile 
