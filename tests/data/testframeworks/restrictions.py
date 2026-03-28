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


class DCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Category D", description="Category D description (with restricted frameworks)")


class FrameworkA(umake.frameworks.BaseFramework):

    def __init__(self, **kwargs):
        super().__init__(name="Framework A", description="Description for framework A (restricted arch)",
                         only_on_archs=["foo", "baz"], **kwargs)

    def setup(self, install_path=None, auto_accept_license=False):
        super().setup()

    def remove(self):
        super().remove()

    def depends(self):
        super().depends()


class FrameworkB(umake.frameworks.BaseFramework):

    def __init__(self, **kwargs):
        super().__init__(name="Framework B", description="Description for framework B (restricted version)",
                         only_ubuntu_version=["9.10", "10.04"], **kwargs)

    def setup(self, install_path=None, auto_accept_license=False):
        super().setup()

    def remove(self):
        super().remove()

    def depends(self):
        super().depends()


class FrameworkC(umake.frameworks.BaseFramework):

    def __init__(self, **kwargs):
        super().__init__(name="Framework C", description="Description for framework C (restricted version and arch)",
                         only_on_archs=["foo", "bar", "baz"],
                         only_ubuntu_version=["9.10", "10.04", "10.10.10"], **kwargs)

    def setup(self, install_path=None, auto_accept_license=False):
        super().setup()

    def remove(self):
        super().remove()

    def depends(self):
        super().depends()
