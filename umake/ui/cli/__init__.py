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
from gettext import gettext as _
import logging
import os
from progressbar import ProgressBar, BouncingBar
import readline
import sys
from umake.interactions import InputText, TextWithChoices, LicenseAgreement, DisplayMessage, UnknownProgress
from umake.ui import UI
from umake.frameworks import BaseCategory, list_frameworks
from umake.tools import InputError, MainLoop
from umake.settings import get_version

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

    def _return_main_screen(self, status_code=0):
        # quit the shell
        MainLoop().quit(status_code=status_code)

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
                    with suppress(StopIteration, AttributeError):
                        # pulse and add a timeout callback
                        contentType.bar(contentType._iterator()).next()
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


@MainLoop.in_mainloop_thread
def run_command_for_args(args):
    """Run correct command for args"""
    # args.category can be a category or a framework in main
    target = None
    try:
        target = BaseCategory.categories[args.category]
    except AttributeError:
        target = BaseCategory.main_category.frameworks[args.category]
    target.run_for(args)


def mangle_args_for_default_framework(args):
    """return the potentially changed args_to_parse for the parser for handling default frameworks

    "./<command> [global_or_common_options] category [options from default framework]"
    as subparsers can't define default options and are not optional: http://bugs.python.org/issue9253
    """

    result_args = []
    skip_all = False
    pending_args = []
    category_name = None
    framework_completed = False
    args_to_append = []

    for arg in args:
        # --remove is both installed as global and per-framework optional arguments. argparse will only analyze the
        # per framework one and will override the global one. So if --remove is before the category name, it will be
        # ignored. Mangle the arg and append it last then.
        if not category_name and arg in ("--remove", "-r"):
            args_to_append.append(arg)
            continue
        if not arg.startswith('-') and not skip_all:
            if not category_name:
                if arg in BaseCategory.categories.keys():
                    category_name = arg
                    # file global and common options
                    result_args.extend(pending_args)
                    pending_args = []
                    result_args.append(arg)
                    continue
                else:
                    skip_all = True  # will just append everything at the end
            elif not framework_completed:
                # if we found a real framework or not, consider that one. pending_args will be then filed
                framework_completed = True
                if arg in BaseCategory.categories[category_name].frameworks.keys():
                    result_args.append(arg)
                    continue
                # take default framework if any after some sanitization check
                elif BaseCategory.categories[category_name].default_framework is not None:
                    # before considering automatically inserting default framework, check that this argument has
                    # some path separator into it. This is to avoid typos in framework selection and selecting default
                    # framework with installation path where we didn't want to.
                    if os.path.sep in arg:
                        result_args.append(BaseCategory.categories[category_name].default_framework.prog_name)
                    # current arg will be appending in pending_args
                else:
                    skip_all = True  # will just append everything at the end
        pending_args.append(arg)

    # this happened only if there is no argument after the category name
    if category_name and not framework_completed:
        if BaseCategory.categories[category_name].default_framework is not None:
            result_args.append(BaseCategory.categories[category_name].default_framework.prog_name)

    # let the rest in
    result_args.extend(pending_args)
    result_args.extend(args_to_append)
    return result_args


def get_frameworks_list_output(args):
    """
    Get a frameworks list based on the arguments. It returns a string ready to be printed.
    Multiple forms of the frameworks list can ge given:
        - List with all frameworks
        - List with just only installed frameworks
        - List with just installable frameworks
    """
    categories = list_frameworks()
    print_result = str()

    if args.list or args.list_available:
        # Sort the categories to prevent a random list at each new program execution
        for category in sorted(categories, key=lambda cat: cat["category_name"]):
            if category["category_name"] == "main" and len(category["frameworks"]) == 0:
                continue

            print_result += "{}: {}".format(category["category_name"], category["category_description"])

            cat_is_installed = str()
            if category["is_installed"] == BaseCategory.NOT_INSTALLED:
                cat_is_installed = _("not installed")
            elif category["is_installed"] == BaseCategory.PARTIALLY_INSTALLED:
                cat_is_installed = _("partially installed")
            elif category["is_installed"] == BaseCategory.FULLY_INSTALLED:
                cat_is_installed = _("fully installed")

            if cat_is_installed:
                print_result = "{} [{}]".format(print_result, cat_is_installed)

            print_result += "\n"

            # Sort the frameworks to prevent a random list at each new program execution
            for framework in sorted(category["frameworks"], key=lambda fram: fram["framework_name"]):
                if args.list_available:
                    if not framework["is_installable"]:
                        continue

                print_result += "\t{}: {}".format(framework["framework_name"], framework["framework_description"])

                if not framework["is_installable"]:
                    print_result = _("{} [not installable on this machine]".format(print_result))
                elif framework["is_installed"]:
                    print_result = _("{} [installed]".format(print_result))

                print_result += '\n'
    elif args.list_installed:
        # Sort the categories to prevent a random list at each new program execution
        for category in sorted(categories, key=lambda cat: cat["category_name"]):
            # Sort the frameworks to prevent a random list at each new program execution
            for framework in sorted(category["frameworks"], key=lambda fram: fram["framework_name"]):
                if framework["is_installed"]:
                    print_result += "{}: {}\n".format(framework["framework_name"],
                                                      framework["framework_description"])
                    print_result += "\t{}: {}\n".format(_("path"), framework["install_path"])

        if not print_result:
            print_result = _("No frameworks are currently installed")

    return print_result


def main(parser):
    """Main entry point of the cli command"""
    categories_parser = parser.add_subparsers(help='Developer environment', dest="category")
    for category in BaseCategory.categories.values():
        category.install_category_parser(categories_parser)

    argcomplete.autocomplete(parser)
    # autocomplete will stop there. Can start more expensive operations now.

    arg_to_parse = sys.argv[1:]
    if "--help" not in arg_to_parse:
        # manipulate sys.argv for default frameworks:
        arg_to_parse = mangle_args_for_default_framework(arg_to_parse)
    args = parser.parse_args(arg_to_parse)

    if args.list or args.list_installed or args.list_available:
        print(get_frameworks_list_output(args))
        sys.exit(0)

    if args.version and not len(arg_to_parse) > 1:
        print(get_version())
        sys.exit(0)

    if not args.category:
        parser.print_help()
        sys.exit(0)

    CliUI()
    run_command_for_args(args)
