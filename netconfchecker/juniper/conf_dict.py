"""
 JuniperDict builds a nested hash out of a juniper
 configuration file.

 Usage:
 import juniper_dict
 dict_config = JuniperDict.get_dict(open('juniper.conf').read())
 text_config = JuniperDict.build_config_from_dict(dict_config)
 JuniperDict.get_dict(text_config) == dict_config
 => true


  Copyright (C) 2017, Ed Crewe
  - Lifted from the Ruby version JuniperDict 2015 by Sven Tantau <sven@beastiebytes.com>
"""


class JuniperDict(object):
    """Takes a string and returns a nested dict"""

    def islist(self, obj):
        return isinstance(obj, list) and not isinstance(obj, basestring)
    
    def parse(self, content_string):
        """Main method that turns config into a python dict""" 
        lines_list = content_string.split("\n")
        # remove the comments
        comment_free_lines_list = [line for line in lines_list if not line.startswith('#')]
        # do the work:
        return self.format_blocks_to_dict(comment_free_lines_list)

    def build_config_from_dict(self, block, name=None, level=0):
        """generate config from dict"""
        indent = ' ' * level
        out = ''
        if name:
            out = indent + name + " {\n"
            level += 1
        indent = '  ' * level
        for key, value in block.items():
            if value:
                 if isinstance(value, basestring):
                     out += indent + key + ' ' + value + ";\n"
                 elif isinstance(value, list):
                     value.sort()
                     for val in value:
                         out += indent + key + ' ' + val + ";\n"
                 elif isinstance(value, dict):
                     out += self.build_config_from_dict(value, key, level)
                 else:
                     out += indent + key + ' ' + str(value) + ";\n"                     
            else:
                 out += indent + key + ";\n"
        if name:
            level -= 1
            indent='  ' * level
            out += indent + "}\n"
        return out

    def extract_key_value_from_line(self, line):
        """Break up into key and value"""
        try:
            key, value = line.split(' ', 1)
        except:
            key = line
            value = ''
        key = key.strip()
        key = key.replace(';', '')
        value = value.strip()
        value = value.replace(';', '')        
        return [key, value]

    def extract_blocks_from_block(self, lines_list):
        output = {}
        brace_depth = 0
        target_found = False
        block_name = None
        
        for line in lines_list:
            line = line.strip()
            if not line:
                continue
            # fill array with lines to store a new block
            if target_found:
                output[block_name].append(line)
            if line.find('{') > -1:
                brace_depth += 1
            if line.find('}') > -1:
                brace_depth -= 1

            if brace_depth == 1 and not target_found:
                # found a block
                block_name = line.replace('{', '').strip()
                ## set to new list of lines for a block ... unless its a repeated block (exists already) 
                output[block_name] = output.get(block_name, [])
                target_found = True

            if brace_depth == 0:
                if not line.find('}') > -1:
                    # 'key value' row found
                    key, value = self.extract_key_value_from_line(line)
                    if key in output:
                        if self.islist(output[key]):
                            output[key].append(value)
                        else:
                            # transform to array
                            output[key]=[output[key]]
                            output[key].append(value)
                    else:
                        output[key]=value
                target_found = False
        return output

    def format_blocks_to_dict(self, lines_list, key=None):
        """build the dict (main function) from an array of each line in the conf line"""
        out={}

        if not self.islist(lines_list):
            return lines_list
        else:
            # recursive func if its a list already
            lines_str = ''.join(lines_list)
            if lines_str.find("{") > -1 or lines_str.find("}") > -1:
                if lines_str.find("}") > -1:
                    blocks = self.extract_blocks_from_block(lines_list)
                    for bkey, l_list in blocks.items():
                        out[bkey] = self.format_blocks_to_dict(l_list, bkey)
                else:
                    for line in lines_list:
                        if line.find("}") == -1:
                            key, value = self.extract_key_value_from_line(line)
                            if key in out:
                                if self.islist(out[key]):
                                    out[key].append(value)
                                else:
                                    # transform to array
                                    out[key] = [out[key]]
                                    out[key].append(value)
                            else:
                                out[key] = value
            else:
                return lines_list                
        return out
