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


"""Database module"""

from gettext import gettext as _
import logging
import os
import umake.frameworks.baseinstaller
from umake.tools import add_exec_link, get_current_arch

logger = logging.getLogger(__name__)


class DatabaseCategory(umake.frameworks.BaseCategory):
    def __init__(self):
        super().__init__(
            name="Database", description=_("Database and DBMS tools"), logo_path=None
        )


class DuckDB(umake.frameworks.baseinstaller.BaseInstaller):
    def __init__(self, **kwargs):
        super().__init__(
            name="DuckDB",
            description=_(
                " DuckDB is an in-process SQL OLAP Database Management System."
            ),
            only_on_archs=["aarch64", "amd64"],
            download_page="https://api.github.com/repos/duckdb/duckdb/releases/latest",
            dir_to_decompress_in_tarball=".",
            required_files_path=["duckdb"],
            json=True,
            **kwargs,
        )

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if asset["browser_download_url"].endswith(
                f"cli-linux-{get_current_arch()}.zip"
            ):
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Add the DuckDB binary to PATH"""
        add_exec_link(
            os.path.join(self.install_path, self.required_files_path[0]), "duckdb"
        )
        # add_env_to_user(self.name, {"PATH": {"value": self.install_path}})
        # UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
