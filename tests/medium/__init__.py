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
import signal
import subprocess
import tempfile
from udtc.tools import launcher_exists_and_is_pinned
import subprocess
from ..tools import get_root_dir, get_tools_helper_dir, LoggedTestCase
from udtc import settings


class ContainerTests(LoggedTestCase):
    """Container-based tests utilities"""

    def setUp(self):
        super().setUp()  # this will call other parents of ContainerTests ancestors, like LargeFrameworkTests
        self.in_container = True
        self.udtc_path = get_root_dir()
        self.image_name = settings.DOCKER_TESTIMAGE
        self.container_id = subprocess.check_output([settings.DOCKER_EXEC_NAME, "run", "-d", "-v",
                                                     "{}:{}".format(self.udtc_path, settings.UDTC_IN_CONTAINER),
                                                     self.image_name,
                                                     'sh', '-c',
                                                     'mkdir -p /home/didrocks/work && '
                                                     'ln -s /udtc /home/didrocks/work/ubuntu-developer-tools-center'
                                                     ' && /usr/sbin/sshd -D']).decode("utf-8").strip()
        self.container_ip = subprocess.check_output(["docker", "inspect", "-f", "{{ .NetworkSettings.IPAddress }}",
                                                     self.container_id]).decode("utf-8").strip()
        # override with container paths
        self.conf_path = os.path.expanduser("/home/{}/.config/udtc".format(settings.DOCKER_USER))

    def tearDown(self):
        subprocess.check_call([settings.DOCKER_EXEC_NAME, "stop", self.container_id], stdout=subprocess.DEVNULL)
        subprocess.check_call([settings.DOCKER_EXEC_NAME, "rm", self.container_id], stdout=subprocess.DEVNULL)
        super().tearDown()  # this will call other parents of ContainerTests ancestors, like LargeFrameworkTests

    def command(self, commands_to_run):
        """Return a string for a command line ready to run in docker"""
        return " ".join(self.command_as_list(commands_to_run))

    def command_as_list(self, commands_to_run):
        """Return a list for a command line ready to run in docker"""

        if isinstance(commands_to_run, list):
            commands_to_run = " ".join(commands_to_run)
        return ["sshpass", "-p", settings.DOCKER_PASSWORD, "ssh", "-o", "UserKnownHostsFile=/dev/null", "-o",
                "StrictHostKeyChecking=no", "-t", "-q",
                "{}@{}".format(settings.DOCKER_USER, self.container_ip),
                "bash -c '[ ! -f /tmp/dbus-file ] && dbus-launch > /tmp/dbus-file; export $(cat /tmp/dbus-file); "
                "cd {}; source env/bin/activate; {}'".format(settings.UDTC_IN_CONTAINER, commands_to_run)]

    def _exec_command(self, command):
        """Exec the required command inside the container"""
        return_code = subprocess.call(command)
        if return_code == 0:
            return True
        elif return_code == 1:
            return False
        raise BaseException("Unknown return code from launcher_exists_and_is_pinned")

    def launcher_exists_and_is_pinned(self, launcher_path):
        """Check if launcher exists and is pinned inside the container"""
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "check_launcher_exists_and_is_pinned"),
                                        launcher_path])
        return self._exec_command(command)

    def path_exists(self, path):
        """Check if a path exists inside the container"""
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "path_exists"), path])
        return self._exec_command(command)

    def create_file(self, path, content):
        """Create file inside the container.replace in path current user with the docker user"""
        path = path.replace(os.getlogin(), settings.DOCKER_USER)
        dir_path = os.path.dirname(path)
        command = self.command_as_list(["mkdir", "-p", dir_path, ";", "echo", content, ">", path])
        if self._exec_command(command) != True:
            raise BaseException("Couldn't create {} in container".format(path))
