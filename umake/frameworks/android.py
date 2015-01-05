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
import umake.frameworks.baseinstaller
from umake.tools import create_launcher, get_application_desktop_file, get_current_arch, copy_icon, add_env_to_user, \
    ChecksumType

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class AndroidCategory(umake.frameworks.BaseCategory):

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
            p = re.search(r'href="(.*)"', line)
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

