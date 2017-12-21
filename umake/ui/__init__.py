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

"""Abstracted UI interface that will be overriden by different UI types"""

import logging
from gi.repository import GLib
from umake.tools import Singleton, MainLoop
from umake.settings import get_version, get_latest_version

logger = logging.getLogger(__name__)


class UI(object, metaclass=Singleton):

    currentUI = None

    def __init__(self, current_UI):
        UI.currentUI = current_UI

    @classmethod
    def return_main_screen(cls, status_code=0):
        try:
            truncated_version = get_version().split("+")[0]
            if status_code == 1 and not (get_latest_version() == truncated_version):
                print('''
Your currently installed version ({}) differs from the latest release ({})
Many issues are usually fixed in more up to date versions.
To get the latest version you can read the instructions at https://github.com/ubuntu/ubuntu-make
'''.format(get_version(), get_latest_version()))
        except Exception as e:
            logger.error(e)
        cls.currentUI._return_main_screen(status_code=status_code)

    @classmethod
    @MainLoop.in_mainloop_thread
    def display(cls, contentType):
        """display in main thread this UI contentType. Can be delayed by 50 ms, like for pulse or message"""
        # TODO: add check for current framework == framework sending contentType
        cls.currentUI._display(contentType)

    @classmethod
    @MainLoop.in_mainloop_thread
    def delayed_display(cls, contentType):
        GLib.timeout_add(50, cls._one_time_wrapper, cls.currentUI._display, contentType)

    @staticmethod
    def _one_time_wrapper(fun, contentType):
        """To be called with GLib.timeout_add(), return False to only have one call"""
        fun(contentType)
        return False
