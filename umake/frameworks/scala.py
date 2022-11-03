# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
#
# Authors:
#  Didier Roche
#  Igor Vuk
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


"""Scala module"""

from gettext import gettext as _
import logging
import os
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.tools import add_env_to_user
from umake.ui import UI

logger = logging.getLogger(__name__)


class ScalaCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Scala", description=_("The Scala Programming Language"), logo_path=None)


class ScalaLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Scala Lang", description=_("Scala compiler and interpreter (default)"),
                         is_category_default=True,
                         packages_requirements=["openjdk-7-jre | openjdk-8-jre"],
                         download_page="https://api.github.com/repos/lampepfl/dotty/releases/latest",
                         dir_to_decompress_in_tarball="scala-*",
                         required_files_path=[os.path.join("bin", "scala")],
                         json=True, **kwargs)

    def parse_download_link(self, line, in_download):
        """Parse Scala download link, expect to find a url"""
        url = None
        for asset in line["assets"]:
            if ".tar." in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Add the necessary Scala environment variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")},
                                    "SCALA_HOME": {"value": self.install_path}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
