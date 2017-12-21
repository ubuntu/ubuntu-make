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

from gettext import gettext as _
import json
import logging
import os
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.tools import get_current_arch, add_env_to_user, MainLoop
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
                         json=True, **kwargs)

    arch_trans = {
        "amd64": "x86_64",
        "i386": "i686"
    }

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if "linux-{}.tar.gz".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Add Crystal necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
