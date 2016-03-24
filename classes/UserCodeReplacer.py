#!/usr/bin/env python
"""Class UserCodeReplacer."""

import os
import sys
import re
from collections import OrderedDict


class UserCodeReplacer:
    """This class extracts and replaces user code in STM32CubeMX projects.

    Specifically, it can do the following two things:
    - Parse the file tree of an Eclipse project, extract and store
      the user code
    - Parse the file tree of an Eclipse project an re-insert the user code
    """

    filetypes = set(['.c', '.cpp', '.cxx', '.cc', '.h', '.hpp', '.hxx', '.hh'])
    __re_user_code_begin = re.compile(r'^\s*/\* USER CODE BEGIN (.*) \*/\s*$')
    __re_user_code_end = re.compile(r'^\s*/\* USER CODE END (.*) \*/\s*$')
    __re_empty_text = re.compile(r'^\s*$')

    def __init__(self, args):
        """Init the class, extract some params from args."""
        self.eclipse_path = args.eclipse_path

    @staticmethod
    def dir_walker(path):
        """Iterator over all the files under path having suitable extension.

        Specifically, it iterates over all files with filetype in
        UserCodeReplacer.filetypes
        """
        for subdir, dirs, files in os.walk(path):
            for fname in files:
                fpath = os.path.join(subdir, fname)
                if os.path.splitext(fpath)[1] in UserCodeReplacer.filetypes:
                    yield fpath

    @staticmethod
    def make_backup_fpath(fpath):
        """Return a file path that is a good name for a backup file.

        I.e. the path /x/y/some.c will turn into /x/y/.some.c.1,
        unless that file already exists. In that case it will turn into
        /x/y/.some.c.2. Etc.
        """
        while True:
            head, tail = os.path.split(fpath)
            fname, ext = os.path.splitext(tail)
            ext = ext.lstrip('.')
            if not ext:
                ext = '1'
            else:
                try:
                    ext = str(1+int(ext))
                except ValueError:
                    ext = ext+".1"
            if fname[0] != '.':
                fname = "." + fname
            fpath = os.path.join(head, fname+"."+ext)
            if not os.path.isfile(fpath):
                break
        return fpath

    def parse(self):
        """Do the parse as advertised.

        I.e. go through all the files in the Eclipse project dir and
        extract the user code.
        :returns: OrderedDict file_path => section_map where section_map is a
            OrderedDict of section_name => user_code.
        """
        all_user_code = OrderedDict()       # a map filename->__parse() result
        for fpath in UserCodeReplacer.dir_walker(self.eclipse_path):
            parse_result = self.__parse(fpath)
            if parse_result:
                all_user_code[fpath] = parse_result
        return all_user_code

    def insert(self, all_user_code, do_backup=True):
        """Do the re-insert as advertised.

        I.e. go through all the files in the Eclipse project dir and insert
        the user code in the right section in the right file.
        Backups will be done on all files that have user code in them.
        (See the make_backup_fpath function for details on how the filename
        is constructed.)
        :param all_user_code: The dict returned by parse()
        :param do_backup: Bool to switch the backup feature on/off.
            Default is on.
        """
        all_files = [
            fpath for fpath in UserCodeReplacer.dir_walker(self.eclipse_path)
            if fpath in all_user_code
            ]
        for fpath in all_files:
            new_file_content = self.__parse(fpath, all_user_code[fpath])
            if do_backup:
                # backup the original file
                backup_fpath = UserCodeReplacer.make_backup_fpath(fpath)
                # make a backup of the file by renming it
                os.rename(fpath, backup_fpath)
                sys.stderr.write("Renamed {} -> {}\n".format(fpath, backup_fpath))
            # now we overwrite the file!!
            with open(fpath, 'w') as file:
                file.write(new_file_content)
                sys.stderr.write("Inserted into {}\n".format(fpath))
            del all_user_code[fpath]
        # if there's still something left in all_user_code we write it again:
        for fpath in all_user_code:
            with open(fpath, 'w') as file:
                for section_name, (user_code, lineno) in all_user_code[fpath].iteritems():
                    file.write("/* USER CODE BEGIN {} */\n".format(section_name))
                    file.write(user_code)
                    file.write("/* USER CODE END {} */\n".format(section_name))
            print("Wrote user section(s) to {}".format(fpath))

    def __parse(self, fname, user_code_map=None):
        """Do the actual parsing/inserting.

        This function will be called by parse() and insert().
        So there are two modes:
        1. Parse: When user_code_map==None the file is parsed and the
            user_code_map is returned.
        2. Insert: When user_code_map is not None the file is parsed and
            the new file content is built up by inserting the user code
            stored in user_code_map. The resulting new file content is
            returned.
        """
        file = open(fname, 'r')

        do_insert = user_code_map is not None   # this bool identifies the mode
        if user_code_map is None:
            # user_code_map will be a dict of section_name => user_code
            user_code_map = OrderedDict()

        # state variables
        state = 'sys'               # state can be 'sys' or 'user'
        line_no = 0                 # current line number in file
        line_no_start = None        # line no where the current section started
        begin_section_name = None
        end_section_name = None
        previous_begin_section_name = None   # previous section name for errors
        current_section_user_code = ''
        new_file_content = ''    # only actually needed when do_insert == True

        for line in file:
            line_no += 1

            re_begin = UserCodeReplacer.__re_user_code_begin.match(line)
            re_end = UserCodeReplacer.__re_user_code_end.match(line)

            if re_begin is not None and re_end is not None:
                # Let's test for it although it should never happen
                sys.stderr.write("Internal Error!\n")
                sys.exit(1)

            # now we have three cases:
            # 1. the line is a /* USER CODE BEGIN <section_name> */ line
            # 2. the line contains the user code in between
            # 3. the line is a /* USER CODE END <section_name> */ line
            # 4. the line contains the system code

            if re_begin is not None:
                # case 1: /* USER CODE BEGIN <section_name> */
                previous_begin_section_name = begin_section_name
                begin_section_name = re_begin.group(1)
                if state != 'sys':
                    sys.stderr.write(
                        "Error in {} line {}: 'USER CODE BEGIN {}' \
                        inside 'USER CODE BEGIN {}'\n".format(
                            fname, line_no, begin_section_name,
                            previous_begin_section_name
                        ))
                    sys.exit(1)
                else:
                    new_file_content += line
                    # change state variables
                    state = 'user'
                    current_section_user_code = ''
                    line_no_start = line_no
                    end_section_name = None

            elif re_end is not None:
                # case 3: /* USER CODE END <section_name> */
                end_section_name = re_end.group(1)

                if state != 'user' or end_section_name != begin_section_name:
                    sys.stderr.write(
                        "Error in {} line {}: 'USER CODE END {}' \
                        not preceded by 'USER CODE BEGIN {}'\n".format(
                            fname, line_no, end_section_name, end_section_name
                        ))
                    sys.exit(1)

                if do_insert:
                    inserted_text, inserted_lineno = user_code_map.get(end_section_name, (None, None))
                    if inserted_text is not None:
                        del user_code_map[end_section_name]
                        new_file_content += inserted_text
                        if re.match("^\s*$", inserted_text) is None:
                            print("{}:{} Inserted USER CODE '{}'".format(fname, inserted_lineno, end_section_name))
                    else:
                        print("{}: Error: Section name '{}' not found".format(fname, end_section_name))
                else:
                    user_code_map[end_section_name] = \
                        (current_section_user_code, line_no_start)
                new_file_content += line
                # reset all state variables
                state = 'sys'
                end_section_name = begin_section_name = None
                current_section_user_code = ''
                line_no_start = None

            else:
                if state == 'user':     # case 2: It's user code in between
                    current_section_user_code += line
                else:                   # case 4: It's sys code
                    new_file_content += line
                continue

        file.close()
        # report any un-inserted user sections:
        if do_insert:
            for section_name, (text, line_no) in user_code_map.iteritems():
                print("{}:{} NOT Inserted USER CODE '{}'".format(fname, inserted_lineno, section_name))

        # recall that the return type is different for the two parsing modes
        return new_file_content if do_insert else user_code_map
