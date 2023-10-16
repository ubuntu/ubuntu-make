# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Galileo Sartor
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


"""Logic module"""
import re
from gettext import gettext as _
import logging
import os
import umake.frameworks.baseinstaller
from umake.tools import create_launcher, get_application_desktop_file
from umake.ui import UI

logger = logging.getLogger(__name__)


class LogicCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Logic", description=_("Tools for Logic and knowledge modelling"),
                         logo_path=None)


class Protege(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Protege",
                         description=_("Protege is an OWL ontology development environment."),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/protegeproject/protege-distribution/releases/latest",
                         dir_to_decompress_in_tarball="Protege-*",
                         required_files_path=["protege"],
                         desktop_filename="protege.desktop",
                         json=True, **kwargs)

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if asset["browser_download_url"].endswith("linux.tar.gz"):
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Create the Protege launcher"""
        icon_path = os.path.join(self.install_path, "app/Protege.ico")
        comment = self.description
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=self.name,
                                                     icon_path=icon_path,
                                                     try_exec=self.exec_path,
                                                     exec=self.exec_link_name,
                                                     comment=comment,
                                                     categories=categories))

    def parse_latest_version_from_package_url(self):
        return (re.search(r'/protege-(\d+\.\d+\.\d+)/', self.package_url).group(1)
                if self.package_url else 'Missing information')

    @staticmethod
    def get_current_user_version(install_path):
        return 'Missing information'
