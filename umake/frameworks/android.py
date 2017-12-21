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
        if tag in line:
            in_license = True
        if in_license:
            if '<input id="agree_' in line:
                in_license = False
            else:
                license_txt.write(line)
        return in_license

    def parse_download_link(self, tag, line, in_download):
        """Parse Android download links, expect to find a sha1sum and a url"""
        url, sha1sum = (None, None)
        if tag in line:
            in_download = True
        if in_download:
            p = re.search(r'href=\"(https://dl.google.com.*-linux.*.zip)\"', line)
            with suppress(AttributeError):
                url = p.group(1)
            p = re.search(r'<td>(\w+)</td>', line)
            with suppress(AttributeError):
                # ensure the size can match a md5 or sha1 checksum
                if len(p.group(1)) > 15:
                    sha1sum = p.group(1)
            if "</tr>" in line:
                in_download = False

        if url is None and sha1sum is None:
            return (None, in_download)
        if url and url.startswith("//"):
            url = "https:" + url
        return ((url, sha1sum), in_download)


class AndroidStudio(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Android Studio", description=_("Android Studio (default)"), is_category_default=True,
                         only_on_archs=_supported_archs, expect_license=True,
                         packages_requirements=["openjdk-7-jdk | openjdk-8-jdk",
                                                "libncurses5:i386", "libstdc++6:i386", "zlib1g:i386"],
                         download_page="https://developer.android.com/studio/index.html",
                         checksum_type=ChecksumType.sha256,
                         dir_to_decompress_in_tarball="android-studio",
                         desktop_filename="android-studio.desktop",
                         required_files_path=[os.path.join("bin", "studio.sh")], **kwargs)

    def parse_license(self, line, license_txt, in_license):
        """Parse Android Studio download page for license"""
        return self.category.parse_license('<div id="studio_linux_bundle_download"', line, license_txt, in_license)

    def parse_download_link(self, line, in_download):
        """Parse Android Studio download link, expect to find a sha1sum and a url"""
        return self.category.parse_download_link('linux_bundle_download', line, in_download)

    def post_install(self):
        """Create the Android Studio launcher"""
        add_env_to_user(self.name, {"ANDROID_HOME": {"value": self.install_path, "keep": False},
                                    "ANDROID_SDK": {"value": self.install_path, "keep": False}})
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Android Studio"),
                        icon_path=os.path.join(self.install_path, "bin", "studio.png"),
                        try_exec=os.path.join(self.install_path, "bin", "studio.sh"),
                        exec=self.exec_link_name,
                        comment=_("Android Studio developer environment"),
                        categories="Development;IDE;",
                        extra="StartupWMClass=jetbrains-studio"))


class AndroidSDK(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Android SDK", description=_("Android SDK"),
                         only_on_archs=_supported_archs, expect_license=True,
                         packages_requirements=["openjdk-7-jdk | openjdk-8-jdk",
                                                "libncurses5:i386", "libstdc++6:i386", "zlib1g:i386"],
                         download_page="https://developer.android.com/studio/index.html",
                         checksum_type=ChecksumType.sha256,
                         dir_to_decompress_in_tarball=".",
                         required_files_path=[os.path.join("tools", "android"),
                                              os.path.join("tools", "bin", "sdkmanager")],
                         **kwargs)

    def parse_license(self, line, license_txt, in_license):
        """Parse Android SDK download page for license"""
        return self.category.parse_license('<div id="sdk_linux_download"', line, license_txt, in_license)

    def parse_download_link(self, line, in_download):
        """Parse Android SDK download link, expect to find a SHA-1 and a url"""
        return self.category.parse_download_link('sdk_linux_download', line, in_download)

    def post_install(self):
        """Add necessary environment variables"""
        # add a few fall-back variables that might be used by some tools
        # do not set ANDROID_SDK_HOME here as that is the path of the preference folder expected by the Android tools
        add_env_to_user(self.name, {"ANDROID_HOME": {"value": self.install_path, "keep": False},
                                    "ANDROID_SDK": {"value": self.install_path, "keep": False},
                                    "PATH": {"value": [os.path.join(self.install_path, "tools"),
                                                       os.path.join(self.install_path, "tools", "bin")]}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))

        # print wiki page message
        UI.delayed_display(DisplayMessage("SDK installed in {}. More information on how to use it on {}".format(
                                          self.install_path,
                                          "https://developer.android.com/sdk/installing/adding-packages.html")))


class AndroidPlatformTools(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Android Platform Tools", description=_("Android Platform Tools"),
                         only_on_archs=_supported_archs, expect_license=True,
                         # Install the android-sdk-platform-tools-common package for the udev rules
                         packages_requirements=['android-sdk-platform-tools-common'],
                         download_page="https://developer.android.com/studio/releases/platform-tools/index.html",
                         dir_to_decompress_in_tarball=".",
                         required_files_path=[os.path.join("platform-tools", "adb")],
                         **kwargs)

    def parse_license(self, line, license_txt, in_license):
        """Parse Android SDK download page for license"""
        return self.category.parse_license('<div class="dialog-content-stretch sdk-terms">',
                                           line, license_txt, in_license)

    def parse_download_link(self, line, in_download):
        """Parse Android SDK download link, expect to find a SHA-1 and a url"""
        return self.category.parse_download_link('dac-download-linux', line, in_download)

    def post_install(self):
        """Add necessary environment variables"""
        add_env_to_user(self.name, {"PATH": {"value": [os.path.join(self.install_path, "platform-tools")]}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))


class AndroidNDK(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Android NDK", description=_("Android NDK"),
                         only_on_archs='amd64', expect_license=True,
                         download_page="https://developer.android.com/ndk/downloads/index.html",
                         checksum_type=ChecksumType.sha1,
                         packages_requirements=['clang'],
                         dir_to_decompress_in_tarball="android-ndk-*",
                         required_files_path=[os.path.join("ndk-build")], **kwargs)

    def parse_license(self, line, license_txt, in_license):
        """Parse Android NDK download page for license"""
        return self.category.parse_license('<div id="ndk_linux64_download"', line, license_txt, in_license)

    def parse_download_link(self, line, in_download):
        """Parse Android NDK download link, expect to find a sha1sum and a url"""
        return self.category.parse_download_link('ndk_linux64_download', line, in_download)

    def post_install(self):
        """Add necessary environment variables"""
        # add a few fall-back variables that might be used by some tools
        add_env_to_user(self.name, {"NDK_ROOT": {"value": self.install_path, "keep": False},
                                    "ANDROID_NDK": {"value": self.install_path, "keep": False},
                                    "ANDROID_NDK_HOME": {"value": self.install_path, "keep": False}})

        # print wiki page message
        UI.display(DisplayMessage("NDK installed in {}. More information on how to use it on {}".format(
                                  self.install_path,
                                  "https://developer.android.com/tools/sdk/ndk/index.html#GetStarted")))


class EclipseADTForRemoval(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Eclipse ADT", description="For removal only (not supported upstream anymore)",
                         download_page=None, only_on_archs=_supported_archs, only_for_removal=True, **kwargs)
