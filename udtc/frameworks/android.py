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
import udtc.frameworks

_supported_archs = ['i386', 'amd64']


class AndroidCategory(udtc.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name=_("Android"), description=_("Android Developement Environment"),
                         logo_path=None)


class EclipseAdt(udtc.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="ADT", description="Android Developer Tools (using eclipse)",
                         category=category, install_path_dir="android/adt-eclipse",
                         only_on_archs=_supported_archs)

    def setup(self, install_path=None):
        print("Installing…")
        super().setup()


class AndroidStudio(udtc.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Android Studio", description="Android Studio", is_category_default=True,
                         category=category, only_on_archs=_supported_archs)

    def setup(self, install_path=None):
        print("Installing android studio…")
        super().setup()
