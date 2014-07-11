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

"""Tests for the decompressor module"""

import os
from time import time
from unittest.mock import Mock
import shutil
import subprocess
import tempfile
from ..tools import get_data_dir, LoggedTestCase
from udtc.decompressor import Decompressor


class BasicCLI(LoggedTestCase):
    """This will test the basic cli command class"""

    def test_global_help(self):
        """We display a global help message"""
        subprocess.call(['./developer-tools-center', '--help'])
