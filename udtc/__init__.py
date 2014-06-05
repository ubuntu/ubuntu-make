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
import logging.config
import os
import yaml

_default_log_level = logging.WARNING

logger = logging.getLogger(__name__)


def setup_logging(default_file='logging.yaml', env_key='LOG_CFG', level=_default_log_level):
    """Setup logging configuration

    Order of preference:
    - manually define level
    - env_key env variable if set (logging config file)
    - default_file path if present (logging config file)
    - fallback to _default_log_level
    """
    path = default_file
    value = os.getenv(env_key, None)
    logging.basicConfig(level=level, format="[%(name)s] %(levelname)s: %(message)s")
    if level == _default_log_level:
        if value:
            path = value
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = yaml.load(f.read())
            logging.config.dictConfig(config)
    logger.info("Logging level set to {}".format(logging.getLevelName(level)))
