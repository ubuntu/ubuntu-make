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

    # The mock server replaces the checksum path.
    # this emulates the php function without using the same
    # filename as the tar archive.
    # The relevant change can be found in local_server.py

    def setUp(self):
        self.hosts = {443: ["www.eclipse.org"], 80: ["www.eclipse.org"]}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
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
                                               "eclipse-packages", "index.html")
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))

    def test_install_with_changed_checksum_page(self):
        """Installing eclipse ide should fail if checksum link is unparseable"""
        self.bad_download_page_test(self.command(self.command_args), self.bad_download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))


class EclipseJEEIDEInContainer(ContainerTests, test_ide.EclipseJEEIDETests):
    """This will test the eclipse IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["www.eclipse.org"], 80: ["www.eclipse.org"]}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "eclipse-jee")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "www.eclipse.org", "technology", "epp",
                                                        "downloads", "release", "version", "point_release",
                                                        "eclipse-jee-linux-gtk-x86_64.tar.gz.sha512")


class EclipsePHPIDEInContainer(ContainerTests, test_ide.EclipsePHPIDETests):
    """This will test the eclipse IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["www.eclipse.org"], 80: ["www.eclipse.org"]}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "eclipse-php")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "www.eclipse.org", "technology", "epp",
                                                        "downloads", "release", "version", "point_release",
                                                        "eclipse-php-linux-gtk-x86_64.tar.gz.sha512")


class EclipseJSIDEInContainer(ContainerTests, test_ide.EclipseJSIDETests):
    """This will test the eclipse IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["www.eclipse.org"], 80: ["www.eclipse.org"]}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "eclipse-javascript")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "www.eclipse.org", "technology", "epp",
                                                        "downloads", "release", "version", "point_release",
                                                        "eclipse-javascript-linux-gtk-x86_64.tar.gz.sha512")


class EclipseCPPIDEInContainer(ContainerTests, test_ide.EclipseCPPIDETests):
    """This will test the eclipse IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["www.eclipse.org"], 80: ["www.eclipse.org"]}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
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
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "idea")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=IIC")

    # This actually tests the code in BaseJetBrains
    def test_install_with_changed_download_page(self):
        """Installing IntelliJ Idea should fail if download page has changed"""
        self.bad_download_page_test(self.command(self.command_args), self.bad_download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))


class IdeaUltimateIDEInContainer(ContainerTests, test_ide.IdeaUltimateIDETests):
    """This will test the Idea Ultimate IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "idea-ultimate")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=IIU")


class PyCharmIDEInContainer(ContainerTests, test_ide.PyCharmIDETests):
    """This will test the PyCharm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "pycharm")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=PCC")


class PyCharmEducationalIDEInContainer(ContainerTests, test_ide.PyCharmEducationalIDETests):
    """This will test the PyCharm Educational IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "pycharm-educational")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=PCE")


class PyCharmProfessionalIDEInContainer(ContainerTests, test_ide.PyCharmProfessionalIDETests):
    """This will test the PyCharm Professional IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "pycharm-professional")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=PCP")


class RubyMineIDEInContainer(ContainerTests, test_ide.RubyMineIDETests):
    """This will test the RubyMine IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'rubymine')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "rubymine")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=RM")


class WebStormIDEInContainer(ContainerTests, test_ide.WebStormIDETests):
    """This will test the WebStorm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "webstorm")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=WS")


class CLionIDEInContainer(ContainerTests, test_ide.CLionIDETests):
    """This will test the CLion IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "clion")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=CL")


class DataGripIDEInContainer(ContainerTests, test_ide.DataGripIDETests):
    """This will test the DataGrip IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "datagrip")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=DG")


class PhpStormIDEInContainer(ContainerTests, test_ide.PhpStormIDETests):
    """This will test the PhpStorm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "phpstorm")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=PS")


class GoLandIDEInContainer(ContainerTests, test_ide.GoLandIDETests):
    """This will test the GoLand IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "goland")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=GO")


class RiderIDEInContainer(ContainerTests, test_ide.RiderIDETests):
    """This will test the Rider IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["data.services.jetbrains.com", 'download.jetbrains.com']}
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'rider')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "rider")
        self.bad_download_page_file_path = os.path.join(get_data_dir(),
                                                        "server-content", "data.services.jetbrains.com",
                                                        "products", "releases?code=RD")


class BaseNetBeansInContainer(ContainerTests, test_ide.BaseNetBeansTests):
    """This will test the NetBeans IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10
    TEST_CHECKSUM_NETBEANS_DATA = "e5018c428b5657b669155886f58429af63f69436625e876be9710824bbfd144a"

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
        self.assertFalse(self.is_in_path(self.exec_link))

    def test_install_with_changed_download_reference_page(self):
        """Installing NetBeans ide should fail if download reference page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "netbeans.org", "images_www",
                                               "v6", "download", "8.2", "final", "js", "files.js")
        umake_command = self.command('{} ide netbeans'.format(UMAKE))
        self.bad_download_page_test(umake_command, download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))

    def test_install_with_changed_checksum_page(self):
        """Installing NetBeans ide should fail if checksum link is wrong"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "netbeans.org", "images_www",
                                               "v6", "download", "8.2", "final", "js", "files.js")
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
            self.assertFalse(self.is_in_path(self.exec_link))


