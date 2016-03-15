#!/usr/bin/env python
""" Use find_user_code.py to dump the user code groups for all
    files in a eclipse project. """

import os
import argparse
import sys
import re
from collections import defaultdict, OrderedDict


class UserCodeReplacer:
    """ For now, this class does two things:
        - It parses the eclipse path, extracts and stores the user code
        - It prints the user code for each group for each file
    """

    filetypes = set(['.c', '.cpp', '.cxx', '.cc', '.h', '.hpp', '.hxx', '.hh'])
    __re_user_code_begin = re.compile(r'^\s*/\* USER CODE BEGIN (.*) \*/\s*$')
    __re_user_code_end = re.compile(r'^\s*/\* USER CODE END (.*) \*/\s*$')
    __re_empty_text = re.compile(r'^\s*$')

    def __init__(self, args):
        self.eclipse_path = args.eclipse_path
        self.cubemx_path = args.cubemx_path
        self.user_code_map = dict()

    def parse(self):
        all_user_code = OrderedDict()       # a map filename->__parse() results
        for subdir, dirs, files in os.walk(self.eclipse_path):
            for fname in files:
                full_fname = os.path.join(subdir, fname)
                if os.path.splitext(full_fname)[1] in UserCodeReplacer.filetypes:
                    result = self.__parse(full_fname)
                    if result:
                        all_user_code[fname] = result
                        print("***** {} *****".format(full_fname))
                        for group_name, (user_code, line_no) in result.iteritems():
                            print(">{}: USER CODE '{}'".format(line_no, group_name))
                            sys.stdout.write(user_code)

    def __parse(self, fname):
        """ This function does the actual parse """
        file = open(fname, 'r')

        # result will be a dict of group_name => user_code
        result = OrderedDict()

        # state variables
        state = 'sys'               # state can be 'sys' or 'user'
        line_no = 0                 # current line number in file
        line_no_start = None        # line no where the current group started
        begin_group_name = None
        end_group_name = None
        previous_begin_group_name = None    # only needed for error reporting
        this_user_code = ''

        for line in file:
            line_no += 1

            re_begin = UserCodeReplacer.__re_user_code_begin.match(line)
            re_end = UserCodeReplacer.__re_user_code_end.match(line)

            if re_begin is None and re_end is None:
                if state == 'user':
                    this_user_code += line
                continue

            if re_begin is not None:
                previous_begin_group_name = begin_group_name
                begin_group_name = re_begin.group(1)
                if state != 'sys':
                    sys.stderr.write("Error in {} line {}: 'USER CODE BEGIN {}' inside 'USER CODE BEGIN {}'\n".format(
                        fname, line_no, begin_group_name, previous_begin_group_name
                        ))
                    sys.exit(1)
                else:
                    state = 'user'
                    line_no_start = line_no
                    end_group_name = None

            if re_end is not None:
                end_group_name = re_end.group(1)
                if state != 'user' or end_group_name != begin_group_name:
                    sys.stderr.write("Error in {} line {}: 'USER CODE END {}' not preceded by 'USER CODE BEGIN {}'\n".format(
                        fname, line_no, end_group_name, end_group_name
                        ))
                    sys.exit(1)
                else:
                    if UserCodeReplacer.__re_empty_text.match(this_user_code) is None:
                        result[end_group_name] = [this_user_code, line_no_start]

                    # reset all state variables
                    state = 'sys'
                    end_group_name = begin_group_name = None
                    this_user_code = ''
                    line_no_start = None

        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('eclipse_path', metavar='eclipse_project_folder', type=str,
                       help='an integer for the accumulator')

    args = parser.parse_args()
    print(args)

    replacer = UserCodeReplacer(args)
    replacer.parse()
