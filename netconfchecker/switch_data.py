"""
Wrapper to parse any switch format file or files into a nested dictionary for data analysis 

Just give it the path to the file or folder of files holding the switches config data and it should 
detect what format its dealing with and do the rest.
"""

import os
from datadiff.tools import assert_equal

from netconfchecker.juniper.conf_dict import JuniperDict


class SwitchData(object):
    """Generic class to detect switch data format and load it to Python data structure

       Plus diffdata wrapper method to diff two configs
    """
    config_suffixes = ['conf', 'config']
    parsers = {'juniper': JuniperDict,
               'cisco': None
               }
    
    def _load_config_file(self, file_path, switch_type='juniper'):
        """Load config from available switch types"""
        parser_class = self.parsers.get(switch_type, None)
        if parser_class:
            parser =  parser_class()
            return self._load_switch_config(file_path, switch_type, parser) 
        else:
            raise Exception('No parser available for switch type = %s' % switch_type)
        
    def _load_switch_config(self, file_path, switch_type, parser):
        """Load a switch config file using its custom parser"""
        with open(file_path) as conf_file:
            confstr = conf_file.read()
            confstr.strip()
            if len(confstr) > 4:
                try:
                    return parser.parse(confstr)
                except Exception as err:
                    self.errors.append('%s switch conf parse error - %s:\n%s' % (switch_type, err, confstr))
        return {}

    def _load_json(fullpath):
        """Load a json file"""
        with open(file_path) as conf_file:
            confstr = conf_file.read()
            confstr.strip()
            if len(confstr) > 1:
                try:
                    return json.loads(confstr)
                except Exception as err:
                    self.errors.append('%s switch conf parse error - %s:\n%s' % (switch_type, err, confstr))
        return {}
    
    def _get_file_data(self, full_path):
        """Determine the file format and load its data to a nested dict"""
        for suffix in self.config_suffixes:
            if full_path.endswith('.%s' % suffix) or full_path.find('.%s.' % suffix) > -1:
                return self._load_config_file(full_path)
        if full_path.endswith('.json'):
            return self._load_json(full_path)
        else:
            raise Exception('Do not know what format the data file is - %s' % full_path) 
    
    def get_data(self, full_path):
        """Only public method that gets data from a config file or directory
           
        Let OS errors be raised so if file doesnt exist just throw that - should be handled by calling code
        Otherwise see if its a file or folder of files and then parse any json or config files it finds
        """
        new = {}
        if os.path.isfile(full_path):
            return self._get_file_data(full_path)
        for part in os.listdir(full_path):
            conf = os.path.join(full_path, part)
            partdict = self._get_file_data(conf)
            if partdict:
                new.update(partdict)
        return new
    

    def diff_dict(self, old, new):
        """diff dict as assert equal

        Return the top level key diffs individually for easier debug, plus formatted msg
        So if this is empty ie False then test passes
        """
        diffs = {}
        try:
            assert_equal(old, new)
        except AssertionError, err:
            # diffs['all'] = err
            # Break down the diffs to each top level key
            for key in new:
                old_sub = old.get(key, None)
                try:
                    assert_equal(old_sub, new[key])
                except AssertionError, err:
                    diffs[key] = err
        msg = ''
        if diffs:
            for key, value in diffs.items():
                msg += '\n\n%s diff: %s' % (key, value)
        return diffs, msg
