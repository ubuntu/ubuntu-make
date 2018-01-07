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
import json

import umake.frameworks.baseinstaller
from umake.network.download_center import DownloadItem, DownloadCenter
from umake.tools import as_root, create_launcher, get_application_desktop_file, get_current_arch,\
    ChecksumType, MainLoop, Checksum
from umake.ui import UI

logger = logging.getLogger(__name__)


class GamesCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Games", description=_("Games Development Environment"), logo_path=None)


class Stencyl(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Stencyl", description=_("Stencyl game developer IDE"),
                         only_on_archs=['i386', 'amd64'],
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
                                                "libasound2:i386"],
                         **kwargs)

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
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;",
                        extra="Path={}\nStartupWMClass=stencyl-sw-Launcher".format(self.install_path)))


class Blender(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Blender", description=_("Very fast and versatile 3D modeller/renderer"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://www.blender.org/download/",
                         checksum_type=ChecksumType.md5,
                         desktop_filename="blender.desktop",
                         required_files_path=["blender"],
                         dir_to_decompress_in_tarball='blender*', **kwargs)

    arch_trans = {
        "amd64": "x86_64",
        "i386": "i686"
    }
    arch = arch_trans[get_current_arch()]

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Download files to download + license and check it"""
        logger.debug("Parse download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        in_download = False
        url = False
        for line in result[self.download_page].buffer:
            line_content = line.decode()
            (_url, in_download) = self.parse_download_link(line_content, in_download)
            if not url:
                url = _url
        self.url = url

    def parse_download_link(self, line, in_download):
        """Parse Blender download links"""
        url = None
        if '.tar.bz2' in line:
            p = re.search(r'href="(http://download.blender.org/[^<]*{}.tar.bz2)"'.format(self.arch), line)
            with suppress(AttributeError):
                url = p.group(1)
                filename = 'release' + re.search('blender-(.*)-linux', url).group(1).replace('.', '') + '.md5'
                self.checksum_url = os.path.join(os.path.dirname(url), filename)
                DownloadCenter(urls=[DownloadItem(self.checksum_url, None)],
                               on_done=self.get_checksum_and_start_download, download=False)
        return (url, in_download)

    @MainLoop.in_mainloop_thread
    def get_checksum_and_start_download(self, download_result):
        for line in download_result[self.checksum_url].buffer:
            line = line.decode()
            if '{}.tar.bz2'.format(self.arch_trans[get_current_arch()]) in line:
                break
        checksum = line.split()[0]
        self.download_requests.append(DownloadItem(self.url, Checksum(self.checksum_type, checksum)))
        self.start_download_and_install()

    def post_install(self):
        """Create the Blender launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Blender"),
                        icon_path=os.path.join(self.install_path, "icons", "scalable", "apps", "blender.svg"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;Graphics"))


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


class Twine(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Twine", description=_("Twine tool for creating interactive and nonlinear stories"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://twinery.org/",
                         dir_to_decompress_in_tarball='twine*',
                         desktop_filename="twine.desktop",
                         required_files_path=["Twine"],
                         **kwargs)
        # add logo download as the tar doesn't provide one
        self.download_requests.append(DownloadItem("https://twinery.org/img/logo.svg", None))

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
            UI.return_main_screen(status_code=1)
        super().decompress_and_install(fds)
        # rename the asset logo
        self.icon_name = "logo.svg"
        os.rename(os.path.join(self.install_path, orig_icon_name), os.path.join(self.install_path, self.icon_name))

    def post_install(self):
        """Create the Twine launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Twine"),
                        icon_path=os.path.join(self.install_path, self.icon_name),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;"))


class Superpowers(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Superpowers", description=_("The HTML5 2D+3D game maker"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/superpowers/superpowers-app/releases/latest",
                         dir_to_decompress_in_tarball='superpowers*',
                         desktop_filename="superpowers.desktop",
                         required_files_path=["Superpowers"],
                         **kwargs)

    arch_trans = {
        "amd64": "x64",
        "i386": "ia32"
    }

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        logger.debug("Fetched download page, parsing.")
        page = result[self.download_page]
        error_msg = page.error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        try:
            assets = json.loads(page.buffer.read().decode())["assets"]
            download_url = None
            for asset in assets:
                if "linux-{}".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                    download_url = asset["browser_download_url"]
            if not download_url:
                raise IndexError
        except (json.JSONDecodeError, IndexError):
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download URL: " + download_url)

        self.download_requests.append(DownloadItem(download_url, None))
        self.start_download_and_install()

    def post_install(self):
        """Create the Superpowers launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Superpowers"),
                        icon_path=os.path.join(self.install_path, "resources", "app", "renderer",
                                               "images", "superpowers-256.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;"))


class Unity3D(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Unity3D", description="For removal only (The tarfile is not supported upstream anymore)",
                         download_page=None, only_on_archs=['amd64'], only_for_removal=True, **kwargs)
