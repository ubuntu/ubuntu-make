#!/usr/bin/env python3
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

from babel.messages import frontend as babel
from glob import glob
from setuptools import setup, find_packages


def get_requirements(tag_to_detect=""):
    """Gather a list line per line of requirements from tag_to_detect to next tag.

    if tag_to_detect is empty, it will gather every requirements"""
    requirements = []
    tag_detected = False
    with open("requirements.txt") as f:
        for line in f.read().splitlines():
            if line.startswith("#") or line == "":
                tag_detected = False
                if line.startswith(tag_to_detect):
                    tag_detected = True
                continue
            if tag_detected:
                requirements.append(line)
    print(requirements)
    return requirements

setup(
    name="Ubuntu Developer Tools Center",
    version="0.0.1",
    packages=find_packages(exclude=["tests*"]),
    package_data={},
    entry_points={
        'console_scripts': [
            'udtc = udtc:main'
        ],
    },

    data_files=[("share/ubuntu-developer-tools-center/log-confs", glob('log-confs/*.yaml'))],

    # In addition to run all nose tests, that will as well show python warnings
    test_suite="nose.collector",

    # i18n based on http://babel.pocoo.org/docs/setup/
    cmdclass={'compile_catalog': babel.compile_catalog,
              'extract_messages': babel.extract_messages,
              'init_catalog': babel.init_catalog,
              'update_catalog': babel.update_catalog}
)
