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

import logging
import os
from udtc.settings import CONFIG_FILENAME
from xdg.BaseDirectory import load_first_config, xdg_config_home
import yaml
import yaml.scanner
import yaml.parser

logger = logging.getLogger(__name__)


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigHandler(metaclass=Singleton):

    def __init__(self):
        """Load the config"""
        self._config = None
        config_file = load_first_config(CONFIG_FILENAME)
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
        config_file = os.path.join(xdg_config_home, CONFIG_FILENAME)
        logging.debug("Saving new configuration: {} in {}".format(config, config_file))
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        self._config = config
