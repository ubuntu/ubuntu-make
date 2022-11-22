# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Canonical
#
# Authors:
#  Didier Roche
#  Galileo Sartor
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


"""Generic Electronics module."""
from concurrent import futures
from contextlib import suppress
from gettext import gettext as _
import grp
import logging
import os
from os.path import join
import pwd
import re
import subprocess

import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.tools import as_root, create_launcher, get_application_desktop_file, get_current_arch, get_current_distro_version
from umake.ui import UI

logger = logging.getLogger(__name__)


def _add_to_group(user, group):
    """Add user to group"""
    # switch to root
    with as_root():
        env = os.environ.copy()
        if get_current_distro_version(distro_name="debian") is not None:
            env["PATH"] = "/usr/sbin:/sbin:" + env["PATH"]
        try:
            output = subprocess.check_output(["adduser", user, group], env=env)
            logger.debug("Added {} to {}: {}".format(user, group, output))
            return True
        # except FileNotFoundError:
        #     logger.error("Couldn't add {} to {}: adduser command not found".format(user, group))
        #     return False
        except subprocess.CalledProcessError as e:
            logger.error("Couldn't add {} to {}".format(user, group))
            return False


class ElectronicsCategory(umake.frameworks.BaseCategory):
    def __init__(self):
        super().__init__(name="Electronics", description=_("Electronics software"),
                         logo_path=None)


class Arduino(umake.frameworks.baseinstaller.BaseInstaller):

    ARDUINO_GROUP = "dialout"

    def __init__(self, **kwargs):

        if os.geteuid() != 0:
            self._current_user = os.getenv("USER")
        self._current_user = pwd.getpwuid(int(os.getenv("SUDO_UID", default=0))).pw_name
        for group_name in [g.gr_name for g in grp.getgrall() if self._current_user in g.gr_mem]:
            if group_name == self.ARDUINO_GROUP:
                self.was_in_arduino_group = True
                break
        else:
            self.was_in_arduino_group = False

        super().__init__(name="Arduino", description=_("Arduino"),
                         only_on_archs=['amd64'],
                         download_page="https://api.github.com/repos/arduino/arduino-ide/releases/latest",
                         desktop_filename="arduino-ide.desktop",
                         required_files_path=["arduino-ide"],
                         dir_to_decompress_in_tarball="arduino-ide*",
                         need_root_access=not self.was_in_arduino_group,
                         json=True, **kwargs)

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if "Linux_64bit.zip" in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Create the Arduino IDE launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Arduino IDE"),
                        icon_path=os.path.join(self.install_path, "resources", "app", "lib",
                                               "e1f37bb1fd5c02b876f8..png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("Arduino IDE 2.x"),
                        categories="Development;IDE;"))
        # add the user to arduino group
        if not self.was_in_arduino_group:
            with futures.ProcessPoolExecutor(max_workers=1) as executor:
                f = executor.submit(_add_to_group, self._current_user, self.ARDUINO_GROUP)
                if not f.result():
                    UI.return_main_screen(status_code=1)
            UI.delayed_display(DisplayMessage(_("You need to logout and login again for your installation to work")))



class ArduinoLegacy(umake.frameworks.baseinstaller.BaseInstaller):
    """The Arduino Software distribution."""

    ARDUINO_GROUP = "dialout"

    def __init__(self, **kwargs):

        if os.geteuid() != 0:
            self._current_user = os.getenv("USER")
        self._current_user = pwd.getpwuid(int(os.getenv("SUDO_UID", default=0))).pw_name
        for group_name in [g.gr_name for g in grp.getgrall() if self._current_user in g.gr_mem]:
            if group_name == self.ARDUINO_GROUP:
                self.was_in_arduino_group = True
                break
        else:
            self.was_in_arduino_group = False

        super().__init__(name="Arduino Legacy",
                         description=_("The Arduino Software Distribution"),
                         only_on_archs=['i386', 'amd64', 'armhf', 'arm64'],
                         download_page='https://www.arduino.cc/en/Main/Software',
                         dir_to_decompress_in_tarball='arduino-*',
                         desktop_filename='arduino.desktop',
                         packages_requirements=['gcc-avr', 'avr-libc'],
                         need_root_access=not self.was_in_arduino_group,
                         required_files_path=["arduino"], **kwargs)

    arch_trans = {
        "amd64": "64",
        "i386": "32",
        "armhf": "arm",  # This should work on the raspberryPi
        "arm64": "aarch64"
    }

    def parse_download_link(self, line, in_download):
        """Parse Arduino download links (hardcoded)"""
        url = "https://downloads.arduino.cc/arduino-1.8.19-linux{}.tar.xz".format(self.arch_trans[get_current_arch()])
        return ((url, None), in_download)

    def post_install(self):
        """Create the Arduino launcher"""
        icon_path = join(self.install_path, 'lib', 'arduino_icon.ico')
        comment = _("The Arduino Software IDE")
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=_("Arduino Legacy"),
                                                     icon_path=icon_path,
                                                     try_exec=self.exec_path,
                                                     exec=self.exec_link_name,
                                                     comment=comment,
                                                     categories=categories))
        # add the user to arduino group
        if not self.was_in_arduino_group:
            with futures.ProcessPoolExecutor(max_workers=1) as executor:
                f = executor.submit(_add_to_group, self._current_user, self.ARDUINO_GROUP)
                if not f.result():
                    UI.return_main_screen(status_code=1)
            UI.delayed_display(DisplayMessage(_("You need to logout and login again for your installation to work")))


class Eagle(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Eagle", description=_("PCB design software for students, makers, and professionals"),
                         only_on_archs=['amd64'],
                         download_page="https://eagle-updates.circuits.io/downloads/latest.html",
                         desktop_filename="eagle.desktop",
                         required_files_path=["eagle"],
                         dir_to_decompress_in_tarball="eagle-*",
                         **kwargs)

    def parse_download_link(self, line, in_download):
        """Parse Eagle download links"""
        url = None
        if '.tar.gz' in line:
            p = re.search(r'href="([^<]*.tar.gz)"', line)
            with suppress(AttributeError):
                url = p.group(1)
        return ((url, None), in_download)

    def post_install(self):
        """Create the Eagle launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Eagle"),
                        icon_path=os.path.join(self.install_path, "bin", "eagle-logo.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;"))


class Fritzing(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Fritzing", description="For removal only (tarfile not supported upstream anymore)",
                         download_page=None, only_on_archs=['amd64'], only_for_removal=True, **kwargs)
