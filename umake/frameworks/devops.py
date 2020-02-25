# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
#
# Authors:
#  Alexander Sidorenko
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


"""Devops module"""

from gettext import gettext as _
import logging
import os
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.ui import UI
from umake.tools import get_current_arch, add_env_to_user

logger = logging.getLogger(__name__)


class DevopsCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="devops", description=_("Devops Environment"), logo_path=None)


class Terraform(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Terraform", description=_("Infrastructure-as-code tool"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/hashicorp/terraform/releases/latest",
                         dir_to_decompress_in_tarball=".",
                         required_files_path=["terraform"],
                         json=True, **kwargs)

    arch_trans = {
        "amd64": "amd64",
        "i386": "386"
    }

    def parse_download_link(self, line, in_download):
        """Parse Terraform download links"""
        url = None
        tag_name = line["tag_name"]
        if tag_name:
            version = tag_name[1:]
            arch = self.arch_trans[get_current_arch()]
            url = "https://releases.hashicorp.com/terraform/{version}/terraform_{version}_linux_{arch}.zip".format(
                version=version, arch=arch)
        return url, in_download

    def post_install(self):
        """Add Terraform necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path)}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))
