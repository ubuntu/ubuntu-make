# -*- coding: utf-8 -*-
# Copyright (C) 2016 Canonical
#
# Authors:
#  Omer Sheikh
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

"""Kotlin module"""

from gettext import gettext as _
import logging
import os
import json
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.tools import add_env_to_user, MainLoop
from umake.ui import UI
from umake.network.download_center import DownloadItem

logger = logging.getLogger(__name__)


class KotlinCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Kotlin", description=_("The Kotlin Programming Language"), logo_path=None)


class KotlinLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Kotlin Lang", description=_("Kotlin language standalone compiler"),
                         is_category_default=True, category=category,
                         packages_requirements=["openjdk-7-jre | openjdk-8-jre"],
                         download_page="https://api.github.com/repos/Jetbrains/kotlin/releases/latest",
                         dir_to_decompress_in_tarball="kotlinc",
                         required_files_path=[os.path.join("bin", "kotlinc")])

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        logger.debug("Fetched download page, parsing.")

        page = result[self.download_page]

        error_msg = page.error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        try:
            assets = json.loads(page.buffer.read().decode())["assets"]
            download_url = assets[0]["browser_download_url"]
        except (json.JSONDecodeError, IndexError):
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download URL: " + download_url)

        self.download_requests.append(DownloadItem(download_url, None))
        self.start_download_and_install()

    def post_install(self):
        """Add the Kotlin binary dir to PATH"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(self.POST_INSTALL_WARN.format(self.name)))
