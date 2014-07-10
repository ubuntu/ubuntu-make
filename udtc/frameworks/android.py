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
from io import StringIO
import logging
from progressbar import ProgressBar
import os
import re
import shutil
from textwrap import dedent
import udtc.frameworks.baseinstaller
from udtc.decompressor import Decompressor
from udtc.interactions import InputText, YesNo, LicenseAgreement, DisplayMessage, UnknownProgress
from udtc.network.download_center import DownloadCenter
from udtc.network.requirements_handler import RequirementsHandler
from udtc.ui import UI
from udtc.tools import MainLoop, strip_tags, create_launcher, get_application_desktop_file

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class AndroidCategory(udtc.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name=_("Android"), description=_("Android Developement Environment"),
                         logo_path=None,
                         packages_requirements=["openjdk-7-jdk", "libncurses5:i386", "libstdc++6:i386", "zlib1g:i386"])


class EclipseAdt(udtc.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="ADT", description="Android Developer Tools (using eclipse)",
                         category=category, install_path_dir="android/adt-eclipse",
                         only_on_archs=_supported_archs)
        self.ADT_DOWNLOAD_PAGE = "https://developer.android.com/sdk/index.html"

    def setup(self, install_path=None):
        print("Installing…")
        super().setup()


class AndroidStudio(udtc.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        self.desktop_filename = "android-studio.desktop"
        super().__init__(name="Android Studio", description="Android Studio (default)", is_category_default=True,
                         category=category, only_on_archs=_supported_archs, expect_license=True,
                         download_page="http://developer.android.com/sdk/installing/studio.html",
                         dir_to_decompress_in_tarball="android-studio", desktop_file_name=self.desktop_filename)

    def parse_license(self, line, license_txt, in_license):
        """Parse Android Studio download page for license"""
        if line.startswith('<p class="sdk-terms-intro">'):
            in_license = True
        if in_license:
            if line.startswith('</div>'):
                in_license = False
            else:
                license_txt.write(line)
        return in_license

    def parse_download_link(self, line, in_download):
        """Parse Android Studio download link, expect to find a md5sum and a url"""
        url, md5sum = (None, None)
        if 'id="linux-studio"' in line:
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

        if url is None:
            return (None, in_download)
        return ((url, md5sum), in_download)

    def create_launcher(self):
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