class VisualStudioCodeInContainer(ContainerTests, test_ide.VisualStudioCodeTest):
    """This will test the Visual Studio Code integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["code.visualstudio.com", "go.microsoft.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'vscode')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "visual-studio-code")


class LightTableInContainer(ContainerTests, test_ide.LightTableTest):
    """This will test the LightTable integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["api.github.com", "github.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'LightTable')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "lighttable")

    def test_install_with_changed_download_page(self):
        """Installing LightTable should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "api.github.com",
                                               "repos", "LightTable", "LightTable", "releases", "latest")
        umake_command = self.command('{} ide lighttable'.format(UMAKE))
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))


class AtomInContainer(ContainerTests, test_ide.AtomTest):
    """This will test the Atom integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["api.github.com", "github.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'atom')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "atom")

    def test_install_with_changed_download_page(self):
        """Installing Atom should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "api.github.com",
                                               "repos", "Atom", "Atom", "releases", "latest")
        umake_command = self.command('{} ide atom'.format(UMAKE))
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))

    def test_install_beta_with_changed_download_page(self):
        """Installing Atom Beta should fail if the latest is not a beta"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "api.github.com",
                                               "repos", "Atom", "Atom", "releases", "index.html")
        with swap_file_and_restore(download_page_file_path) as content:
            with open(download_page_file_path, "w") as newfile:
                newfile.write(content.replace("-beta", ""))
            self.child = umake_command = self.command('{} ide atom --beta'.format(UMAKE))
            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
            self.assertFalse(self.is_in_path(self.exec_link))


class SublimeTextInContainer(ContainerTests, test_ide.SublimeTextTests):
    """This will test the Sublime Text integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["sublimetext.com", "download.sublimetext.com"]}
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "sublime-text")


class DBeaverInContainer(ContainerTests, test_ide.DBeaverTest):
    """This will test the DBeaver integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["api.github.com", "github.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'dbeaver')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "dbeaver")

    def test_install_with_changed_download_page(self):
        """Installing DBeaver should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "api.github.com",
                                               "repos", "DBeaver", "DBeaver", "releases", "latest")
        umake_command = self.command('{} ide dbeaver'.format(UMAKE))
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))


class SpringToolsSuiteInContainer(ContainerTests, test_ide.SpringToolsSuiteTest):
    """This will test Spring Tools Suite IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ['spring.io'], 80: ['download.springsource.com']}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
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
        self.assertFalse(self.is_in_path(self.exec_link))

    def test_install_with_changed_checksum_page(self):
        """Installing STS should fail if checksum link is unparseable"""
        download_page_file_path = os.path.join(get_data_dir(), 'server-content', 'download.springsource.com', 'release',
                                               'STS', 'mock.RELEASE', 'dist', 'emock',
                                               'spring-tool-suite-mock.RELEASE-emock-linux-gtk-x86_64.tar.gz.sha1')
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))


class ProcessingInContainer(ContainerTests, test_ide.ProcessingTests):
    """This will test the Processing integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["api.github.com", "github.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'arduino')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "processing")

    def test_install_with_changed_download_page(self):
        """Installing Processing should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "api.github.com",
                                               "repos", "processing", "processing", "releases", "latest")
        umake_command = self.command('{} ide processing'.format(UMAKE))
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))


class LiteIDEInContainer(ContainerTests, test_ide.LiteIDETests):
    """This will test the LiteIDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hosts = {443: ["api.github.com", "github.com"]}
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'liteide')
        super().setUp()
        # override with container path
        self.installed_path = os.path.join(self.install_base_path, "ide", "liteide")

    def test_install_with_changed_download_page(self):
        """Installing LiteIDE should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "api.github.com",
                                               "repos", "visualfc", "liteide", "releases", "latest")
        umake_command = self.command('{} ide liteide'.format(UMAKE))
        self.bad_download_page_test(self.command(self.command_args), download_page_file_path)
        self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assertFalse(self.is_in_path(self.exec_link))
