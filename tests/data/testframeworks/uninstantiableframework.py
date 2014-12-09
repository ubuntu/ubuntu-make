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


class Uninstantiable(umake.frameworks.BaseFramework):

    def __new__(cls, *args, **kwargs):
        "This class is not meant to be instantiated, so __new__ returns None."
        if cls == Uninstantiable:
            return None
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setup(self, install_path=None):
        super().setup()

    def remove(self):
        super().remove()


class InheritedFromUninstantiable(Uninstantiable):

    def __init__(self, category):
        super().__init__(name="Inherited From Uninstantiable", description="Framework Inheriting Uninstantiable",
                         category=category)
