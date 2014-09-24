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
import signal
import subprocess
from time import sleep
from udtc.tools import get_icon_path, get_launcher_path, launcher_exists_and_is_pinned
from ..tools import LoggedTestCase, local_which


class LargeFrameworkTests(LoggedTestCase):
    """Large framework base utilities"""

    def setUp(self):
        super().setUp()
        self.in_container = False
        self.installed_path = ""
        self.conf_path = os.path.expanduser("~/.config/udtc")
        self.desktop_filename = ""
        self.icon_filename = ""
        self.child = None

    def tearDown(self):
        # don't remove on machine paths if running within a container
        if not self.in_container:
            with suppress(FileNotFoundError):
                shutil.rmtree(self.installed_path)
            with suppress(FileNotFoundError):
                os.remove(self.conf_path)
            with suppress(FileNotFoundError):
                os.remove(get_launcher_path(self.desktop_filename))
            with suppress(FileNotFoundError):
                if self.icon_filename:
                    os.remove(get_icon_path(self.icon_filename))
        super().tearDown()

    def _pid_for(self, process_grep):
        """Return pid matching the process_grep elements"""
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

    def check_and_kill_process(self, process_grep, wait_before=0, send_sigkill=False):
        """Check a process matching process_grep exists and kill it"""
        sleep(wait_before)
        pid = self._pid_for(process_grep)
        if send_sigkill:
            os.kill(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGTERM)

    def assert_for_warn(self, content, expect_warn=False):
        """assert if there is any warn"""
        if not expect_warn:
            # We need to remove the first expected message, which is "Logging level set to "
            # (can be WARNING or ERROR)
            content = content.replace("Logging level set to WARNING", "").replace("Logging level set to ERROR", "")
            self.assertNotIn("WARNING", content)
            self.assertNotIn("ERROR", content)
        else:
            for warn_tag in ("WARNING", "ERROR"):
                if warn_tag in content:
                    break
            else:  # nothing found:
                raise BaseException("We didn't find an expected WARNING or ERROR in {}".format(content))

    def expect_and_no_warn(self, expect_query, timeout=-1, expect_warn=False):
        """run the expect query and check that there is no warning or error

        It doesn't fail on the given timeout if stdout is progressing"""
        output = ""
        continue_expect = True
        while(continue_expect):
            try:
                self.child.expect(expect_query, timeout=timeout)
                continue_expect = False
            except pexpect.TIMEOUT:
                # stalled during timeout period
                if output == self.child.before:
                    raise
                output = self.child.before
        self.assert_for_warn(self.child.before, expect_warn)

    def wait_and_no_warn(self, expect_warn=False):
        """run wait and check that there is no warning or error"""
        self.expect_and_no_warn(pexpect.EOF, expect_warn=expect_warn)

    def accept_default_and_wait(self, expect_warn=False):
        """accept default and wait for exiting"""
        self.child.sendline("")
        self.wait_and_no_warn(expect_warn)

    def command(self, commands_to_run):
        """passthrough, return args"""
        return commands_to_run

    def command_as_list(self, commands_input):
        """passthrough, return args"""
        return commands_input

    def launcher_exists_and_is_pinned(self, desktop_filename):
        """passthrough to in process method"""
        return launcher_exists_and_is_pinned(desktop_filename)

    def path_exists(self, path):
        """passthrough to os.path.exists"""
        return os.path.exists(path)

    def is_in_path(self, filename):
        """check that we have a directory in path"""
        return_code = subprocess.call(["bash", "-i", "which", filename], stdin=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if return_code == 0:
            return True
        elif return_code == 1:
            return False
        raise BaseException("Unknown return code for looking if {} is in path".format(filename))

    def create_file(self, path, content):
        """passthrough to create a file on the disk"""
        open(path, 'w').write(content)
