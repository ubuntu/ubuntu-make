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

from contextlib import suppress
from gettext import gettext as _
import logging
import os
import re
import shutil
import stat

import umake.frameworks.baseinstaller
from umake.network.download_center import DownloadItem, DownloadCenter
from umake.tools import as_root, create_launcher, get_application_desktop_file, get_current_arch

logger = logging.getLogger(__name__)


class GamesCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Games", description=_("Games Development Environment"), logo_path=None)


class Stencyl(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Stencyl", description=_("For removal only (SSL errors on download page)"),
                         download_page=None, only_on_archs=['amd64'], only_for_removal=True, **kwargs)


class Blender(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Blender", description=_("Very fast and versatile 3D modeller/renderer"),
                         only_on_archs=['amd64'],
                         download_page="https://www.blender.org/download/",
                         desktop_filename="blender.desktop",
                         required_files_path=["blender"],
                         dir_to_decompress_in_tarball='blender*', **kwargs)

    def parse_download_link(self, line, in_download):
        """Parse Blender download links"""
        url = None
        if 'linux-x64.tar.xz' in line:
            p = re.search(r'href=\"(https:\/\/www\.blender\.org\/.*linux-x64\.tar\.xz).?"', line)
            with suppress(AttributeError):
                url = p.group(1)
                filename = 'release' + re.search('blender-(.*)-linux', url).group(1).replace('.', '') + '.md5'
                self.checksum_url = os.path.join(os.path.dirname(url),
                                                 filename).replace('download', 'release').replace('www', 'download')
        return ((url, None), in_download)

    def post_install(self):
        """Create the Blender launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Blender"),
                        icon_path=os.path.join(self.install_path, "icons", "scalable", "apps", "blender.svg"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;Graphics"))


class Unity3D(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Unity3D", description="For removal only (tarfile not supported upstream anymore)",
                         download_page=None, only_on_archs=['amd64'], only_for_removal=True, **kwargs)


class Twine(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Twine", description=_("Twine tool for creating interactive and nonlinear stories"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/klembot/twinejs/releases/latest",
                         dir_to_decompress_in_tarball='twine*',
                         desktop_filename="twine.desktop",
                         required_files_path=["Twine"],
                         json=True, **kwargs)
        # add logo download as the tar doesn't provide one
        self.icon_url = "https://github.com/klembot/twinejs/blob/master/icons/app.svg"
        self.icon_name = 'twine.svg'

    arch_trans = {
        "amd64": "x64",
        "aarch64": "arm64",
        "i386": "ia32"
    }

    def parse_download_link(self, line, in_download):
        """Parse Twine download links"""
        url = None
        for asset in line["assets"]:
            if 'Linux-{}.zip'.format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Create the Twine launcher"""
        DownloadCenter(urls=[DownloadItem(self.icon_url, None)],
                       on_done=self.save_icon, download=True)
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Twine"),
                        icon_path=os.path.join(self.install_path, self.icon_name),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;"))

    def save_icon(self, download_result):
        """Save correct Twine icon"""
        icon = download_result.pop(self.icon_url).fd.name
        shutil.copy(icon, os.path.join(self.install_path, self.icon_name))
        logger.debug("Copied icon: {}".format(self.icon_url))


class Superpowers(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Superpowers", description=_("The HTML5 2D+3D game maker"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/superpowers/superpowers-app/releases/latest",
                         dir_to_decompress_in_tarball='superpowers*',
                         desktop_filename="superpowers.desktop",
                         required_files_path=["Superpowers"],
                         json=True,
                         version_regex='/v(\d+\.\d+\.\d+)',
                         supports_update=True,
                         **kwargs)

    arch_trans = {
        "amd64": "x64",
        "i386": "ia32"
    }

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if "linux-{}".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Create the Superpowers launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Superpowers"),
                        icon_path=os.path.join(self.install_path, "resources", "app", "renderer",
                                               "images", "superpowers-256.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;"))

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'version'), 'r') as file:
                return file.readline().strip() if file else None
        except FileNotFoundError:
            return


class GDevelop(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="GDevelop", description="For removal only (tarfile not supported upstream anymore)",
                         download_page=None, only_on_archs=['i386', 'amd64'], only_for_removal=True, **kwargs)


class Godot(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Godot", description=_("The game engine you waited for"),
                         only_on_archs=['amd64'],
                         download_page="https://godotengine.org/download/linux",
                         desktop_filename="godot.desktop",
                         required_files_path=['godot'],
                         **kwargs)
        self.icon_url = "https://godotengine.org/assets/press/icon_color.svg"
        self.icon_filename = "Godot.svg"

    arch_trans = {
        "amd64": "x86_64",
    }

    def parse_download_link(self, line, in_download):
        """Parse Godot download links"""
        url = None
        if '{}.zip'.format(self.arch_trans[get_current_arch()]) in line:
            in_download = True
            p = re.search(r'href=\"?([^\s]+\.zip)', line)
            with suppress(AttributeError):
                url = p.group(1)
                bin = re.search(r'(Godot.*)\.zip', url)
                self.required_files_path[0] = bin.group(1)

        if url is None:
            return (None, in_download)
        return ((url, None), in_download)

    def post_install(self):
        """Create the Godot launcher"""
        # Override the exec_path.
        # Rename the binary to remove the version.
        self.set_exec_path()
        shutil.move(self.exec_path, os.path.join(self.install_path, 'godot'))
        self.exec_path = os.path.join(self.install_path, 'godot')

        DownloadCenter(urls=[DownloadItem(self.icon_url, None)],
                       on_done=self.save_icon, download=True)
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Godot"),
                        icon_path=os.path.join(self.install_path, self.icon_filename),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;"))

    def save_icon(self, download_result):
        """Save correct Godot icon"""
        icon = download_result.pop(self.icon_url).fd.name
        shutil.copy(icon, os.path.join(self.install_path, self.icon_filename))
        logger.debug("Copied icon: {}".format(self.icon_url))
