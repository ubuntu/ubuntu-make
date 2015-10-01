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

"""Tests for basic CLI commands"""

import os
import pexpect
import subprocess
from ..tools import get_root_dir, get_tools_helper_dir, LoggedTestCase, get_docker_path, get_data_dir, \
    swap_file_and_restore
from time import sleep
from nose.tools import nottest


class ContainerTests(LoggedTestCase):
    """Container-based tests utilities"""

    DOCKER_USER = "user"
    DOCKER_PASSWORD = "user"
    DOCKER_TESTIMAGE = "didrocks/docker-umake-manual"
    UMAKE_IN_CONTAINER = "/umake"
    APT_FAKE_REPO_PATH = "/apt-fake-repo"

    def setUp(self):
        super().setUp()  # this will call other parents of ContainerTests ancestors, like LargeFrameworkTests
        self.in_container = True
        self.umake_path = get_root_dir()
        self.image_name = self.DOCKER_TESTIMAGE
        command = [get_docker_path(), "run"]
        runner_cmd = "mkdir -p {}; ln -s {}/ {};".format(os.path.dirname(get_root_dir()), self.UMAKE_IN_CONTAINER,
                                                         get_root_dir())

        # start the local server at container startup
        if hasattr(self, "hostnames"):
            ftp_redir = hasattr(self, 'ftp')
            for hostname in self.hostnames:
                if "-h" not in command:
                    command.extend(["-h", hostname])
                runner_cmd += 'sudo echo "127.0.0.1 {}" >> /etc/hosts;'.format(hostname)
            runner_cmd += "{} {} 'sudo -E env PATH={} VIRTUAL_ENV={} {} {} {} {}';".format(
                os.path.join(get_tools_helper_dir(), "run_in_umake_dir_async"),
                self.UMAKE_IN_CONTAINER,
                os.getenv("PATH"), os.getenv("VIRTUAL_ENV"),
                os.path.join(get_tools_helper_dir(), "run_local_server"),
                self.port,
                str(ftp_redir),
                " ".join(self.hostnames))

            if ftp_redir:
                runner_cmd += "/usr/bin/twistd ftp -p 21 -r {};".format(os.path.join(get_data_dir(), 'server-content',
                                                                                     self.hostnames[0]))

        if hasattr(self, "apt_repo_override_path"):
            runner_cmd += "sudo sh -c 'echo deb file:{} / > /etc/apt/sources.list';sudo apt-get update;".format(
                self.apt_repo_override_path)
        runner_cmd += "/usr/sbin/sshd -D"

        command.extend(["-d", "-v", "{}:{}".format(self.umake_path, self.UMAKE_IN_CONTAINER),
                        "--dns=8.8.8.8", "--dns=8.8.4.4",  # suppress local DNS warning
                        self.image_name,
                        'sh', '-c', runner_cmd])

        self.container_id = subprocess.check_output(command).decode("utf-8").strip()
        self.container_ip = subprocess.check_output([get_docker_path(), "inspect", "-f",
                                                     "{{ .NetworkSettings.IPAddress }}",
                                                     self.container_id]).decode("utf-8").strip()
        # override with container paths
        self.conf_path = os.path.expanduser("/home/{}/.config/umake".format(self.DOCKER_USER))
        sleep(5)  # let the container and service starts

    def tearDown(self):
        subprocess.check_call([get_docker_path(), "stop", "-t", "0", self.container_id],
                              stdout=subprocess.DEVNULL)
        subprocess.check_call([get_docker_path(), "rm", self.container_id], stdout=subprocess.DEVNULL)
        super().tearDown()  # this will call other parents of ContainerTests ancestors, like LargeFrameworkTests

    def command(self, commands_to_run):
        """Return a string for a command line ready to run in docker"""
        return " ".join(self.command_as_list(commands_to_run))

    def command_as_list(self, commands_to_run):
        """Return a list for a command line ready to run in docker"""

        if isinstance(commands_to_run, list):
            commands_to_run = " ".join(commands_to_run)
        return ["sshpass", "-p", self.DOCKER_PASSWORD, "ssh", "-o", "UserKnownHostsFile=/dev/null", "-o",
                "StrictHostKeyChecking=no", "-t", "-q",
                "{}@{}".format(self.DOCKER_USER, self.container_ip),
                "{} {} '{}'".format(os.path.join(get_tools_helper_dir(), "run_in_umake_dir"),
                                    self.UMAKE_IN_CONTAINER, commands_to_run)]

    def check_and_kill_process(self, process_grep, wait_before=0, send_sigkill=False):
        """Check a process matching process_grep exists and kill it"""
        sleep(wait_before)
        if not self._exec_command(self.command_as_list("{} {} {}".format(os.path.join(get_tools_helper_dir(),
                                                                                      "check_and_kill_process"),
                                                                         send_sigkill,
                                                                         " ".join(process_grep))))[0]:
            raise BaseException("The process we try to find and kill can't be found".format(process_grep))

    def _get_path_from_desktop_file(self, key, abspath_transform=None):
        """get the path referred as key in the desktop filename exists"""

        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "get_path_from_desktop_file"),
                                       self.desktop_filename, key])
        success, stdout, stderr = self._exec_command(command)
        if success:
            path = stdout
            if not path.startswith("/") and abspath_transform:
                path = abspath_transform(path)
        else:
            raise BaseException("Unknown failure from {}".format(command))
        return path

    def _exec_command(self, command):
        """Exec the required command inside the container, returns if it exited with 0 or 1 + stdout/stderr"""
        proc = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        (stdout, stderr) = proc.communicate()
        # convert in strings and remove remaining \n
        if stdout:
            stdout = stdout.decode("utf-8").strip()
        if stderr:
            stderr = stderr.decode("utf-8").strip()
        return_code = proc.returncode
        if return_code == 0:
            return (True, stdout, stderr)
        elif return_code == 1:
            return (False, stdout, stderr)
        raise BaseException("Unknown return code from {}".format(command))

    def launcher_exists_and_is_pinned(self, desktop_filename):
        """Check if launcher exists and is pinned inside the container"""
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "check_launcher_exists_and_is_pinned"),
                                        desktop_filename])
        return self._exec_command(command)[0]

    def path_exists(self, path):
        """Check if a path exists inside the container"""
        # replace current user home dir with container one.
        path = path.replace(os.environ['HOME'], "/home/{}".format(self.DOCKER_USER))
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "path_exists"), path])
        return self._exec_command(command)[0]

    def is_in_path(self, filename):
        """Check inside the container if filename is in PATH thanks to which"""
        return self._exec_command(self.command_as_list(["bash", "-l", "which", filename]))[0]

    def is_in_group(self, group):
        """Check inside the container if the user is in a group"""
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "check_user_in_group"), group])
        return self._exec_command(command)[0]

    def get_file_perms(self, path):
        """return unix file perms string for path from the container"""
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "get_file_perms"), path])
        success, stdout, stderr = self._exec_command(command)
        if success:
            return stdout
        else:
            raise BaseException("Unknown failure from {}".format(command))

    def create_file(self, path, content):
        """Create file inside the container.replace in path current user with the docker user"""
        path = path.replace(os.getlogin(), self.DOCKER_USER)
        dir_path = os.path.dirname(path)
        command = self.command_as_list(["mkdir", "-p", dir_path, path])
        if not self._exec_command(command)[0]:
            raise BaseException("Couldn't create {} in container".format(path))

    @nottest
    def bad_download_page_test(self, command, content_file_path):
        """Helper for running a test to confirm failure on a significantly changed download page."""
        with swap_file_and_restore(content_file_path):
            with open(content_file_path, "w") as newfile:
                newfile.write("foo")
            self.child = pexpect.spawnu(command)
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.wait_and_close(expect_warn=True, exit_status=1)
