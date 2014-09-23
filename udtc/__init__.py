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

import argparse
import gettext
from gettext import gettext as _
import logging
import logging.config
import os
import sys
from udtc.frameworks import BaseCategory, load_frameworks
from udtc.tools import MainLoop
from .ui import cli
import yaml

gettext.textdomain("ubuntu-developer-tools-center")
logger = logging.getLogger(__name__)

_default_log_level = logging.WARNING
_datadir = None


def _setup_logging(env_key='LOG_CFG', level=_default_log_level):
    """Setup logging configuration

    Order of preference:
    - manually define level
    - env_key env variable if set (logging config file)
    - fallback to _default_log_level
    """
    path = os.getenv(env_key, '')
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
    if level == _default_log_level:
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = yaml.load(f.read())
            logging.config.dictConfig(config)
    logger.info("Logging level set to {}".format(logging.getLevelName(logging.root.getEffectiveLevel())))


def get_data_dir():
    """Return absolute path to data dir.

    Use the local data dir if found, otherwise, return the system dir.
    """
    if not _datadir:
        local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        if os.path.isdir(local_dir):
            logger.debug("Using local data dir in {}".format(local_dir))
            return local_dir
    if not _datadir:
        logging.error("No data directory found")
    return _datadir


def set_logging_from_args(args, parser):
    """Choose logging ignoring any unknown sys.argv options"""
    result_verbosity_arg = []
    for arg in args:
        if arg.startswith("-v"):
            for char in arg:
                if char not in ['-', 'v']:
                    break
            else:
                result_verbosity_arg.append(arg)
    args = parser.parse_args(result_verbosity_arg)

    # setup logging level if set by the command line
    if args.verbose == 1:
        _setup_logging(level=logging.INFO)
    elif args.verbose > 1:
        _setup_logging(level=logging.DEBUG)
    else:
        _setup_logging()


class _HelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print(_("* Command '{}':").format(choice))
                print(subparser.format_help())
        parser.exit()


def main():
    """Main entry point of the program"""

    parser = argparse.ArgumentParser(description=_("Deploy and setup developers environment easily on ubuntu"),
                                     epilog=_("Note that you can also configure different debug logs behaviors using "
                                              "LOG_CFG pointing to a log yaml profile."),
                                     add_help=False)
    parser.add_argument('--help', action=_HelpAction, help=_('Show this help'))  # add custom help
    parser.add_argument("-v", "--verbose", action="count", default=0, help=_("Increase output verbosity (2 levels)"))

    parser.add_argument('-r', '--remove', action="store_true", help=_("Remove specified framework if installed"))

    # set logging ignoring unknown options
    set_logging_from_args(sys.argv, parser)

    mainloop = MainLoop()

    # load frameworks and initialize parser
    load_frameworks()
    cli.main(parser)

    mainloop.run()
