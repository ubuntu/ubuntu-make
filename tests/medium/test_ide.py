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


class EclipseIDEInContainer(ContainerTests, test_ide.EclipseIDETests):
    """This will test the Eclipse Luna IDE integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse".format(self.DOCKER_USER))


class EclipseJavaIDEInContainer(ContainerTests, test_ide.EclipseJavaIDETests):
    """This will test the Eclipse Mars Java IDE integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-java".format(self.DOCKER_USER))


class EclipseEEIDEInContainer(ContainerTests, test_ide.EclipseEEIDETests):
    """This will test the Eclipse Mars EE IDE integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-ee".format(self.DOCKER_USER))


class EclipseCppIDEInContainer(ContainerTests, test_ide.EclipseCppIDETests):
    """This will test the Eclipse Mars C/C++ IDE integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-c-cpp".format(self.DOCKER_USER))


class EclipsePhpIDEInContainer(ContainerTests, test_ide.EclipsePhpIDETests):
    """This will test the Eclipse Mars PHP IDE integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-php".format(self.DOCKER_USER))


class EclipseCommittersIDEInContainer(ContainerTests, test_ide.EclipseCommittersIDETests):
    """This will test the Eclipse Mars Committers IDE integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-committers".format(self.DOCKER_USER))


class EclipseDslIDEInContainer(ContainerTests, test_ide.EclipseDslIDETests):
    """This will test the Eclipse Mars Java and DSL IDE integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-dsl".format(self.DOCKER_USER))


class EclipseRcpAndRapIDEInContainer(ContainerTests, test_ide.EclipseRcpAndRapIDETests):
    """This will test the Eclipse Mars RCP and RAP IDE integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-rcp".format(self.DOCKER_USER))


class EclipseModelingToolsIDEInContainer(ContainerTests, test_ide.EclipseModelingToolsIDETests):
    """This will test the Eclipse Mars Modeling Tools integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-modeling".format(self.DOCKER_USER))


class EclipseReportIDEInContainer(ContainerTests, test_ide.EclipseReportIDETests):
    """This will test the Eclipse Mars Java and Report integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-report".format(self.DOCKER_USER))


class EclipseAutomotiveIDEInContainer(ContainerTests, test_ide.EclipseAutomotiveIDETests):
    """This will test the Eclipse Mars Automotive integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-automotive".format(self.DOCKER_USER))


class EclipseTestersIDEInContainer(ContainerTests, test_ide.EclipseTestersIDETests):
    """This will test the Eclipse Mars Testers integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-testing".format(self.DOCKER_USER))


class EclipseParallelIDEInContainer(ContainerTests, test_ide.EclipseParallelIDETests):
    """This will test the Eclipse Mars Parallel integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-parallel".format(self.DOCKER_USER))


class EclipseScoutIDEInContainer(ContainerTests, test_ide.EclipseScoutIDETests):
    """This will test the Eclipse Mars Scout integration inside a container."""

    TIMEOUT_START = 20
    TIMEOUT_STOP = 10

    def setUp(self):
        self.hostname = "www.eclipse.org"
        self.port = "443"
        # we reuse the android-studio repo
        self.apt_repo_override_path = os.path.join(self.APT_FAKE_REPO_PATH, 'android')
        super().setUp()
        # override with container path
        self.installed_path = os.path.expanduser("/home/{}/tools/ide/eclipse-scout".format(self.DOCKER_USER))


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
