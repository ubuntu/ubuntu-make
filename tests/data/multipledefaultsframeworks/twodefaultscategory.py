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


"""Framework with two defaults frameworks"""

import umake.frameworks


class ACategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Category A", description="Category A description")


class FrameworkA(umake.frameworks.BaseFramework):

    def __init__(self, **kwargs):
        super().__init__(name="Framework A", description="Description for framework A", is_category_default=True,
                         install_path_dir="custom/frameworka", **kwargs)

    def setup(self, install_path=None, auto_accept_license=False):
        super().setup()

    def remove(self):
        super().remove()

    def depends(self):
        super().depends()


class FrameworkB(umake.frameworks.BaseFramework):

    def __init__(self, **kwargs):
        super().__init__(name="Framework B", description="Description for framework B", is_category_default=True,
                         **kwargs)

    def setup(self, install_path=None, auto_accept_license=False):
        super().setup()

    def remove(self):
        super().remove()

    def depends(self):
        super().depends()
