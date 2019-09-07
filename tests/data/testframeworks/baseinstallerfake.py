# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
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


"""Base category module"""

from contextlib import suppress
from gettext import gettext as _
import logging
import os
import platform
import re
import umake.frameworks.baseinstaller
from umake.tools import create_launcher, get_application_desktop_file, ChecksumType

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class BaseCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Base", description=_("Base category"), logo_path=None)

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


class BaseFramework(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Base Framework", description=_("Base Framework (default)"), is_category_default=True,
                         only_on_archs=_supported_archs, expect_license=True,
                         # Remove dependency to enable test on newer systems
                         # packages_requirements=["jayatana"],
                         download_page="http://localhost:8765/index.html",
                         checksum_type=ChecksumType.sha1,
                         dir_to_decompress_in_tarball="base-framework-*",
                         desktop_filename="base-framework.desktop",
                         required_files_path=[os.path.join("bin", "studio.sh")], **kwargs)

        arch = platform.machine()
        self.tag = 'id="linux-bundle64"'
        if arch == 'i686':
            self.tag = 'id="linux-bundle32"'

    def parse_license(self, line, license_txt, in_license):
        """Parse download page for license"""
        if line.startswith('<p class="sdk-terms-intro">'):
            in_license = True
        if in_license:
            if line.startswith('</div>'):
                in_license = False
            else:
                license_txt.write(line)
        return in_license

    def parse_download_link(self, line, in_download):
        """Parse download links, expect to find a md5sum and a url"""
        url, md5sum = (None, None)
        if self.tag in line:
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

    def post_install(self):
        """Create the launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Base Framework"),
                        icon_path=os.path.join(self.install_path, "bin", "studio.png"),
                        try_exec=os.path.join(self.install_path, "bin", "studio.sh"),
                        exec=self.exec_link_name,
                        comment=_("Base Framework developer environment"),
                        categories="Development;IDE;",
                        extra="StartupWMClass=jetbrains-base-framework"))
