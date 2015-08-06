
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

"""Tests for the IDE category"""
import logging
import platform
import subprocess
import os
import pexpect
from tests.large import LargeFrameworkTests
from tests.tools import UMAKE

logger = logging.getLogger(__name__)


class BaseLargeIdeTest(LargeFrameworkTests):
    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.name = ""
        self.command_name = ""
        self.installed_path = ""
        self.desktop_filename = ""

    @property
    def arch_option(self):
        """we return the expected arch call on command line"""
        return platform.machine()

    def test_default_install(self):
        self.child = pexpect.spawnu(self.command('{0} ide {1}'.format(UMAKE, self.name)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", self.installed_path], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{0} ide {1}'.format(UMAKE, self.command_name)))
        self.expect_and_no_warn("{0} is already installed.*\[.*\] ".format(self.name))
        self.child.sendline()
        self.wait_and_no_warn()


class BaseLargeEclipseIdeTest(BaseLargeIdeTest):
    def test_default_install(self):
        self.child = pexpect.spawnu(self.command('{0} ide {1}'.format(UMAKE, self.name)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        # on 64 bits, there is a java subprocess, we kill that one with SIGKILL (eclipse isn't reliable on SIGTERM)
        if self.arch_option == "x86_64":
            self.check_and_kill_process(["java", self.arch_option, self.installed_path],
                                        wait_before=self.TIMEOUT_START, send_sigkill=True)
        else:
            self.check_and_kill_process([self.exec_path],
                                        wait_before=self.TIMEOUT_START, send_sigkill=True)

        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{0} ide {1}'.format(UMAKE, self.command_name)))
        self.expect_and_no_warn("{0} is already installed.*\[.*\] ".format(self.name))
        self.child.sendline()
        self.wait_and_no_warn()


class EclipseIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse"
        self.command_name = "eclipse"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse")
        self.desktop_filename = "eclipse.desktop"


class EclipseJavaIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars Java distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse Java"
        self.command_name = "eclipse-java"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-java")
        self.desktop_filename = "eclipse-java.desktop"


class EclipseEEIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars EE distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse EE"
        self.command_name = "eclipse-ee"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-ee")
        self.desktop_filename = "eclipse-ee.desktop"


class EclipseCppIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars C/C++ distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse C/Cpp"
        self.command_name = "eclipse-c-cpp"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-cpp")
        self.desktop_filename = "eclipse-c-cpp.desktop"


class EclipsePhpIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars PHP distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse PHP"
        self.command_name = "eclipse-php"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-php")
        self.desktop_filename = "eclipse-php.desktop"


class EclipseCommittersIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars Committers distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse Committers"
        self.command_name = "eclipse-committers"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-committers")
        self.desktop_filename = "eclipse-committers.desktop"


class EclipseDslIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars Java and DSL distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse DSL"
        self.command_name = "eclipse-dsl"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-dsl")
        self.desktop_filename = "eclipse-dsl.desktop"


class EclipseRcpAndRapIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars RCP and RAP distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse RCP"
        self.command_name = "eclipse-rcp"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-rcp")
        self.desktop_filename = "eclipse-rcp.desktop"


class EclipseModelingToolsIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars Modeling Tools distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse Modeling"
        self.command_name = "eclipse-modeling"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-modeling")
        self.desktop_filename = "eclipse-modeling.desktop"


class EclipseReportIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars Java and Report distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse Report"
        self.command_name = "eclipse-report"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-report")
        self.desktop_filename = "eclipse-report.desktop"


class EclipseAutomotiveIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars Automotive Software distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse Automotive"
        self.command_name = "eclipse-automotive"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-automotive")
        self.desktop_filename = "eclipse-automotive.desktop"


class EclipseTestersIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars Testers distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse Testers"
        self.command_name = "eclipse-testers"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-testers")
        self.desktop_filename = "eclipse-testing.desktop"


class EclipseParallelIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars Parallel distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse Parallel"
        self.command_name = "eclipse-parallel"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-parallel")
        self.desktop_filename = "eclipse-parallel.desktop"


class EclipseScoutIDETests(BaseLargeEclipseIdeTest):
    """The Eclipse Mars Scout distribution from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Eclipse Scout"
        self.command_name = "eclipse-scout"
        self.installed_path = os.path.expanduser("~/tools/ide/eclipse-scout")
        self.desktop_filename = "eclipse-scout.desktop"


class IdeaIDETests(BaseLargeIdeTest):
    """IntelliJ Idea from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Idea"
        self.command_name = "idea"
        self.installed_path = os.path.expanduser("~/tools/ide/idea")
        self.desktop_filename = 'jetbrains-idea.desktop'


class IdeaUltimateIDETests(BaseLargeIdeTest):
    """IntelliJ Idea Ultimate from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "Idea Ultimate"
        self.command_name = "idea-ultimate"
        self.installed_path = os.path.expanduser("~/tools/ide/idea-ultimate")
        self.desktop_filename = "jetbrains-idea.desktop"


class PyCharmIDETests(BaseLargeIdeTest):
    """PyCharm from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "PyCharm"
        self.command_name = "pycharm"
        self.installed_path = os.path.expanduser("~/tools/ide/pycharm")
        self.desktop_filename = 'jetbrains-pycharm.desktop'


class PyCharmEducationalIDETests(BaseLargeIdeTest):
    """PyCharm Educational from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "PyCharm Educational"
        self.command_name = "pycharm-educational"
        self.installed_path = os.path.expanduser("~/tools/ide/pycharm-educational")
        self.desktop_filename = 'jetbrains-pycharm.desktop'


class PyCharmProfessionalIDETests(BaseLargeIdeTest):
    """PyCharm Professional from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "PyCharm Professional"
        self.command_name = "pycharm-professional"
        self.installed_path = os.path.expanduser("~/tools/ide/pycharm-professional")
        self.desktop_filename = 'jetbrains-pycharm.desktop'


class RubyMineIDETests(BaseLargeIdeTest):
    """RubyMine from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "RubyMine"
        self.command_name = "rubymine"
        self.installed_path = os.path.expanduser("~/tools/ide/rubymine")
        self.desktop_filename = 'jetbrains-rubymine.desktop'


class WebStormIDETests(BaseLargeIdeTest):
    """WebStorm from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "WebStorm"
        self.command_name = "webstorm"
        self.installed_path = os.path.expanduser("~/tools/ide/webstorm")
        self.desktop_filename = 'jetbrains-webstorm.desktop'


class PhpStormIDETests(BaseLargeIdeTest):
    """PhpStorm from the IDE collection."""

    def setUp(self):
        super().setUp()
        self.name = "PhpStorm"
        self.command_name = "phpstorm"
        self.installed_path = os.path.expanduser("~/tools/ide/phpstorm")
        self.desktop_filename = 'jetbrains-phpstorm.desktop'


class ArduinoIDETests(LargeFrameworkTests):
    """The Arduino Software distribution from the IDE collection."""

    TIMEOUT_INSTALL_PROGRESS = 120
    TIMEOUT_START = 60
    TIMEOUT_STOP = 60

    def setUp(self):
        super().setUp()
        self.installed_path = os.path.expanduser("~/tools/ide/arduino")
        self.desktop_filename = "arduino.desktop"

    @property
    def arch_option(self):
        """we return the expected arch call on command line"""
        return platform.machine()

    def test_default_install(self):
        """Install the distribution from scratch test case"""
        self.child = pexpect.spawnu(self.command('{} ide arduino'.format(UMAKE)))
        self.expect_and_no_warn("Choose installation path: {}".format(self.installed_path))
        self.child.sendline("")
        self.expect_and_no_warn("Installation done", timeout=self.TIMEOUT_INSTALL_PROGRESS)
        self.wait_and_no_warn()

        # we have an installed launcher, added to the launcher and an icon file
        self.assertTrue(self.launcher_exists_and_is_pinned(self.desktop_filename))
        self.assert_exec_exists()
        self.assert_icon_exists()
        self.assertTrue(self.is_in_group("dialout"))

        # launch it, send SIGTERM and check that it exits fine
        proc = subprocess.Popen(self.command_as_list(self.exec_path), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        self.check_and_kill_process(["java", "processing.app.Base"], wait_before=self.TIMEOUT_START)
        proc.wait(self.TIMEOUT_STOP)

        # ensure that it's detected as installed:
        self.child = pexpect.spawnu(self.command('{} ide arduino'.format(UMAKE)))
        self.expect_and_no_warn("Arduino is already installed.*\[.*\] ")
        self.child.sendline()
        self.wait_and_no_warn()
