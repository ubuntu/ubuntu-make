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

from gi.repository import GLib
from umake.tools import Singleton, MainLoop


class UI(object, metaclass=Singleton):

    currentUI = None

    def __init__(self, current_UI):
        UI.currentUI = current_UI

    @classmethod
    def return_main_screen(cls, status_code=0):
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
