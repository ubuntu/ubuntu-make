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

"""Ensure we keep a sane formatting syntax"""

import os
import pep8
from .tools import get_root_dir
import umake
from unittest import TestCase


class CodeCheck(TestCase):

    def test_pep8(self):
        """Proceed a pep8 checking

        Note that we have a .pep8 config file for maximum line length tweak
        and excluding the virtualenv dir."""
        pep8style = pep8.StyleGuide(config_file=os.path.join(get_root_dir(), '.pep8'))

        # we want to use either local or system umake, but always local tests files
        umake_dir = os.path.dirname(umake.__file__)
        results = pep8style.check_files([umake_dir, os.path.join(get_root_dir(), "tests"),
                                         os.path.join(get_root_dir(), "bin")])
        self.assertEqual(results.get_statistics(), [])
