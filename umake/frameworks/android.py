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


"""Android module"""

from contextlib import suppress
from gettext import gettext as _
import logging
import os
import platform
import re
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.ui import UI
from umake.tools import add_env_to_user, create_launcher, get_application_desktop_file, ChecksumType

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class AndroidCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Android", description=_("Android Development Environment"), logo_path=None)

    def parse_license(self, tag, line, license_txt, in_license):
        """Parse Android download page for license"""
        if line.startswith(tag):
            in_license = True
        if in_license:
            if line.startswith('</div>'):
                in_license = False
            else:
                license_txt.write(line)
        return in_license

    def parse_download_link(self, tag, line, in_download):
        """Parse Android download links, expect to find a md5sum and a url"""
        url, md5sum = (None, None)
        if tag in line:
            in_download = True
        if in_download:
            p = re.search(r'href="(.*)"', line)
            with suppress(AttributeError):
                url = p.group(1)
            p = re.search(r'<td>(\w+)</td>', line)
            with suppress(AttributeError):
                # ensure the size can match a md5 or sha1 checksum
                if len(p.group(1)) > 15:
                    md5sum = p.group(1)
            if "</tr>" in line:
                in_download = False

        if url is None and md5sum is None:
            return (None, in_download)
        return ((url, md5sum), in_download)


class AndroidStudio(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Android Studio", description=_("Android Studio (default)"), is_category_default=True,
                         category=category, only_on_archs=_supported_archs, expect_license=True,
                         packages_requirements=["openjdk-7-jdk", "libncurses5:i386", "libstdc++6:i386", "zlib1g:i386",
                                                "jayatana"],
                         download_page="https://developer.android.com/sdk/index.html",
                         checksum_type=ChecksumType.sha1,
                         dir_to_decompress_in_tarball="android-studio",
                         desktop_filename="android-studio.desktop",
                         required_files_path=[os.path.join("bin", "studio.sh")])

    def parse_license(self, line, license_txt, in_license):
        """Parse Android Studio download page for license"""
        return self.category.parse_license('<p class="sdk-terms-intro">', line, license_txt, in_license)

    def parse_download_link(self, line, in_download):
        """Parse Android Studio download link, expect to find a md5sum and a url"""
        return self.category.parse_download_link('id="linux-bundle"', line, in_download)

    def post_install(self):
        """Create the Android Studio launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Android Studio"),
                        icon_path=os.path.join(self.install_path, "bin", "studio.png"),
                        exec='"{}" %f'.format(os.path.join(self.install_path, "bin", "studio.sh")),
                        comment=_("Android Studio developer environment"),
                        categories="Development;IDE;",
                        extra="StartupWMClass=jetbrains-android-studio"))


class AndroidSDK(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Android SDK", description=_("Android SDK"),
                         category=category, only_on_archs=_supported_archs, expect_license=True,
                         packages_requirements=["openjdk-7-jdk", "libncurses5:i386", "libstdc++6:i386", "zlib1g:i386",
                                                "jayatana"],
                         download_page="https://developer.android.com/sdk/index.html",
                         checksum_type=ChecksumType.sha1,
                         dir_to_decompress_in_tarball="android-sdk-linux",
                         required_files_path=[os.path.join("tools", "android")])

    def parse_license(self, line, license_txt, in_license):
        """Parse Android SDK download page for license"""
        return self.category.parse_license('<p class="sdk-terms-intro">', line, license_txt, in_license)

    def parse_download_link(self, line, in_download):
        """Parse Android SDK download link, expect to find a SHA-1 and a url"""
        return self.category.parse_download_link('id="linux-tools"', line, in_download)

    def post_install(self):
        """Add necessary environment variables"""
        add_env_to_user(self.name, {"ANDROID_HOME": {"value": self.install_path, "keep": False}})
        # add "platform-tools" to PATH to ensure "adb" can be run once the platform tools are installed via
        # the SDK manager
        add_env_to_user(self.name, {"PATH": {"value": [os.path.join("$ANDROID_HOME", "tools"),
                                                       os.path.join("$ANDROID_HOME", "platform-tools")]}})
        UI.delayed_display(DisplayMessage(_("You need to restart your current shell session for your {} installation "
                                            "to work properly").format(self.name)))

        # print wiki page message
        UI.delayed_display(DisplayMessage("SDK installed in {}. More information on how to use it on {}".format(
                                          self.install_path,
                                          "https://developer.android.com/sdk/installing/adding-packages.html")))


class AndroidNDK(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Android NDK", description=_("Android NDK"),
                         category=category, only_on_archs=_supported_archs, expect_license=True,
                         download_page="https://developer.android.com/ndk/downloads/index.html",
                         checksum_type=ChecksumType.md5,
                         dir_to_decompress_in_tarball="android-ndk-*",
                         required_files_path=[os.path.join("ndk-build")])

    def parse_license(self, line, license_txt, in_license):
        """Parse Android NDK download page for license"""
        return self.category.parse_license('<div class="sdk-terms"', line, license_txt, in_license)

    def parse_download_link(self, line, in_download):
        """Parse Android NDK download link, expect to find a md5sum and a url"""
        arch = platform.machine()
        tag_machine = '64'
        if arch == 'i686':
            tag_machine = '32'
        return self.category.parse_download_link('<td>Linux {}'.format(tag_machine), line, in_download)

    def post_install(self):
        """Add necessary environment variables"""
        add_env_to_user(self.name, {"NDK_ROOT": {"value": self.install_path, "keep": False}})

        # print wiki page message
        UI.display(DisplayMessage("NDK installed in {}. More information on how to use it on {}".format(
                                  self.install_path,
                                  "https://developer.android.com/tools/sdk/ndk/index.html#GetStarted")))


class EclipseADTForRemoval(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Eclipse ADT", description="For removal only (not supported upstream anymore)",
                         download_page=None, category=category, only_on_archs=_supported_archs, only_for_removal=True)
