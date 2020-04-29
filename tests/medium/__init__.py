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
import pwd
import subprocess
from ..tools import get_root_dir, get_tools_helper_dir, LoggedTestCase, get_docker_path, get_data_dir, INSTALL_DIR, \
    BRANCH_TESTS, SYSTEM_UMAKE_DIR, set_local_umake
from time import sleep

if not BRANCH_TESTS:
    set_local_umake()


class ContainerTests(LoggedTestCase):
    """Container-based tests utilities"""

    DOCKER_USER = "user"
    DOCKER_TESTIMAGE = "lyzardking/ubuntu-make"
    UMAKE_TOOLS_IN_CONTAINER = "/umake"
    APT_FAKE_REPO_PATH = "/apt-fake-repo"
    in_container = True

    def setUp(self):
        super().setUp()  # this will call other parents of ContainerTests ancestors, like LargeFrameworkTests
        self.umake_path = get_root_dir()
        # Docker permissions
        os.chmod(os.path.join(get_root_dir(), "docker", "umake_docker"), 0o600)
        self.install_base_path = os.path.expanduser("/home/{}/{}".format(self.DOCKER_USER, INSTALL_DIR))
        self.binary_dir = self.binary_dir.replace(os.environ['HOME'], "/home/{}".format(self.DOCKER_USER))
        self.image_name = self.DOCKER_TESTIMAGE
        if not hasattr(self, "hosts"):
            self.hosts = {}
        if not hasattr(self, "additional_local_frameworks"):
            self.additional_local_frameworks = []
        command = [get_docker_path(), "run"]

        # bind master used for testing tools code inside the container
        runner_cmd = "mkdir -p {}; ln -s {}/ {};".format(os.path.dirname(get_root_dir()), self.UMAKE_TOOLS_IN_CONTAINER,
                                                         get_root_dir())

        local_framework_dir = "/home/{}/.umake/frameworks/".format(self.DOCKER_USER)
        runner_cmd += "mkdir -p {};".format(local_framework_dir)
        for additional_framework in self.additional_local_frameworks:
            runner_cmd += "cp {} {};".format(
                os.path.join(self.UMAKE_TOOLS_IN_CONTAINER, additional_framework), local_framework_dir)

        if not BRANCH_TESTS:
            # create a system binary which will use system umake version (without having the package installed)
            bin_umake = "/usr/bin/umake"
            runner_cmd += "echo '#!/usr/bin/env python3\nfrom umake import main\nif __name__ == \"__main__\":" \
                          "\n  main()'>{bin_umake}; chmod +x {bin_umake};".format(bin_umake=bin_umake)

        # start the local server at container startup
        for port, hostnames in self.hosts.items():
            ftp_redir = hasattr(self, 'ftp')
            for hostname in hostnames:
                if "-h" not in command:
                    command.extend(["-h", hostname])
                runner_cmd += ' echo "127.0.0.1 {}" >> /etc/hosts;'.format(hostname)
            runner_cmd += "{} {} 'sudo -E env PATH={} VIRTUAL_ENV={} {} {} {} {}';".format(
                os.path.join(get_tools_helper_dir(), "run_in_umake_dir_async"),
                self.UMAKE_TOOLS_IN_CONTAINER,
                os.getenv("PATH"), os.getenv("VIRTUAL_ENV"),
                os.path.join(get_tools_helper_dir(), "run_local_server"),
                str(port),
                str(ftp_redir),
                " ".join(hostnames) if port == 443 else "")

            if ftp_redir:
                runner_cmd += "/usr/bin/twistd ftp -p 21 -r {};".format(os.path.join(get_data_dir(), 'server-content',
                                                                                     hostnames[0]))

        if hasattr(self, "apt_repo_override_path"):
            runner_cmd += "sh -c 'echo deb file:{} / > /etc/apt/sources.list'; apt-get update;".format(
                self.apt_repo_override_path)
        runner_cmd += "/usr/sbin/sshd -D"

        # we bindmount system umake directory
        if not BRANCH_TESTS:
            command.extend(["-v", "{system_umake}:{system_umake}".format(system_umake=SYSTEM_UMAKE_DIR)])

        command.extend(["-d", "-v", "{}:{}".format(self.umake_path, self.UMAKE_TOOLS_IN_CONTAINER),
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
        return ["ssh", "-i", os.path.join(get_root_dir(), "docker", "umake_docker"),
                "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", "-t", "-q",
                "{}@{}".format(self.DOCKER_USER, self.container_ip),
                "{} {} '{}'".format(os.path.join(get_tools_helper_dir(), "run_in_umake_dir"),
                                    self.UMAKE_TOOLS_IN_CONTAINER, commands_to_run)]

    def check_and_kill_process(self, process_grep, wait_before=0, send_sigkill=False):
        """Check a process matching process_grep exists and kill it"""
        sleep(wait_before)
        if not self._exec_command(self.command_as_list("{} {} {}".format(os.path.join(get_tools_helper_dir(),
                                                                                      "check_and_kill_process"),
                                                                         send_sigkill,
                                                                         " ".join(process_grep))))[0]:
            raise BaseException("The process we try to find and kill can't be found: {}".format(process_grep))

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

    def get_launcher_path(self, desktop_filename):
        """Return launcher path inside container"""
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "get_launcher_path"),
                                        desktop_filename])
        return self._exec_command(command)[1]

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

    def remove_path(self, path):
        """Remove targeted path"""
        path = path.replace(os.environ['HOME'], "/home/{}".format(self.DOCKER_USER))
        command = self.command_as_list([os.path.join(get_tools_helper_dir(), "remove_path"), path])
        self._exec_command(command)

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
        try:
            src_user = os.getlogin()
        except FileNotFoundError:
            # fallback for container issues when trying to get login
            src_user = pwd.getpwuid(os.getuid())[0]
        path = path.replace(src_user, self.DOCKER_USER)
        dir_path = os.path.dirname(path)
        command = self.command_as_list(["mkdir", "-p", dir_path, path])
        if not self._exec_command(command)[0]:
            raise BaseException("Couldn't create {} in container".format(path))
