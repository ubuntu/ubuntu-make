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
from pytest import mark
import os
import pexpect
import shutil
import signal
import stat
import subprocess
from time import sleep
from umake.tools import get_icon_path, get_launcher_path, launcher_exists_and_is_pinned, remove_framework_envs_from_user
from ..tools import LoggedTestCase, get_path_from_desktop_file, is_in_group, INSTALL_DIR, swap_file_and_restore, \
    spawn_process, set_local_umake, BRANCH_TESTS
from umake.settings import DEFAULT_BINARY_LINK_PATH


class LargeFrameworkTests(LoggedTestCase):
    """Large framework base utilities"""

    in_container = False

    if not BRANCH_TESTS:
        set_local_umake()

    def setUp(self):
        super().setUp()
        self.installed_path = ""
        self.framework_name_for_profile = ""
        self.conf_path = os.path.expanduser("~/.config/umake")
        self.install_base_path = os.path.expanduser("~/{}".format(INSTALL_DIR))
        self.binary_dir = DEFAULT_BINARY_LINK_PATH
        self.desktop_filename = ""
        self.child = None
        self.additional_dirs = []
        self.original_env = os.environ.copy()
        # we want to standardize on bash environment for running large tests
        os.environ["SHELL"] = "/bin/bash"

    def tearDown(self):
        # don't remove on machine paths if running within a container
        if not self.in_container:
            with suppress(FileNotFoundError):
                shutil.rmtree(self.installed_path)
            # TODO: need to be finer grain in the future
            with suppress(FileNotFoundError):
                os.remove(self.conf_path)
            if self.desktop_filename:
                with suppress(FileNotFoundError):
                    os.remove(get_launcher_path(self.desktop_filename))
                    os.remove(self.exec_link)
            remove_framework_envs_from_user(self.framework_name_for_profile)
            for dir in self.additional_dirs:
                with suppress(OSError):
                    shutil.rmtree(dir)
        # restore original environment. Do not use the dict copy which erases the object and doesn't have the magical
        # _Environ which setenv() for subprocess
        os.environ.clear()
        os.environ.update(self.original_env)
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

    @property
    def exec_link(self):
        return os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])

    @property
    def exec_path(self):
        return self._get_path_from_desktop_file("TryExec")

    def _get_path_from_desktop_file(self, key, abspath_transform=None):
        """get the path referred as key in the desktop filename exists"""

        path = get_path_from_desktop_file(self.desktop_filename, key)
        if not path.startswith("/") and abspath_transform:
            path = abspath_transform(path)
        return path

    def assert_exec_exists(self):
        """Assert that the exec path exists"""
        assert self.path_exists(self.exec_path)

    def assert_icon_exists(self):
        """Assert that the icon path exists"""
        assert self.path_exists(self._get_path_from_desktop_file('Icon', get_icon_path))

    def assert_exec_link_exists(self):
        """Assert that the link to the binary exists"""
        assert self.is_in_path(self.exec_link)

    def assert_for_warn(self, content, expect_warn=False):
        """assert if there is any warn"""
        if not expect_warn:
            # We need to remove the first expected message, which is "Logging level set to "
            # (can be WARNING or ERROR)
            content = content.replace("Logging level set to WARNING", "").replace("Logging level set to ERROR", "")
            assert "WARNING" not in content
            assert "ERROR" not in content
        else:
            for warn_tag in ("WARNING", "ERROR"):
                if warn_tag in content:
                    break
            else:  # nothing found:
                raise BaseException("We didn't find an expected WARNING or ERROR in {}".format(content))

    def return_and_wait_expect(self, expect_query, timeout=-1):
        """run the expect query and return the result"""
        output = ""
        continue_expect = True
        while continue_expect:
            try:
                result = self.child.expect(expect_query, timeout=timeout)
                continue_expect = False
            except pexpect.TIMEOUT:
                # stalled during timeout period
                if output == self.child.before:
                    print(self.child.before)
                    raise
                output = self.child.before
            # print the whole process output before getting the pexpect exception
            except:
                print(self.child.before)
                raise
        return result

    def expect_and_no_warn(self, expect_query, timeout=-1, expect_warn=False):
        """run the expect query and check that there is no warning or error

        It doesn't fail on the given timeout if stdout is progressing"""
        self.return_and_wait_expect(expect_query, timeout)
        self.assert_for_warn(self.child.before, expect_warn)

    def wait_and_no_warn(self, expect_warn=False):
        """run wait and check that there is no warning or error"""
        self.expect_and_no_warn(pexpect.EOF, expect_warn=expect_warn)

    def accept_default_and_wait(self, expect_warn=False):
        """accept default and wait for exiting"""
        self.child.sendline("")
        self.wait_and_no_warn(expect_warn)

    def close_and_check_status(self, exit_status=0):
        """exit child process and check its exit status"""
        self.child.close()
        assert exit_status == self.child.exitstatus

    def wait_and_close(self, expect_warn=False, exit_status=0):
        """wait for exiting and check exit status"""
        self.wait_and_no_warn(expect_warn)
        self.close_and_check_status(exit_status)

    def command(self, commands_to_run):
        """passthrough, return args"""
        return commands_to_run

    def command_as_list(self, commands_input):
        """passthrough, return args"""
        return commands_input

    def get_launcher_path(self, desktop_filename):
        """passthrough getting the launcher path from umake tools"""
        return get_launcher_path(desktop_filename)

    def launcher_exists_and_is_pinned(self, desktop_filename):
        """passthrough to in process method"""
        return launcher_exists_and_is_pinned(desktop_filename)

    def path_exists(self, path):
        """passthrough to os.path.exists"""
        return os.path.exists(path)

    def remove_path(self, path):
        """Remove targeted path"""
        try:
            os.remove(path)
        except OSError:
            shutil.rmtree(path)

    def is_in_path(self, filename):
        """check that we have a directory in path"""
        return_code = subprocess.call(["bash", "-l", "which", filename], stdin=subprocess.DEVNULL,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if return_code == 0:
            return True
        elif return_code == 1:
            return False
        raise BaseException("Unknown return code for looking if {} is in path".format(filename))

    def is_in_group(self, group):
        """return if current user is in a group"""
        return is_in_group(group)

    def get_file_perms(self, path):
        """return unix file perms string for path"""
        return stat.filemode(os.stat(path).st_mode)

    def create_file(self, path, content):
        """passthrough to create a file on the disk"""
        open(path, 'w').write(content)

    @mark.skip(reason="Not a test")
    def bad_download_page_test(self, command, content_file_path):
        """Helper for running a test to confirm failure on a significantly changed download page."""
        with swap_file_and_restore(content_file_path):
            with open(content_file_path, "w") as newfile:
                newfile.write("foo")
            self.child = spawn_process(command)
            self.expect_and_no_warn(r"Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.wait_and_close(expect_warn=True, exit_status=1)
