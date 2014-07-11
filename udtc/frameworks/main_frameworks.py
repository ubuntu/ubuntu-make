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


"""Android module"""

from gettext import gettext as _
import logging
import os
import udtc.frameworks

logger = logging.getLogger(__name__)


class MainFramework1(udtc.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Framework 1", description="Main framework 1", category=category)

    def setup(self, install_path=None):
        super().setup()


class MainFramework2(udtc.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Framework 2", description="Main framework 2", category=category)

    def setup(self, install_path=None):
        # first step, check the license
        super().setup()
