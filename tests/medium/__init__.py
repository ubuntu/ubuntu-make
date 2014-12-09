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
import subprocess
from ..tools import get_root_dir, get_tools_helper_dir, LoggedTestCase, get_docker_path
from time import sleep
from umake import settings


class ContainerTests(LoggedTestCase):
    """Container-based tests utilities"""

    def setUp(self):
        super().setUp()  # this will call other parents of ContainerTests ancestors, like LargeFrameworkTests
        self.in_container = True
        self.umake_path = get_root_dir()
        self.image_name = settings.DOCKER_TESTIMAGE
        command = [get_docker_path(), "run"]
        runner_cmd = "mkdir -p {}; ln -s {}/ {};".format(os.path.dirname(get_root_dir()), settings.UMAKE_IN_CONTAINER,
                                                         get_root_dir())

        # start the local server at container startup
        if hasattr(self, "hostname"):
            command.extend(["-h", self.hostname])
            runner_cmd += "{} {} 'sudo -E env PATH={} VIRTUAL_ENV={} {} {} {}';".format(
                os.path.join(get_tools_helper_dir(), "run_in_umake_dir_async"),
                settings.UMAKE_IN_CONTAINER,
                os.getenv("PATH"), os.getenv("VIRTUAL_ENV"),
                os.path.join(get_tools_helper_dir(), "run_local_server"),
                self.port,
                self.hostname)

        if hasattr(self, "apt_repo_override_path"):
            runner_cmd += "sudo sh -c 'echo deb file:{} / > /etc/apt/sources.list';sudo apt-get update;".format(
                self.apt_repo_override_path)
        runner_cmd += "/usr/sbin/sshd -D"

        command.extend(["-d", "-v", "{}:{}".format(self.umake_path, settings.UMAKE_IN_CONTAINER),
                        "--dns=8.8.8.8", "--dns=8.8.4.4",  # suppress local DNS warning
                        self.image_name,
                        'sh', '-c', runner_cmd])
        self.container_id = subprocess.check_output(command).decode("utf-8").strip()
        self.container_ip = subprocess.check_output([get_docker_path(), "inspect", "-f",
                                                     "{{ .NetworkSettings.IPAddress }}",
                                                     self.container_id]).decode("utf-8").strip()
        # override with container paths
        self.conf_path = os.path.expanduser("/home/{}/.config/umake".format(settings.DOCKER_USER))
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
        return ["sshpass", "-p", settings.DOCKER_PASSWORD, "ssh", "-o", "UserKnownHostsFile=/dev/null", "-o",
                "StrictHostKeyChecking=no", "-t", "-q",
                "{}@{}".format(settings.DOCKER_USER, self.container_ip),
                "{} {} '{}'".format(os.path.join(get_tools_helper_dir(), "run_in_umake_dir"),
                                    settings.UMAKE_IN_CONTAINER, commands_to_run)]

    def check_and_kill_process(self, process_grep, wait_before=0, send_sigkill=False):
        """Check a process matching process_grep exists and kill it"""
        sleep(wait_before)
        if not self._exec_command(self.command_as_list("{} {} {}".format(os.path.join(get_tools_helper_dir(),
                                                                                      "check_and_kill_process"),
                                                                         send_sigkill,
                                                                         " ".join(process_grep)))):
            raise BaseException("The process we try to find and kill can't be found".format(process_grep))

    def _exec_command(self, command):
        """Exec the required command inside the container"""
        return_code = subprocess.call(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)
        if return_code == 0:
            return True
        elif return_code == 1:
            return False
        raise BaseException("Unknown return code from {}".format(command))

    def launcher_exists_and_is_pinned(self, desktop_filename):
        """Check if launcher exists and is pinned inside the container"""
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "check_launcher_exists_and_is_pinned"),
                                        desktop_filename])
        return self._exec_command(command)

    def path_exists(self, path):
        """Check if a path exists inside the container"""
        # replace current user home dir with container one.
        path = path.replace(os.environ['HOME'], "/home/{}".format(settings.DOCKER_USER))
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "path_exists"), path])
        return self._exec_command(command)

    def is_in_path(self, filename):
        """Check inside the container if filename is in PATH thanks to which"""
        return self._exec_command(self.command_as_list(["bash", "-i", "which", filename]))

    def create_file(self, path, content):
        """Create file inside the container.replace in path current user with the docker user"""
        path = path.replace(os.getlogin(), settings.DOCKER_USER)
        dir_path = os.path.dirname(path)
        command = self.command_as_list(["mkdir", "-p", dir_path, path])
        if not self._exec_command(command):
            raise BaseException("Couldn't create {} in container".format(path))
