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
from ..tools import get_data_dir, swap_file_and_restore, UMAKE


class EclipseIDEInContainer(ContainerTests, test_ide.EclipseIDETests):
    """This will test the eclipse IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'eclipse')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse".format(self.DOCKER_USER))


class EclipseIDEInContainerFTP(ContainerTests, test_ide.EclipseIDETests):
    """This will test the Eclipse IDE integration inside a container, involving an FTP server."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        self.ftp = True
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'eclipse')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse".format(self.DOCKER_USER))


class IdeaIDEInContainer(ContainerTests, test_ide.IdeaIDETests):
    """This will test the Idea IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/idea".format(self.DOCKER_USER))

    # This actually tests the code in BaseJetBrains
    def test_install_with_changed_download_page(self):
        """Installing IntelliJ Idea should fail if download page has changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.jetbrains.com", "idea",
                                               "download", "download_thanks.jsp?edition=IC&os=linux")
        fake_content = "<html></html>"
        with swap_file_and_restore(download_page_file_path):
            with open(download_page_file_path, "w") as newfile:
                newfile.write(fake_content)
            self.child = pexpect.spawnu(self.command('{} ide idea'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("Can't parse the download URL from the download page.", expect_warn=True)
            self.wait_and_close(exit_status=1)

            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))


class IdeaUltimateIDEInContainer(ContainerTests, test_ide.IdeaUltimateIDETests):
    """This will test the Idea Ultimate IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/idea-ultimate".format(self.DOCKER_USER))


class PyCharmIDEInContainer(ContainerTests, test_ide.PyCharmIDETests):
    """This will test the PyCharm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/pycharm".format(self.DOCKER_USER))


class PyCharmEducationalIDEInContainer(ContainerTests, test_ide.PyCharmEducationalIDETests):
    """This will test the PyCharm Educational IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/pycharm-educational".format(self.DOCKER_USER))


class PyCharmProfessionalIDEInContainer(ContainerTests, test_ide.PyCharmProfessionalIDETests):
    """This will test the PyCharm Professional IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/pycharm-professional".format(self.DOCKER_USER))


class RubyMineIDEInContainer(ContainerTests, test_ide.RubyMineIDETests):
    """This will test the RubyMine IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/rubymine".format(self.DOCKER_USER))


class WebStormIDEInContainer(ContainerTests, test_ide.WebStormIDETests):
    """This will test the WebStorm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/webstorm".format(self.DOCKER_USER))


class PhpStormIDEInContainer(ContainerTests, test_ide.PhpStormIDETests):
    """This will test the PhpStorm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/phpstorm".format(self.DOCKER_USER))


class ArduinoIDEInContainer(ContainerTests, test_ide.ArduinoIDETests):
    """This will test the Arduino IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.arduino.cc"
        self.port = "80"
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'arduino')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/arduino".format(self.DOCKER_USER))

    def test_install_with_changed_download_page(self):
        """Installing arduino ide should fail if download page has significantly changed"""
        download_page_file_path = os.path.join(get_data_dir(), "server-content", "www.arduino.cc", "en", "Main",
                                               "Software")
        fake_content = "<html></html>"
        with swap_file_and_restore(download_page_file_path):
            with open(download_page_file_path, "w") as newfile:
                newfile.write(fake_content)
            self.child = pexpect.spawnu(self.command('{} ide arduino'.format(UMAKE)))
            self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
            self.child.sendline("")
            self.expect_and_no_warn("Can't parse the download link", expect_warn=True)
            self.wait_and_close(exit_status=1)

            self.assertFalse(self.launcher_exists_and_is_pinned(self.desktop_filename))
