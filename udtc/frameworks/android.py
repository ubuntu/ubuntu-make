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
import re
import udtc.frameworks.baseinstaller
from udtc.tools import create_launcher, get_application_desktop_file, get_current_arch, copy_icon, add_env_to_user, \
    ChecksumType

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class AndroidCategory(udtc.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name=_("Android"), description=_("Android Development Environment"), logo_path=None,
                         packages_requirements=["openjdk-7-jdk", "libncurses5:i386", "libstdc++6:i386", "zlib1g:i386"])

    def parse_license(self, line, license_txt, in_license):
        """Parse Android download page for license"""
        if line.startswith('<p class="sdk-terms-intro">'):
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
            p = re.search(r'href="(.*)">', line)
            with suppress(AttributeError):
                url = p.group(1)
            p = re.search(r'<td>(\w+)</td>', line)
            with suppress(AttributeError):
                md5sum = p.group(1)
            if "</tr>" in line:
                in_download = False

        if url is None and md5sum is None:
            return (None, in_download)
        return ((url, md5sum), in_download)


class AndroidStudio(udtc.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Android Studio", description="Android Studio (default)", is_category_default=True,
                         category=category, only_on_archs=_supported_archs, expect_license=True,
                         download_page="https://developer.android.com/sdk/installing/studio.html",
                         checksum_type=ChecksumType.sha1,
                         dir_to_decompress_in_tarball="android-studio",
                         desktop_filename="android-studio.desktop")

    def parse_license(self, line, license_txt, in_license):
        """Parse Android Studio download page for license"""
        return self.category.parse_license(line, license_txt, in_license)

    def parse_download_link(self, line, in_download):
        """Parse Android Studio download link, expect to find a md5sum and a url"""
        return self.category.parse_download_link('id="linux-studio"', line, in_download)

    def post_install(self):
        """Create the Android Studio launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Android Studio"),
                        icon_path=os.path.join(self.install_path, "bin", "idea.png"),
                        exec='"{}" %f'.format(os.path.join(self.install_path, "bin", "studio.sh")),
                        comment=_("Android Studio developer environment"),
                        categories="Development;IDE;",
                        extra="StartupWMClass=jetbrains-android-studio"))

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not os.path.join(self.install_path, "bin", "studio.sh"):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True


class EclipseAdt(udtc.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Eclipse ADT", description="Android Developer Tools (using eclipse)",
                         category=category, only_on_archs=_supported_archs, expect_license=True,
                         download_page="https://developer.android.com/sdk/index.html",
                         checksum_type=ChecksumType.md5,
                         dir_to_decompress_in_tarball="adt-bundle-linux-*", desktop_filename="adt.desktop",
                         icon_filename="adt.png")

    def parse_license(self, line, license_txt, in_license):
        """Parse ADT download page for license"""
        return self.category.parse_license(line, license_txt, in_license)

    def parse_download_link(self, line, in_download):
        """Parse ADT download link, expect to find a md5sum and a url"""
        if get_current_arch() == "i386":
            tag = 'id="linux-bundle32"'
        else:
            tag = 'id="linux-bundle64"'
        return self.category.parse_download_link(tag, line, in_download)

    def post_install(self):
        """Create the ADT launcher"""
        # copy the adt icon to local folder (as the icon is in a .*version folder, not stable)
        copy_icon(os.path.join(self.install_path,
                               'eclipse/plugins/com.android.ide.eclipse.adt.package*/icons/adt48.png'),
                  self.icon_filename)
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("ADT Eclipse"),
                        icon_path=os.path.splitext(self.icon_filename)[0],
                        exec='"{}" %f'.format(os.path.join(self.install_path, "eclipse", "eclipse")),
                        comment=_("Android Developer Tools (using eclipse)"),
                        categories="Development;IDE;"))
        # add adb and other android tools to PATH
        paths_to_add = os.pathsep.join([os.path.join(self.install_path, "sdk", "platform-tools"),
                                        os.path.join(self.install_path, "sdk", "tools")])
        add_env_to_user(self.name, {"PATH": {"value": paths_to_add}})

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not os.path.join(self.install_path, "eclipse", "eclipse"):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True
