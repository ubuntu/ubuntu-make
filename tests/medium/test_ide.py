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
from ..large import test_ide
from umake import settings


class EclipseIDEInContainer(ContainerTests, test_ide.EclipseIDETests):
    """This will test the eclipse IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'eclipse')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse".format(settings.DOCKER_USER))


class EclipseIDEInContainerFTP(ContainerTests, test_ide.EclipseIDETests):
    """This will test the Eclipse IDE integration inside a container, involving an FTP server."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        self.ftp = True
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'eclipse')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse".format(settings.DOCKER_USER))


class IdeaIDEInContainer(ContainerTests, test_ide.IdeaIDETests):
    """This will test the Idea IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/idea".format(settings.DOCKER_USER))


class IdeaUltimateIDEInContainer(ContainerTests, test_ide.IdeaUltimateIDETests):
    """This will test the Idea Ultimate IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/idea-ultimate".format(settings.DOCKER_USER))


class PyCharmIDEInContainer(ContainerTests, test_ide.PyCharmIDETests):
    """This will test the PyCharm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/pycharm".format(settings.DOCKER_USER))


class PyCharmEducationalIDEInContainer(ContainerTests, test_ide.PyCharmEducationalIDETests):
    """This will test the PyCharm Educational IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/pycharm-educational".format(settings.DOCKER_USER))


class PyCharmProfessionalIDEInContainer(ContainerTests, test_ide.PyCharmProfessionalIDETests):
    """This will test the PyCharm Professional IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/pycharm-professional".format(settings.DOCKER_USER))


class RubyMineIDEInContainer(ContainerTests, test_ide.RubyMineIDETests):
    """This will test the RubyMine IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/rubymine".format(settings.DOCKER_USER))


class WebStormIDEInContainer(ContainerTests, test_ide.WebStormIDETests):
    """This will test the WebStorm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/webstorm".format(settings.DOCKER_USER))


class PhpStormIDEInContainer(ContainerTests, test_ide.PhpStormIDETests):
    """This will test the PhpStorm IDE integration inside a container"""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.jetbrains.com"
        self.port = "443"
        # Reuse the Android Studio environment.
        self.apt_repo_override_path = os.path.join(settings.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/phpstorm".format(settings.DOCKER_USER))
