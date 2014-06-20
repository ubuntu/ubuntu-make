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

from gi.repository import GLib
import logging
import os
import subprocess
from udtc import settings
from xdg.BaseDirectory import load_first_config, xdg_config_home
import yaml
import yaml.scanner
import yaml.parser

logger = logging.getLogger(__name__)

# cache current arch. Shouldn't change in the life of the process ;)
_current_arch = None
_version = None


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigHandler(metaclass=Singleton):

    def __init__(self):
        """Load the config"""
        self._config = {}
        config_file = load_first_config(settings.CONFIG_FILENAME)
        logger.debug("Opening {}".format(config_file))
        try:
            with open(config_file) as f:
                self._config = yaml.load(f)
        except (TypeError, FileNotFoundError):
            logger.info("No configuration file found")
        except (yaml.scanner.ScannerError, yaml.parser.ParserError) as e:
            logger.error("Invalid configuration file found: {}".format(e))

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, config):
        config_file = os.path.join(xdg_config_home, settings.CONFIG_FILENAME)
        logging.debug("Saving new configuration: {} in {}".format(config, config_file))
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        self._config = config


class NoneDict(dict):
    """We don't use a defaultdict(lambda: None) as it's growing everytime something is requested"""
    def __getitem__(self, key):
        return dict.get(self, key)


class classproperty(object):
    """Class property, similar to instance properties"""
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


def get_current_arch():
    """Get current configuration dpkg architecture"""
    global _current_arch
    if _current_arch is None:
        _current_arch = subprocess.check_output(["dpkg", "--print-architecture"], universal_newlines=True).rstrip("\n")
    return _current_arch


def get_current_ubuntu_version():
    """Return current ubuntu version or raise an error if couldn't find any"""
    global _version
    if _version is None:
        try:
            with open(settings.LSB_RELEASE_FILE) as lsb_release_file:
                for line in lsb_release_file:
                    line = line.strip()
                    if line.startswith('DISTRIB_RELEASE='):
                        tag, release = line.split('=', 1)
                        _version = release
                        break
                else:
                    message = "Couldn't find DISTRIB_RELEASE in {}".format(settings.LSB_RELEASE_FILE)
                    logger.error(message)
                    raise BaseException(message)
        except (FileNotFoundError, IOError) as e:
            message = "Can't open lsb-release file: {}".format(e)
            logger.error(message)
            raise BaseException(message)
    return _version


def in_mainloop_thread(function):
    """Decorator to run a function in a mainloop thread"""
    def inner(*args, **kwargs):
        return GLib.idle_add(function, *args, **kwargs)
    return inner
