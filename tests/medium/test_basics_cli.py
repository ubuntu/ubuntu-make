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

import subprocess
from ..tools import get_root_dir
from ..large.test_basics_cli import BasicCLI
from udtc import settings


class BasicCLIInContainer(BasicCLI):
    """This will test the basic cli command class inside a container"""

    def setUp(self):
        super().setUp()
        self.udtc_path = get_root_dir()
        self.udtc_in_container = "/udtc"
        self.image_name = settings.DOCKER_TESTIMAGE
        self.container_id = subprocess.check_output(["docker", "run", "-d", "-v",
                                                     "{}:{}".format(self.udtc_path, self.udtc_in_container),
                                                     self.image_name,
                                                     'sh', '-c',
                                                     'mkdir -p /home/didrocks/work/ubuntu-developer-tools-center && '
                                                     'ln -s /udtc/env /home/didrocks/work/ubuntu-developer-tools-center'
                                                     ' && /usr/sbin/sshd -D']).decode("utf-8").strip()
        self.container_ip = subprocess.check_output(["docker", "inspect", "-f", "{{ .NetworkSettings.IPAddress }}",
                                                     self.container_id]).decode("utf-8").strip()

    def tearDown(self):
        subprocess.check_call(["docker", "stop", self.container_id], stdout=subprocess.DEVNULL)
        subprocess.check_call(["docker", "rm", self.container_id], stdout=subprocess.DEVNULL)
        super().tearDown()

    def command(self, commands_to_run):
        """Run command in docker"""
        return ["sshpass", "-p", settings.DOCKER_PASSWORD, "ssh", "-q",
                "{}@{}".format(settings.DOCKER_USER, self.container_ip), '-oStrictHostKeyChecking=no',
                "bash -c '[ ! -f /tmp/dbus-file ] && dbus-launch > /tmp/dbus-file; export $(cat /tmp/dbus-file); "
                "cd /udtc; source env/bin/activate; {}'".format(' '.join(commands_to_run))]
