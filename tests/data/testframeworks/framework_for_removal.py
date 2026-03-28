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


"""Framework only marked for removal"""

import umake.frameworks


class RCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Category R", description="Only containing one framework for removal")


class FrameworkRuninstalled(umake.frameworks.BaseFramework):

    def __init__(self, **kwargs):
        super().__init__(name="Framework R uninstalled", description="For removal", only_for_removal=True,
                         **kwargs)

    def setup(self, install_path=None, auto_accept_license=False):
        super().setup()

    def remove(self):
        super().remove()

    def depends(self):
        super().depends()


class FrameworkRinstalled(umake.frameworks.BaseFramework):

    def __init__(self, **kwargs):
        super().__init__(name="Framework R installed", description="For removal", only_for_removal=True,
                         **kwargs)

    def setup(self, install_path=None, auto_accept_license=False):
        super().setup()

    def remove(self):
        super().remove()

    def depends(self):
        super().depends()

    @property
    def is_installed(self):
        return True


class FrameworkRinstallednotinstallable(umake.frameworks.BaseFramework):

    def __init__(self, **kwargs):
        super().__init__(name="Framework R installed not installable",
                         description="For removal without only for removal", **kwargs)

    def setup(self, install_path=None, auto_accept_license=False):
        print("here")
        super().setup()

    def remove(self):
        super().remove()

    def depends(self):
        super().depends()

    @property
    def is_installed(self):
        return True

    @property
    def is_installable(self):
        return False
