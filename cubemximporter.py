#!/usr/bin/python

# Copyright (c) 2015 Carmine Noviello
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function

version = 0.2

import os
import sys
import argparse
import copy
import logging
import shutil
import re
from lxml import etree
from classes.CubeMXImporter import CubeMXImporter
from classes.UserCodeReplacer import UserCodeReplacer


def make_header(str):
    """ Turns str into *** str *** in a nice way """
    l = len(str)
    m = (80-l)/2
    return "*"*m + " " + str + " " + "*"*m


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import a STM32CubeMX generated project inside an existing Eclipse project generated with the GNU ARM plugin')

    parser.add_argument('eclipse_path', metavar='eclipse_project_folder', type=str,
                       help='Path to the Eclipse project')

    parser.add_argument('cubemx_path', metavar='cubemx_project_folder', type=str,
                       help='Path to the STM32CubeMX project')

    parser.add_argument('-v', '--verbose', type=int, action='store', default=1,
                       help='Verbosity level: 1=Error (default), 2=Info, 3=Debug')

    parser.add_argument('--dryrun', action='store_true',
                       help="Don't perform any operations - for debug purposes")

    parser.add_argument('--dump', action='store_true',
                       help="Dump the user code sections")

    parser.add_argument('--insert', action='store_true',
                       help="Re-insert the user code sections into the Eclipse project code.")

    parser.add_argument('--no-backup', action='store_true', default=False,
                       help="Do NOT make a backup before re-inserting the user section code.")


    args = parser.parse_args()

    if args.verbose == 3:
        logging.basicConfig(level=logging.DEBUG)
    if args.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.ERROR)

    if args.dryrun and args.insert:
        sys.stderr.write("Error: The options --dryrun and --insert are not compatible.\n")
        sys.exit(1)

    if args.dump or args.insert:
        codeReplacer = UserCodeReplacer(args)
        all_user_code = codeReplacer.parse()
        if args.dump:
            for fname, user_code_map in all_user_code.iteritems():
                print(make_header(fname))
                for section_name, (user_code, line_no) in user_code_map.iteritems():
                    print(">{}: USER CODE '{}'".format(line_no, section_name))
                    sys.stdout.write(user_code)

    cubeImporter =  CubeMXImporter()
    cubeImporter.setDryRun(args.dryrun)
    cubeImporter.eclipseProjectPath = args.eclipse_path
    cubeImporter.cubeMXProjectPath = args.cubemx_path
    cubeImporter.parseEclipseProjectFile()
    cubeImporter.deleteOriginalEclipseProjectFiles()
    cubeImporter.importApplication()
    cubeImporter.importHAL()
    cubeImporter.importCMSIS()
    cubeImporter.importMiddlewares()
    cubeImporter.saveEclipseProjectFile()
    # cubeImporter.addCIncludes(["../middlewares/freertos"])
    # cubeImporter.printEclipseProjectFile()

    if args.insert and not args.dryrun:
        codeReplacer.insert(all_user_code, do_backup=not args.no_backup)
