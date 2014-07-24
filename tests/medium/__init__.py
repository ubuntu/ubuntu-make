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
from ..tools import get_root_dir, LoggedTestCase
from ..large.test_android import AndroidStudioTests
from udtc import settings


class ContainerTests(LoggedTestCase):
    """Container-based tests utilities"""

    def setUp(self):
        super().setUp()
        print("CALLLLLLLLLLLLLLLLLLED")
        self.udtc_path = get_root_dir()
        self.image_name = settings.DOCKER_TESTIMAGE
        self.container_id = subprocess.check_output([settings.DOCKER_EXEC_NAME, "run", "-d", "-v",
                                                     "{}:{}".format(self.udtc_path, settings.UDTC_IN_CONTAINER),
                                                     self.image_name,
                                                     'sh', '-c',
                                                     'mkdir -p /home/didrocks/work/ubuntu-developer-tools-center && '
                                                     'ln -s /udtc/env /home/didrocks/work/ubuntu-developer-tools-center'
                                                     ' && /usr/sbin/sshd -D']).decode("utf-8").strip()
        print(self.container_id)
        self.container_ip = subprocess.check_output(["docker", "inspect", "-f", "{{ .NetworkSettings.IPAddress }}",
                                                     self.container_id]).decode("utf-8").strip()
        # override in container paths
        self.installed_path = os.path.expanduser("/home/{}/tools/android/android-studio".format(settings.DOCKER_USER))
        self.conf_path = os.path.expanduser("/home/{}/.config/udtc".format(settings.DOCKER_USER))

    def tearDown(self):
        subprocess.check_call([settings.DOCKER_EXEC_NAME, "stop", self.container_id], stdout=subprocess.DEVNULL)
        subprocess.check_call([settings.DOCKER_EXEC_NAME, "rm", self.container_id], stdout=subprocess.DEVNULL)
        super().tearDown()

    def command(self, commands_to_run):
        """Run command in docker and return a string"""
        return " ".join(self.command_as_list(commands_to_run))

    def command_as_list(self, commands_to_run):
        """Run command in docker and return as a list"""

        if isinstance(commands_to_run, list):
            commands_to_run = " ".join(commands_to_run)
        return ["sshpass", "-p", settings.DOCKER_PASSWORD, "ssh", "-o", "UserKnownHostsFile=/dev/null", "-o",
                "StrictHostKeyChecking=no", "-t", "-q",
                "{}@{}".format(settings.DOCKER_USER, self.container_ip),
                "bash -c '[ ! -f /tmp/dbus-file ] && dbus-launch > /tmp/dbus-file; export $(cat /tmp/dbus-file); "
                "cd {}; source env/bin/activate; {}'".format(settings.UDTC_IN_CONTAINER, commands_to_run)]
