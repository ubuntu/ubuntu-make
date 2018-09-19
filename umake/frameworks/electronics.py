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
from abc import ABCMeta, abstractmethod
from concurrent import futures
from contextlib import suppress
from gettext import gettext as _
import grp
from io import StringIO
import json
import logging
import os
from os.path import join
import pwd
import platform
import re
import subprocess
from urllib import parse
import shutil

import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage, LicenseAgreement
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.tools import as_root, create_launcher, get_application_desktop_file, ChecksumType, Checksum, MainLoop,\
    strip_tags, add_env_to_user, add_exec_link, get_current_arch
from umake.ui import UI

logger = logging.getLogger(__name__)


def _add_to_group(user, group):
    """Add user to group"""
    # switch to root
    with as_root():
        try:
            output = subprocess.check_output(["adduser", user, group])
            logger.debug("Added {} to {}: {}".format(user, group, output))
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Couldn't add {} to {}".format(user, group))
            return False


class ElectronicsCategory(umake.frameworks.BaseCategory):
    def __init__(self):
        super().__init__(name="Electronics", description=_("Electronics software"),
                         logo_path=None)


class Arduino(umake.frameworks.baseinstaller.BaseInstaller):
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

        super().__init__(name="Arduino",
                         description=_("The Arduino Software Distribution"),
                         only_on_archs=['i386', 'amd64', 'armhf'],
                         download_page='https://www.arduino.cc/en/Main/Software',
                         dir_to_decompress_in_tarball='arduino-*',
                         desktop_filename='arduino.desktop',
                         checksum_type=ChecksumType.sha512,
                         packages_requirements=['gcc-avr', 'avr-libc'],
                         need_root_access=not self.was_in_arduino_group,
                         required_files_path=["arduino"], **kwargs)

    arch_trans = {
        "amd64": "64",
        "i386": "32",
        "armhf": "arm"  # This should work on the raspberryPi
    }

    def parse_download_link(self, line, in_download):
        """Parse Arduino download links"""
        if "sha512sum.txt" in line:
            in_download = True
        else:
            in_download = False
        if in_download:
            p = re.search(r'href=.*href="(.*)" rel', line)
            with suppress(AttributeError):
                self.new_download_url = "https:" + p.group(1)
        return ((None, None), in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url].buffer.getvalue().decode()
        line = re.search(r'.*linux{}.tar.xz'.format(self.arch_trans[get_current_arch()]), res).group(0)
        # you get and store url and checksum
        checksum = line.split()[0]
        url = os.path.join(self.new_download_url.rpartition('/')[0], line.split()[1])
        self.check_data_and_start_download(url, checksum)

    def post_install(self):
        """Create the Arduino launcher"""
        icon_path = join(self.install_path, 'lib', 'arduino_icon.ico')
        comment = _("The Arduino Software IDE")
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=_("Arduino"),
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
