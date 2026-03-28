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

#PYTHON_ARGCOMPLETE_OK

import argparse
import gettext
from gettext import gettext as _
import locale
import logging
import logging.config
import os
import sys
from umake.frameworks import load_frameworks
from umake.tools import MainLoop
from .ui import cli
import yaml

logger = logging.getLogger(__name__)

# if set locale isn't installed, don't load up translations (we don't know what's the locale
# user encoding is and python3 will fallback to ANSI_X3.4-1968, which isn't UTF-8 and creates
# thus UnicodeEncodeError)
try:
    locale.setlocale(locale.LC_ALL, '')
    gettext.textdomain("ubuntu-make")
except locale.Error:
    logger.debug("Couldn't load default locale {}, fallback to English".format(locale.LC_ALL))

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
    if level == logging.DEBUG:
        logger.debug("Set http/requests logger to debug")
        import http.client as http_client
        http_client.HTTPConnection.debuglevel = 1

        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
    if level == _default_log_level:
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = yaml.load(f.read())
            logging.config.dictConfig(config)
    logging.info("Logging level set to {}".format(logging.getLevelName(logging.root.getEffectiveLevel())))


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


def should_load_all_frameworks(args):
    """Set partial or complete framework loading condition based on arg"""
    for arg in args[1:]:
        if arg in ["-l", "--list", "--list-installed", "--list-available", "--list-json"]:
            return True

    return False


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

    if "udtc" in sys.argv[0]:
        print(_("WARNING: 'udtc' command is the previous name of Ubuntu Make. Please use the 'umake' command from now "
                "on providing the exact same features. The 'udtc' command will be removed soon."))

    parser = argparse.ArgumentParser(description=_("Deploy and setup developers environment easily on ubuntu"),
                                     epilog=_("Note that you can also configure different debug logging behavior using "
                                              "LOG_CFG that points to a log yaml profile."),
                                     add_help=False)
    parser.add_argument('--help', action=_HelpAction, help=_('Show this help'))  # add custom help
    parser.add_argument("-v", "--verbose", action="count", default=0, help=_("Increase output verbosity (2 levels)"))
    parser.add_argument('-u', '--update', action='store_true', help=_('Update installed frameworks'))
    parser.add_argument('-y', '--assume-yes', action='store_true', help=_('Assume yes at interactive prompts'))
    parser.add_argument('-r', '--remove', action="store_true", help=_("Remove specified framework if installed"))
    parser.add_argument('-d', '--depends', action="store_true", help=_("List specified framework dependencies"))

    list_group = parser.add_argument_group("List frameworks").add_mutually_exclusive_group()
    list_group.add_argument('-l', '--list', action="store_true", help=_("List all frameworks"))
    list_group.add_argument('--list-installed', action="store_true", help=_("List installed frameworks"))
    list_group.add_argument('--list-available', action="store_true", help=_("List installable frameworks"))
    list_group.add_argument('--list-json', action="store_true", help=_("List installable frameworks (json)"))

    parser.add_argument('--version', action="store_true", help=_("Print version and exit"))

    # set logging ignoring unknown options
    set_logging_from_args(sys.argv, parser)

    mainloop = MainLoop()

    # load frameworks
    load_frameworks(force_loading=should_load_all_frameworks(sys.argv))

    # initialize parser
    cli.main(parser)

    mainloop.run()
