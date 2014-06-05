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

"""Common tools between tests"""

from copy import deepcopy
import logging
import os
from unittest.mock import Mock

logger = logging.getLogger(__name__)


def get_data_dir():
    """Return absolute data dir path"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))


def get_root_dir():
    """Return absolute project root dir path"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def assert_files_identicals(filename1, filename2):
    """Assert if the files content are identical"""
    if open(filename1).read() != open(filename2).read():
        logger.error("{}: {}\n{}: {}".format(filename1, open(filename1).read(),
                                             filename2, open(filename2).read()))
        raise AssertionError("{} and {} aren't identical".format(filename1, filename2))


class CopyingMock(Mock):
    """Mock for recording calls with mutable arguments"""
    def __call__(self, *args, **kwargs):
        args = deepcopy(args)
        kwargs = deepcopy(kwargs)
        return super(CopyingMock, self).__call__(*args, **kwargs)
