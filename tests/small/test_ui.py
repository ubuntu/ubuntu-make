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

"""Tests for the generic ui module"""

from concurrent import futures
from gi.repository import GLib
from time import time
from unittest.mock import Mock, patch
from ..tools import LoggedTestCase
import threading
from umake.tools import MainLoop, Singleton
from umake.ui import UI


class TestUI(LoggedTestCase):
    """This will test the UI generic module"""

    def setUp(self):
        super().setUp()
        self.mockUIPlug = Mock()
        self.mockUIPlug._display.side_effect = self.display_UIPlug
        self.contentType = Mock()
        self.ui = UI(self.mockUIPlug)
        self.mainloop_object = MainLoop()
        self.mainloop_thread = None
        self.function_thread = None
        self.display_thread = None
        self.time_display_call = 0

    def tearDown(self):
        Singleton._instances = {}
        super().tearDown()

    # function that will complete once the mainloop is started
    def wait_for_mainloop_function(self):
        timeout_time = time() + 5
        while not self.mainloop_object.mainloop.is_running():
            if time() > timeout_time:
                raise(BaseException("Mainloop not started in 5 seconds"))

    def wait_for_mainloop_shutdown(self):
        timeout_time = time() + 5
        while self.mainloop_object.mainloop.is_running():
            if time() > timeout_time:
                raise(BaseException("Mainloop not stopped in 5 seconds"))

    def get_mainloop_thread(self):
        self.mainloop_thread = threading.current_thread().ident

    def start_glib_mainloop(self):
        # quit after 5 seconds if nothing made the mainloop to end
        GLib.timeout_add_seconds(5, self.mainloop_object.mainloop.quit)
        GLib.idle_add(self.get_mainloop_thread)
        self.mainloop_object.run()

    def display_UIPlug(self, contentType):
        """handler to mock _display and save the current thread"""
        self.time_display_call = time()
        self.assertEquals(self.contentType, contentType)
        self.display_thread = threading.current_thread().ident
        self.mainloop_object.quit(raise_exception=False)

    def test_singleton(self):
        """Ensure we are delivering a singleton for UI"""
        other = UI(self.mockUIPlug)
        self.assertEquals(self.ui, other)

    def test_return_to_mainscreen(self):
        """We call the return to main screen on the UIPlug"""
        UI.return_main_screen()
        self.assertTrue(self.mockUIPlug._return_main_screen.called)

    @patch("umake.tools.sys")
    def test_call_display(self, mocksys):
        """We call the display method from the UIPlug"""
        UI.display(self.contentType)
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        self.assertTrue(self.mockUIPlug._display.called)
        self.assertIsNotNone(self.mainloop_thread)
        self.assertIsNotNone(self.display_thread)
        self.assertEquals(self.mainloop_thread, self.display_thread)

    @patch("umake.tools.sys")
    def test_call_display_other_thread(self, mocksys):
        """We call the display method on UIPlug in the main thread from another thread"""
        def run_display(future):
            self.function_thread = threading.current_thread().ident
            UI.display(self.contentType)

        executor = futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.wait_for_mainloop_function)
        future.add_done_callback(run_display)
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        self.assertTrue(self.mockUIPlug._display.called)
        self.assertIsNotNone(self.mainloop_thread)
        self.assertIsNotNone(self.function_thread)
        self.assertIsNotNone(self.display_thread)
        self.assertNotEquals(self.mainloop_thread, self.function_thread)
        self.assertEquals(self.mainloop_thread, self.display_thread)

    @patch("umake.tools.sys")
    def test_call_delayed_display(self, mocksys):
        """We call the display method from the UIPlug in delayed_display with 50ms waiting"""
        UI.delayed_display(self.contentType)
        now = time()
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        self.assertTrue(self.mockUIPlug._display.called)
        self.assertIsNotNone(self.mainloop_thread)
        self.assertIsNotNone(self.display_thread)
        self.assertEquals(self.mainloop_thread, self.display_thread)
        self.assertTrue(self.time_display_call - now > 0.05)

    @patch("umake.tools.sys")
    def test_call_delayed_display_from_other_thread(self, mocksys):
        """We call the display method from the UIPlug in delayed_display with 50ms waiting, even on other thread"""
        now = 0

        def run_display(future):
            nonlocal now
            self.function_thread = threading.current_thread().ident
            now = time()
            UI.delayed_display(self.contentType)

        executor = futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.wait_for_mainloop_function)
        future.add_done_callback(run_display)
        self.start_glib_mainloop()
        self.wait_for_mainloop_shutdown()

        self.assertTrue(self.mockUIPlug._display.called)
        self.assertIsNotNone(self.mainloop_thread)
        self.assertIsNotNone(self.function_thread)
        self.assertIsNotNone(self.display_thread)
        self.assertNotEquals(self.mainloop_thread, self.function_thread)
        self.assertEquals(self.mainloop_thread, self.display_thread)
        self.assertTrue(self.time_display_call - now > 0.05)
