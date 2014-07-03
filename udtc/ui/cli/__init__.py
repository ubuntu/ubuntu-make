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

"""Module for loading the command line interface"""

import argcomplete
from contextlib import suppress
from gi.repository import GLib
import logging
from progressbar import ProgressBar, BouncingBar
import readline
import sys
from udtc.interactions import InputText, TextWithChoices, LicenseAgreement, DisplayMessage, UnknownProgress
from udtc.ui import UI
from udtc.frameworks import BaseCategory
from udtc.tools import InputError, MainLoop

logger = logging.getLogger(__name__)


def rlinput(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt + " ")
    finally:
        readline.set_startup_hook()


class CliUI(UI):

    def __init__(self):
        # This this UI as current
        super().__init__(self)

    def _return_main_screen(self):
        # quit the shell
        MainLoop().quit()

    def _add_progress_timeout(self, progress_bar):
        GLib.timeout_add(50, self._display, progress_bar)

    def _display(self, contentType):
        # print depending on the content type
        while True:
            try:
                if isinstance(contentType, InputText):
                    contentType.run_callback(result=rlinput(contentType.content, contentType.default_input))
                elif isinstance(contentType, LicenseAgreement):
                    print(contentType.content)
                    contentType.choose(answer=input(contentType.input))
                elif isinstance(contentType, TextWithChoices):
                    contentType.choose(answer=input(contentType.prompt))
                elif isinstance(contentType, DisplayMessage):
                    print(contentType.text)
                elif isinstance(contentType, UnknownProgress):
                    if not contentType.bar:
                        contentType.bar = ProgressBar(widgets=[BouncingBar()])
                    with suppress(StopIteration):
                        # pulse and add a timeout callback
                        contentType.bar(contentType._iterator()).next()
                        #self._add_progress_timeout(contentType)
                        UI.delayed_display(contentType)
                    # don't recall the callback
                    return False
                else:
                    logger.error("Unexcepted content type to display to CLI UI: {}".format(contentType))
                    MainLoop().quit(status_code=1)
                break
            except InputError as e:
                logger.error(str(e))
                continue

def run_command_for_args(args):
    """Run correct command for args"""
    # args.category can be a category or a framework in main
    target = None
    try:
        target = BaseCategory.categories[args.category]
    except AttributeError:
        target = BaseCategory.main_category.frameworks[args.category]
    target.run_for(args)


def main(parser):
    """Main entry point of the cli command"""
    categories_parser = parser.add_subparsers(help='Developer environment', dest="category")
    for category in BaseCategory.categories.values():
        category.install_category_parser(categories_parser)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if not args.category:
        parser.print_help()
        sys.exit(0)

    CliUI()
    GLib.idle_add(run_command_for_args, args)
