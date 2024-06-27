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

import os
import requests
from xdg.BaseDirectory import xdg_data_home

DEFAULT_INSTALL_TOOLS_PATH = os.path.expanduser(os.path.join(xdg_data_home, "umake"))
DEFAULT_BINARY_LINK_PATH = os.path.expanduser(os.path.join(DEFAULT_INSTALL_TOOLS_PATH, "bin"))
OLD_CONFIG_FILENAME = "udtc"
CONFIG_FILENAME = "umake"
OS_RELEASE_FILE = "/etc/os-release"
UMAKE_FRAMEWORKS_ENVIRON_VARIABLE = "UMAKE_FRAMEWORKS"

from_dev = False


def get_version():
    '''Get version depending if on dev or released version'''
    version = open(os.path.join(os.path.dirname(__file__), 'version'), 'r', encoding='utf-8').read().strip()
    if not from_dev:
        snap_appendix = ''
        snap_rev = os.getenv('SNAP_REVISION')
        if snap_rev:
            snap_appendix = '+snap{}'.format(snap_rev)
        return version + snap_appendix
    import subprocess
    try:
        # use git describe to get a revision ref if running from a branch. Will append dirty if local changes
        version = subprocess.check_output(["git", "describe", "--tags", "--dirty"]).decode('utf-8').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        version += "+unknown"
    return version


def get_latest_version():
    '''Get latest available version from github'''
    try:
        page = requests.get("https://api.github.com/repos/ubuntu/ubuntu-make/releases/latest")
        page.raise_for_status()
    except Exception as e:
        raise e
    latest = page.json().get("tag_name")
    return latest
