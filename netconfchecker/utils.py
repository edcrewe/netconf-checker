#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Class with general utilities useful for testing that are not complex enough to warrant a separate class

Currently this hold two file related utils - untar to extract big fixtures and file / text diff
to replace proper database comparison (ie mysqlutils) ... if its not available.
"""

import os
import tarfile

__author__ = 'Ed Crewe <edmundcrewe@gmail.com>'
__docformat__ = 'plaintext'
__date__ = '2016-01-25'


class Utils(object):
    """Test utils such as ile comparison and fixture extraction"""
    
    tarbutts = ('.tgz', 'tar.gz')

    def untar(self, tarball):
        """Use tarred sql in git for fixtures - since a bit big otherwise"""
        for file_ext in self.tarbutts:
            if tarball.endswith(file_ext):
                new_file = tarball[:-len(file_ext)]
                if os.path.exists(new_file):
                    os.remove(new_file)
                tar = tarfile.open(tarball)
                tar.extractall(path=os.path.dirname(new_file))
                tar.close()
                if os.path.exists(new_file):
                    return new_file
                else:
                    raise Exception('Failed to extract tarball')
        return tarball

    def diff_files(self, *args):
        """Open files first"""
        texts = []
        for path in args:
            with open(path) as fileh:
                texts.append(fileh.read())
        return self.diff_text(*texts)
                
    def diff_text(self, *args):
        """Pass in a list of big strings to compare lines same in any order duplicates ignored - first is master

        If used for SQL files then it means that the resulting database may be the same ... 
        but none of the accuracy of a proper dbcompare
        """
        lines = []
        output = ''
        if len(args) < 2:
            raise Exception('need at least two texts to compare')
        for text in args:
            lines.append(set(text.split('\n')))
        masterset = lines[0]
        difflimit = 10000
        for i, lineset in enumerate(lines[1:]):
            diff = ''
            missing = masterset - lineset
            extra = lineset - masterset
            num_misses = len(missing)
            num_extras = len(extra)
            # If the schema changes or a data value is quoted / unquoted then every insert will differ
            # there is no point reporting all of these so have a difflimit beyond which we dont both showing all the lines differing
            if num_misses > difflimit:
                if num_extras > difflimit:
                    return 'FAIL: Database diff = Aborted full diff logging because there has been a schema or data type change and all rows in a table have changed slightly ie. more than %s rows different' % difflimit
                elif num_extras < 10:
                    return 'FAIL: Database diff = Aborted full diff logging because file %s is missing most of the data compared to file 1' % i + 2
            if num_misses < 10 and num_extras > difflimit:
                return 'FAIL: Database diff = Aborted full diff logging because File 1 is missing most of the data compared to file %s' % i + 2
            if missing:
                for line in missing:
                    diff += '-- %s\n' % line
            if extra:
                for line in extra:
                    diff += '++ %s\n' % line
            if diff:
                output += '----- FAIL: Log of diff between file 1 and file %s ------\n%s' % (i + 2, diff) 
        return output
