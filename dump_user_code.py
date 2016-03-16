#!/usr/bin/env python
""" Use dump_user_code.py to dump the user code sections for all
    files in a eclipse project. """

import argparse
import sys
from classes.UserCodeReplacer import UserCodeReplacer

def make_header(str):
    """ Turns str into *** str *** in a nice way """
    l = len(str)
    m = (80-l)/2
    return "*"*m + " " + str + " " + "*"*m


parser = argparse.ArgumentParser(description=__doc__)

parser.add_argument('eclipse_path', metavar='eclipse_project_folder', type=str,
                   help='Path to the eclipse project')

args = parser.parse_args()

replacer = UserCodeReplacer(args)
all_user_code = replacer.parse()
for fname, user_code_map in all_user_code.iteritems():
    print(make_header(fname))
    for section_name, (user_code, line_no) in user_code_map.iteritems():
        print(">{}: USER CODE '{}'".format(line_no, section_name))
        sys.stdout.write(user_code)
