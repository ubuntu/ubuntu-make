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


"""Framework with package requirements"""

import umake.frameworks


class CategoryF(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Category F", description="Category F to test installed state")


class FrameworkA(umake.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Framework A", description="Description for framework A (impossible path)",
                         category=category, install_path_dir="/foo/bar/baz")

    def setup(self, install_path=None):
        super().setup()

    def remove(self):
        super().remove()


class FrameworkB(umake.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Framework B", description="Description for framework B (good install dir, "
                                                         "no package req)",
                         category=category, install_path_dir="/")

    def setup(self, install_path=None):
        super().setup()

    def remove(self):
        super().remove()


class FrameworkC(umake.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Framework C", description="Description for framework C (good install dir, package req.)",
                         category=category, install_path_dir="/", packages_requirements=["foo", "bar"])

    def setup(self, install_path=None):
        super().setup()

    def remove(self):
        super().remove()
