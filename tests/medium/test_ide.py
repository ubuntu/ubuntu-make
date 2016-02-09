# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Didier Roche
#  Tin Tvrtković
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

"""Tests for ides"""

from . import ContainerTests
import os
import pexpect

from ..large import test_ide
from ..tools import get_data_dir, swap_file_and_restore, UMAKE, spawn_process


class EclipseJavaIDEInContainer(ContainerTests, test_ide.EclipseJavaIDETests):
    """This will test the eclipse IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["www.eclipse.org"]}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'eclipse')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "eclipse")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "www.eclipse.org", "technology", "epp",
                                                        "downloads", "release", "version", "point_release",
                                                        "eclipse-java-linux-gtk-x86_64.tar.gz.sha512")

    def test_install_with_changed_download_page(self):
        """Installing eclipse ide should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.eclipse.org", "downloads",
                                               "index.html")
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))

    def test_install_with_changed_checksum_page(self):
        """Installing eclipse ide should fail if checksum link is unparseable"""
        self.bad_download_page_test(self.command(self.command_args), self.bad_download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))


class EclipsePHPIDEInContainer(ContainerTests, test_ide.EclipsePHPIDETests):
    """This will test the eclipse IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["www.eclipse.org"]}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'eclipse')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "eclipse-php")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "www.eclipse.org", "technology", "epp",
                                                        "downloads", "release", "version", "point_release",
                                                        "eclipse-php-linux-gtk-x86_64.tar.gz.sha512")


class EclipseCPPIDEInContainer(ContainerTests, test_ide.EclipseCPPIDETests):
    """This will test the eclipse IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["www.eclipse.org"]}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'eclipse')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "eclipse-cpp")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "www.eclipse.org", "technology", "epp",
                                                        "downloads", "release", "version", "point_release",
                                                        "eclipse-cpp-linux-gtk-x86_64.tar.gz.sha512")


class IdeaIDEInContainer(ContainerTests, test_ide.IdeaIDETests):
    """This will test the Idea IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "idea")

    # This actually tests the code in BaseJetBrains
    def test_install_with_changed_download_page(self):
        """Installing IntelliJ Idea should fail if download page has changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "data.services.jetbrains.com",
                                               "products", "releases?code=IIC")
        umake_command = self.command('{} ide idea'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))


class IdeaUltimateIDEInContainer(ContainerTests, test_ide.IdeaUltimateIDETests):
    """This will test the Idea Ultimate IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "idea-ultimate")


class PyCharmIDEInContainer(ContainerTests, test_ide.PyCharmIDETests):
    """This will test the PyCharm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "pycharm")


class PyCharmEducationalIDEInContainer(ContainerTests, test_ide.PyCharmEducationalIDETests):
    """This will test the PyCharm Educational IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "pycharm-educational")


class PyCharmProfessionalIDEInContainer(ContainerTests, test_ide.PyCharmProfessionalIDETests):
    """This will test the PyCharm Professional IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "pycharm-professional")


class RubyMineIDEInContainer(ContainerTests, test_ide.RubyMineIDETests):
    """This will test the RubyMine IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "rubymine")


class WebStormIDEInContainer(ContainerTests, test_ide.WebStormIDETests):
    """This will test the WebStorm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "webstorm")


class CLionIDEInContainer(ContainerTests, test_ide.CLionIDETests):
    """This will test the CLion IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "clion")


class DataGripIDEInContainer(ContainerTests, test_ide.DataGripIDETests):
    """This will test the DataGrip IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "datagrip")


class PhpStormIDEInContainer(ContainerTests, test_ide.PhpStormIDETests):
    """This will test the PhpStorm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "phpstorm")


class ArduinoIDEInContainer(ContainerTests, test_ide.ArduinoIDETests):
    """This will test the Arduino IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {80: ["www.arduino.cc"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'arduino')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "arduino")

    def test_install_with_changed_download_page(self):
        """Installing arduino ide should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.arduino.cc", "en", "Main",
                                               "Software")
        umake_command = self.command('{} ide arduino'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))

    def test_install_with_changed_checksum_page(self):
        """Installing arduino ide should fail if checksum link is unparseable"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.arduino.cc",
                                               "checksums.md5sum.txt")
        umake_command = self.command('{} ide arduino'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))


class BaseNetBeansInContainer(ContainerTests, test_ide.BaseNetBeansTests):
    """This will test the NetBeans IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10
    TEST_CHECKSUM_NETBEANS_DATA = "1e07ec8775939ba6d35731831bdb7bf0"

    def setUp(self):
        self.hosts = {80: ["download.netbeans.org"], 443: ["netbeans.org"]}
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "netbeans")

    def test_install_with_changed_download_page(self):
        """Installing NetBeans ide should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "netbeans.org", "downloads",
                                               "zip.html")
        umake_command = self.command('{} ide netbeans'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))

    def test_install_with_changed_download_reference_page(self):
        """Installing NetBeans ide should fail if download reference page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "netbeans.org", "images_www",
                                               "v6", "download", "8.0.42", "js", "files.js")
        umake_command = self.command('{} ide netbeans'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))

    def test_install_with_changed_checksum_page(self):
        """Installing NetBeans ide should fail if checksum link is wrong"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "netbeans.org", "images_www",
                                               "v6", "download", "8.0.42", "js", "files.js")
        with swap_file_and_restore(download_page_file_path) as content:
            with open(download_page_file_path, "w") as newfile:
                newfile.write(content.replace(self.TEST_CHECKSUM_NETBEANS_DATA, "abcdef"))
            self.child = spawn_process(self.command('{} ide netbeans'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn([pexpect.EOF, "Corrupted download? Aborting."],
                                    timeout=self.TIMEOUT_INSTALL_PROGRESS, expect_warn=True)
            self.wait_and_close(exit_status=1)

            # we have nothing installed
            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))


class VisualStudioCodeInContainer(ContainerTests, test_ide.VisualStudioCodeTest):
    """This will test the Visual Studio Code integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["code.visualstudio.com"], 80: ["go.microsoft.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'vscode')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "visual-studio-code")


class LightTableInContainer(ContainerTests, test_ide.LightTableTest):
    """This will test the LightTable integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["github.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'LightTable')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "lighttable")

    def test_install_with_changed_download_page(self):
        """Installing LightTable should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "github.com", "LightTable",
                                               "LightTable", "releases", "index.html")
        umake_command = self.command('{} ide lighttable'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))


class SpringToolsSuiteInContainer(ContainerTests, test_ide.SpringToolsSuiteTest):
    """This will test Spring Tools Suite IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ['spring.io'], 80: ['dist.springsource.com']}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'eclipse')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "spring-tools-suite")

    def test_install_with_changed_download_page(self):
        """Installing STS should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "spring.io", "tools", "sts",
                                               "all")
        umake_command = self.command('{} ide spring-tools-suite'.format(UMAKE))
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))

    def test_install_with_changed_checksum_page(self):
        """Installing STS should fail if checksum link is unparseable"""
        download_page_file_path = os.path.join(get_data_dir(), 'server-content', 'dist.springsource.com', 'release',
                                               'STS', '3.7.2.RELEASE', 'dist', 'e4.5',
                                               'spring-tool-suite-3.7.2.RELEASE-e4.5.1-linux-gtk-x86_64.tar.gz.sha1')
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(os.path.join(self.binary_dir, self.desktop_filename.split('.')[0])))
