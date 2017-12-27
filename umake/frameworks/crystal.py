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


"""Go module"""

from contextlib import suppress
from gettext import gettext as _
import json
import logging
import os
import re
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.tools import get_current_arch, add_env_to_user, ChecksumType, MainLoop
from umake.network.download_center import DownloadItem
from umake.ui import UI

logger = logging.getLogger(__name__)


class CrystalCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Crystal", description=_("Crystal language"),
                         logo_path=None)


class CrystalLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Crystal Lang", description=_("Crystal compiler (default)"), is_category_default=True,
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/crystal-lang/crystal/releases/latest",
                         packages_requirements=["libbsd-dev", "libedit-dev", "libevent-dev",
                                                "libevent-core-2.0-5 | libevent-core-2.1-6",
                                                "libevent-extra-2.0-5 | libevent-extra-2.1-6",
                                                "libevent-openssl-2.0-5 | libevent-openssl-2.1-6",
                                                "libevent-pthreads-2.0-5 | libevent-pthreads-2.1-6",
                                                "libgmp-dev", "libgmpxx4ldbl", "libssl-dev",
                                                "libxml2-dev", "libyaml-dev", "libreadline-dev",
                                                "automake", "libtool", "llvm", "libpcre3-dev",
                                                "build-essential", "libgc-dev"],
                         dir_to_decompress_in_tarball="crystal-*",
                         required_files_path=[os.path.join("bin", "Crystal")],
                         **kwargs)

    arch_trans = {
        "amd64": "x86_64",
        "i386": "i686"
    }

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
            download_url = None
            for asset in assets:
                if "linux-{}.tar.gz".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                    download_url = asset["browser_download_url"]
            if not download_url:
                raise IndexError
        except (json.JSONDecodeError, IndexError):
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download URL: " + download_url)

        self.download_requests.append(DownloadItem(download_url, None))
        self.start_download_and_install()

    def post_install(self):
        """Add Crystal necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
