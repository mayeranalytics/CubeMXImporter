#!/usr/bin/env python
"""Dump the user code sections for all files in file tree.

The output will look something like this:
************************** my_project/src/main.c **************************
>36: USER CODE 'Includes'
#include "my_project.h"
// Etc.
********************** my_project/src/stm32l4xx_it.c **********************
>38: USER CODE '0'
// my code 1
>84: USER CODE 'EXTI4_IRQn 1'
// my code 2
// Etc.
"""

import argparse
import sys
from classes.UserCodeReplacer import UserCodeReplacer


def make_header(str):
    """Turn str into *** str *** in a nice way."""
    l = len(str)
    m = (80-l)/2
    return "*"*m + " " + str + " " + "*"*m


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawTextHelpFormatter
)

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
