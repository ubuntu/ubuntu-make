# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Didier Roche
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""Basic large tests class"""

from contextlib import suppress
import os
import pexpect
import shutil
from time import sleep
from udtc.tools import get_launcher_path
from unittest import TestCase


class LargeFrameworkTests(TestCase):
    """This will test the Android Studio base"""

    def setUp(self):
        super().setUp()
        self.installed_path = ""
        self.conf_path = os.path.expanduser("~/.config/udtc")
        self.launcher_path = ""
        self.child = None

    def tearDown(self):
        with suppress(FileNotFoundError):
            shutil.rmtree(self.installed_path)
        with suppress(FileNotFoundError):
            os.remove(self.conf_path)
        with suppress(FileNotFoundError):
            os.remove(get_launcher_path(self.launcher_path))
        super().tearDown()

    def pid_for(self, process_grep, wait_before=0):
        """Return pid matching the process_grep elements"""
        sleep(wait_before)
        for pid in os.listdir('/proc'):
            if not pid.isdigit():
                continue
            # ignore processes that are closed in between
            with suppress(IOError):
                cmdline = open(os.path.join('/proc', pid, 'cmdline'), 'r').read()
                for process_elem in process_grep:
                    if process_elem not in cmdline:
                        break
                # we found it
                else:
                    return int(pid)
        raise BaseException("The process that we can find with {} isn't started".format(process_grep))

    def assert_for_warn(self, content, expect_warn=False):
        """assert if there is any warn"""
        if not expect_warn:
            self.assertNotIn("WARNING", content)
            self.assertNotIn("ERROR", content)
        else:
            for warn_tag in ("WARNING", "ERROR"):
                if warn_tag in content:
                    break
            else:  # nothing found:
                raise BaseException("We didn't find an expected WARNING or ERROR in {}".format(content))

    def expect_and_no_warn(self, expect_query, timeout=-1, expect_warn=False):
        """run the expect query and check that there is no warning or error"""
        self.child.expect(expect_query, timeout=timeout)
        self.assert_for_warn(self.child.before, expect_warn)

    def wait_and_no_warn(self, expect_warn=False):
        """run wait and check that there is no warning or error"""
        self.expect_and_no_warn(pexpect.EOF, expect_warn=expect_warn)

    def accept_default_and_wait(self, expect_warn=False):
        """accept default and wait for exiting"""
        self.child.sendline("")
        self.wait_and_no_warn(expect_warn)

    @property
    def exec_path(self):
        return os.path.join(self.installed_path, "bin", "studio.sh")
