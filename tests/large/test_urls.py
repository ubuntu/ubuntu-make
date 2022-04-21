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

"""Tests for large base installer framework"""

from . import LargeFrameworkTests

from ..tools import UMAKE, spawn_process


class UrlFetchTests(LargeFrameworkTests):
    """This will test the base installer framework via a fake one"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()

    def test_android_ndk_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} android android-ndk --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_android_platform_tools_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} android android-platform-tools --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_android_sdk_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} android android-sdk --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_android_studio_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} android android-studio --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_crystal_lang_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} crystal crystal-lang --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_dart_sdk_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} dart dart-sdk --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_flutter_sdk_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} dart flutter-sdk --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_terraform_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} devops terraform --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_arduino_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} electronics arduino --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_eagle_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} electronics eagle --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_blender_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} games blender --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_godot_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} games godot --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_superpowers_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} games superpowers --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_twine_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} games twine --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_go_lang_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} go go-lang --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_atom_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide atom --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_clion_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide clion --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_dbeaver_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide dbeaver --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_datagrip_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide datagrip --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_eclipse_cpp_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide eclipse-cpp --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_eclipse_jee_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide eclipse-jee --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_eclipse_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide eclipse --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_eclipse_php_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide eclipse-php --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_goland_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide goland --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_idea_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide idea --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_idea_ultimate_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide idea-ultimate --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_lighttable_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide lighttable --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_liteide_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide liteide --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_netbeans_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide netbeans --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_phpstorm_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide phpstorm --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_processing_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide processing --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_pycharm_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide pycharm --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_pycharm_educational_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide pycharm-educational --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_pycharm_professional_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide pycharm-professional --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_rstudio_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide rstudio --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_rider_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide rider --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_rubymine_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide rubymine --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_spring_tools_suite_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide spring-tools-suite --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_sublime_text_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide sublime-text --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_vscodium_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide vscodium --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_visual_studio_code_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide visual-studio-code --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_webstorm_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} ide webstorm --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_adoptopenjdk_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} java adoptopenjdk --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_openjfx_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} java openjfx --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_kotlin_lang_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} kotlin kotlin-lang --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_maven_lang_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} maven maven-lang --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_nodejs_lang_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} nodejs nodejs-lang --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_rust_lang_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} rust rust-lang --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_scala_lang_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} scala scala-lang --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_swift_lang_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} swift swift-lang --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_chromedriver_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} web chromedriver --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_firefox_dev_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} web firefox-dev --lang en-US --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_geckodriver_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} web geckodriver --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")

    def test_phantomjs_install(self):
        """Install base installer from scratch test case"""
        self.child = spawn_process(self.command(f'{UMAKE} web phantomjs --dry-run'))
        self.expect_and_no_warn("Found download URL:.*")
