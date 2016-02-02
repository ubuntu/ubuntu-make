# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Canonical
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


"""Game IDEs module"""

from concurrent import futures
from contextlib import suppress
from gettext import gettext as _
import logging
import os
import re
import stat

import umake.frameworks.baseinstaller
from umake.network.download_center import DownloadItem
from umake.tools import as_root, create_launcher, get_application_desktop_file, get_current_arch,\
    ChecksumType, MainLoop, Checksum
from umake.ui import UI

logger = logging.getLogger(__name__)


class GamesCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Games", description=_("Games Development Environment"), logo_path=None)


class Stencyl(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Stencyl", description=_("Stencyl game developer IDE"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page="http://www.stencyl.com/download/",
                         desktop_filename="stencyl.desktop",
                         required_files_path=["Stencyl"],
                         packages_requirements=["libxtst6:i386", "libxext6:i386", "libxi6:i386", "libncurses5:i386",
                                                "libxt6:i386", "libxpm4:i386", "libxmu6:i386",
                                                "libgtk2.0-0:i386", "libatk1.0-0:i386", "libc6:i386", "libcairo2:i386",
                                                "libexpat1:i386", "libfontconfig1:i386", "libfreetype6:i386",
                                                "libglib2.0-0:i386", "libice6:i386", "libpango1.0-0:i386",
                                                "libpng12-0:i386", "libsm6:i386", "libxau6:i386", "libxcursor1:i386",
                                                "libxdmcp6:i386", "libxfixes3:i386", "libx11-6:i386",
                                                "libxinerama1:i386", "libxrandr2:i386", "libxrender1:i386",
                                                "zlib1g:i386", "libnss3-1d:i386", "libnspr4-0d:i386", "libcurl3:i386",
                                                "libasound2:i386"])

    def parse_download_link(self, line, in_download):
        """Parse Stencyl download links"""
        url, md5sum = (None, None)
        if ">Linux <" in line:
            in_download = True
        if in_download:
            regexp = r'href="(.*)"><.*64-'
            if get_current_arch() == "i386":
                regexp = r'href="(.*)"><.*32-'
            p = re.search(regexp, line)
            with suppress(AttributeError):
                url = p.group(1)
            if '<div class="spacer"><br/><br/>' in line:
                in_download = False

        if url is None:
            return (None, in_download)
        return ((url, None), in_download)

    def post_install(self):
        """Create the Stencyl launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Stencyl"),
                        icon_path=os.path.join(self.install_path, "data", "other", "icon-30x30.png"),
                        exec='"{}" %f'.format(self.exec_path),
                        comment=self.description,
                        categories="Development;IDE;",
                        extra="Path={}\nStartupWMClass=stencyl-sw-Launcher".format(self.install_path)))


def _chrome_sandbox_setuid(path):
    """Chown and setUID to chrome sandbox"""
    # switch to root
    with as_root():
        try:
            os.chown(path, 0, -1)
            os.chmod(path, stat.S_ISUID | stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            logger.debug("Changed setUID mode {}".format(path))
            return True
        except Exception as e:
            logger.error("Couldn't change owner and file perm to {}: {}".format(path, e))
            return False


class Unity3D(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Unity3d", description=_("Unity 3D Editor Linux experimental support"),
                         category=category, only_on_archs=['amd64'],
                         download_page="http://forum.unity3d.com/threads/" +
                                       "unity-on-linux-release-notes-and-known-issues.350256/",
                         match_last_link=True,
                         checksum_type=ChecksumType.sha1,
                         dir_to_decompress_in_tarball='unity-editor*',
                         desktop_filename="unity3d-editor.desktop",
                         required_files_path=[os.path.join("Editor", "Unity")],
                         # we need root access for chrome sandbox setUID
                         need_root_access=True,
                         # Note that some packages requirements essential to the system itself are not listed (we
                         # don't want to create fake packages and kill the container for medium tests)
                         packages_requirements=["gconf-service", "lib32gcc1", "lib32stdc++6", "libasound2", "libcairo2",
                                                "libcap2", "libcups2", "libfontconfig1", "libfreetype6", "libgconf-2-4",
                                                "libgdk-pixbuf2.0-0", "libgl1-mesa-glx", "libglu1-mesa", "libgtk2.0-0",
                                                "libnspr4", "libnss3", "libpango1.0-0", "libpq5", "libxcomposite1",
                                                "libxcursor1", "libxdamage1", "libxext6", "libxfixes3", "libxi6",
                                                "libxrandr2", "libxrender1", "libxtst6",
                                                "monodevelop"])  # monodevelop is for mono deps, temporary

    def parse_download_link(self, line, in_download):
        """Parse Unity3d download links"""
        url, sha1 = (None, None)
        if ".sh" in line:
            in_download = True
            p = re.search(r'href="(.*.sh)" target', line)
            with suppress(AttributeError):
                url = p.group(1)
        if in_download is True and ')<br />' in line:
            p = re.search(r'(\w+)\)', line)
            with suppress(AttributeError):
                sha1 = p.group(1)
        return ((url, sha1), in_download)

    def decompress_and_install(self, fds):
        """Override to strip the unwanted shell header part"""
        logger.debug("Start looking at the archive inside the script")
        for line in fds[0]:
            if line.startswith(b"__ARCHIVE_BEGINS_HERE__"):
                logger.debug("Found the archive inside the script")
                break
        super().decompress_and_install(fds)

    def post_install(self):
        """Create the Unity 3D launcher and setuid chrome sandbox"""
        with futures.ProcessPoolExecutor(max_workers=1) as executor:
            # chrome sandbox requires this: https//code.google.com/p/chromium/wiki/LinuxSUIDSandbox
            f = executor.submit(_chrome_sandbox_setuid, os.path.join(self.install_path, "Editor", "chrome-sandbox"))
            if not f.result():
                UI.return_main_screen(exit_status=1)
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Unity3D Editor"),
                        icon_path=os.path.join(self.install_path, "unity-editor-icon.png"),
                        exec=self.exec_path,
                        comment=self.description,
                        categories="Development;IDE;"))


class Twine(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Twine", description=_("Twine tool for creating interactive and nonlinear stories"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page="http://twinery.org/",
                         dir_to_decompress_in_tarball='twine*',
                         desktop_filename="twine.desktop",
                         required_files_path=["Twine"])
        # add logo download as the tar doesn't provide one
        self.download_requests.append(DownloadItem("http://twinery.org/img/logo.svg", None))

    def parse_download_link(self, line, in_download):
        """Parse Twine download links"""
        url = None
        regexp = r'href="(.*)" .*linux64'
        if get_current_arch() == "i386":
            regexp = r'href="(.*)" .*linux32'
        p = re.search(regexp, line)
        with suppress(AttributeError):
            url = p.group(1)
        return ((url, None), False)

    def decompress_and_install(self, fds):
        # if icon, we grab the icon name to reference it later on
        for fd in fds:
            if fd.name.endswith(".svg"):
                orig_icon_name = os.path.basename(fd.name)
                break
        else:
            logger.error("We couldn't download the Twine icon")
            UI.return_main_screen(exit_status=1)
        super().decompress_and_install(fds)
        # rename the asset logo
        self.icon_name = "logo.svg"
        os.rename(os.path.join(self.install_path, orig_icon_name), os.path.join(self.install_path, self.icon_name))

    def post_install(self):
        """Create the Twine launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Twine"),
                        icon_path=os.path.join(self.install_path, self.icon_name),
                        exec='"{}" %f'.format(self.exec_path),
                        comment=self.description,
                        categories="Development;IDE;"))
