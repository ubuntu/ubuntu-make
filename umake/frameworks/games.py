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
import glob
import logging
import os
import re
import shutil
import stat
import json

import umake.frameworks.baseinstaller
from umake.network.download_center import DownloadItem, DownloadCenter
from umake.tools import as_root, create_launcher, get_application_desktop_file, get_current_arch,\
    ChecksumType, MainLoop, Checksum, add_exec_link
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
                         desktop_filename="blender.desktop",
                         required_files_path=["blender"],
                         dir_to_decompress_in_tarball='blender*', **kwargs)

    arch_trans = {
        "amd64": "x86_64",
        "i386": "i686"
    }

    def parse_download_link(self, line, in_download):
        """Parse Blender download links"""
        url = None
        if '.tar.bz2' in line:
            p = re.search(r'href=\"(https://www\.blender\.org/[^<]*{}\.tar\.bz2)/?"'.format(
                          self.arch_trans[get_current_arch()]), line)
            with suppress(AttributeError):
                url = p.group(1)
                filename = 'release' + re.search('blender-(.*)-linux', url).group(1).replace('.', '') + '.md5'
                self.checksum_url = os.path.join(os.path.dirname(url),
                                                 filename).replace('download', 'release').replace('www', 'download')
                url = url.replace('www.blender.org/download', 'download.blender.org/release')
        return ((url, None), in_download)

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


class Unity3D(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Unity3d", description=_("Unity 3D Editor Linux experimental support"),
                         only_on_archs=['amd64'],
                         download_page="https://forum.unity3d.com/" +
                                       "threads/unity-on-linux-release-notes-and-known-issues.350256/page-2",
                         match_last_link=True,
                         dir_to_decompress_in_tarball='Editor',
                         desktop_filename="unity3d-editor.desktop",
                         required_files_path=[os.path.join("Unity")],
                         # we need root access for chrome sandbox setUID
                         need_root_access=True,
                         # Note that some packages requirements essential to the system itself are not listed (we
                         # don't want to create fake packages and kill the container for medium tests)
                         packages_requirements=[
                             "gconf-service", "lib32gcc1", "lib32stdc++6", "libasound2", "libcairo2",
                             "libcap2", "libcups2", "libfontconfig1", "libfreetype6", "libgconf-2-4",
                             "libgdk-pixbuf2.0-0", "libglu1-mesa", "libgtk2.0-0",
                             "libgl1-mesa-glx | libgl1-mesa-glx-lts-utopic |\
                              libgl1-mesa-glx-lts-vivid | libgl1-mesa-glx-lts-wily",
                             "libnspr4", "libnss3", "libpango1.0-0", "libpq5", "libxcomposite1",
                             "libxcursor1", "libxdamage1", "libxext6", "libxfixes3", "libxi6",
                             "libxrandr2", "libxrender1", "libxtst6"],
                         **kwargs)

    def parse_download_link(self, line, in_download):
        """Parse Unity3d download links"""
        url = None
        if "beta.unity" in line:
            in_download = True
        if in_download:
            p = re.search(
                r'href="(https://beta.unity3d.*.html)" target="_blank" class="externalLink">https://beta.unity3d.com',
                line)
            with suppress(AttributeError):
                url = p.group(1).replace("public_download.html", "LinuxEditorInstaller/Unity.tar.xz")
        if url is None:
            return (None, in_download)
        return ((url, None), in_download)

    def post_install(self):
        """Create the Unity 3D launcher and setuid chrome sandbox"""
        with futures.ProcessPoolExecutor(max_workers=1) as executor:
            # chrome sandbox requires this: https//code.google.com/p/chromium/wiki/LinuxSUIDSandbox
            f = executor.submit(_chrome_sandbox_setuid, os.path.join(self.install_path, "chrome-sandbox"))
            if not f.result():
                UI.return_main_screen(status_code=1)
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Unity3D Editor"),
                        icon_path=os.path.join(self.install_path, "Data", "Resources", "LargeUnityIcon.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;"))


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
        self.download_requests.append(DownloadItem("https://twinery.org/homepage/img/logo.svg", None))

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

    def parse_download_link(self, line, in_download):
        url = None
        if "linux-{}".format(self.arch_trans[get_current_arch()]) in line["browser_download_url"]:
            in_download = True
            url = line["browser_download_url"]
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


class GDevelop(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="GDevelop", description=_("Create your own games"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/4ian/GD/releases/latest",
                         packages_requirements=["libgconf-2-4"],
                         dir_to_decompress_in_tarball='gdevelop*',
                         desktop_filename="gdevelop.desktop",
                         required_files_path=["gdevelop"],
                         **kwargs)
        self.icon_filename = "GDevelop.png"
        self.icon_url = os.path.join("https://raw.githubusercontent.com/4ian/GD/master/Binaries/Packaging",
                                     "linux-extra-files/usr/share/icons/hicolor/128x128/apps", self.icon_filename)

    def parse_download_link(self, line, in_download):
        url = None
        if ".tar.gz" in line["browser_download_url"]:
            in_download = True
            url = line["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Create the GDevelop launcher"""
        DownloadCenter(urls=[DownloadItem(self.icon_url, None)],
                       on_done=self.save_icon, download=True)
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("GDevelop"),
                        icon_path=os.path.join(self.install_path, self.icon_filename),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;"))

    def save_icon(self, download_result):
        """Save correct GDevelop icon"""
        icon = download_result.pop(self.icon_url).fd.name
        shutil.copy(icon, os.path.join(self.install_path, self.icon_filename))
        logger.debug("Copied icon: {}".format(self.icon_url))


class Godot(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Godot", description=_("The game engine you waited for"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://godotengine.org/download/linux",
                         desktop_filename="godot.desktop",
                         required_files_path=['godot'],
                         **kwargs)
        self.icon_url = "https://godotengine.org/themes/godotengine/assets/download/godot_logo.svg"
        self.icon_filename = "Godot.svg"

    arch_trans = {
        "amd64": "64",
        "i386": "32"
    }

    def parse_download_link(self, line, in_download):
        """Parse Godot download links"""
        url = None
        if '{}.zip'.format(self.arch_trans[get_current_arch()]) in line:
            in_download = True
            p = re.search(r'href=\"(.*\.zip)\"', line)
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
