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


"""Framework with another category module without any framework"""

import umake.frameworks


class ECategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Category E", description="Category E description")


class FrameworkA(umake.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Framework A", description="Description for framework A (installable chained to parent)",
                         category=category)

    def setup(self, install_path=None):
        super().setup()

    def remove(self):
        super().remove()

    @property
    def is_installable(self):
        return super().is_installable


class FrameworkB(umake.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Framework B", description="Description for framework B (installable forced to True even "
                                                         "with archs restrictions)",
                         category=category, only_on_archs=["archswhichdontexist"],
                         only_ubuntu_version=["versionwhichdontexist"])

    def setup(self, install_path=None):
        super().setup()

    def remove(self):
        super().remove()

    @property
    def is_installable(self):
        """overridden to say True"""
        return True


class FrameworkC(umake.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Framework C", description="Description for framework C (installable forced to False "
                                                         "even with no restriction",
                         category=category)

    def setup(self, install_path=None):
        super().setup()

    def remove(self):
        super().remove()

    @property
    def is_installable(self):
        """overridden to say False"""
        return False
