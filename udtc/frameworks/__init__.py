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


"""Base Handling functions and base class of backends"""

import abc
from importlib import import_module
import inspect
import logging
import os
import pkgutil
import sys
from udtc.tools import ConfigHandler, NoneDict
from udtc.settings import DEFAULT_INSTALL_TOOLS_PATH


logger = logging.getLogger(__name__)


class BaseCategory():
    """Base Category class to be inherited"""

    NOT_INSTALLED, PARTIALLY_INSTALLED, FULLY_INSTALLED = range(3)
    categories = NoneDict()

    def __init__(self, name, description="", logo_path=None, is_main_category=False):
        self.name = name
        self.description = description
        self.logo_path = logo_path
        self.main_category = is_main_category
        self.default = None
        self.frameworks = NoneDict()
        if self.name in self.categories:
            logger.error("There is already a registered category with {} as a name. Don't register the second one"
                         .format(name))
        else:
            self.categories[self.name] = self

    @property
    def prog_name(self):
        """Get programmatic, path and CLI compatible names"""
        return self.name.lower().replace('/', '-').replace(' ', '-')

    @classmethod
    def get_main_category(cls):
        """Return main category if any"""
        for category in cls.categories.values():
            if category.main_category:
                logger.debug("Found main category as requested")
                return category
        logger.warning("There is no main category while we requested one")
        return None

    def register_framework(self, framework, is_default=False):
        """Register a new framework"""
        self.frameworks[framework.name] = framework
        if is_default:
            self.default = framework

    def is_installed(self):
        """Return if the category is installed"""
        installed_frameworks = [framework for framework in self.frameworks.values() if framework.is_installed()]
        if len(installed_frameworks) == 0:
            return self.NOT_INSTALLED
        if len(installed_frameworks) == len(self.frameworks):
            return self.FULLY_INSTALLED
        return self.PARTIALLY_INSTALLED

    def has_frameworks(self):
        """Return if a category has at least one framework"""
        return len(self.frameworks) > 0

    def has_one_framework(self):
        """Return if a category has one framework"""
        return len(self.frameworks) == 1


class BaseFramework(metaclass=abc.ABCMeta):

    category_default = False

    def __init__(self, name, description, category, logo_path=None, install_path_dir=None):
        self.name = name
        self.description = description
        self.logo_path = None
        self.category = category

        if not install_path_dir:
            install_path_dir = os.path.join("" if category.main_category else category.prog_name, self.prog_name)
        self.default_install_path = os.path.join(DEFAULT_INSTALL_TOOLS_PATH, install_path_dir)
        self.install_path = self.default_install_path
        # check if we have an install path previously set
        config = ConfigHandler().config
        try:
            self.install_path = config["frameworks"][category.name][name]["path"]
        except (TypeError, KeyError, FileNotFoundError):
            pass
        category.register_framework(self, is_default=self.category_default)

    @property
    def prog_name(self):
        """Get programmatic, path and CLI compatible names"""
        return self.name.lower().replace('/', '-').replace(' ', '-')

    @abc.abstractmethod
    def setup(self, install_path=None):
        """Method call to setup the Framework"""
        if install_path:
            self.install_path = install_path
        config = ConfigHandler().config
        config.setdefault("frameworks", {})\
              .setdefault(self.category.name, {})\
              .setdefault(self.name, {})["path"] = self.install_path
        ConfigHandler().config = config

    def is_installed(self):
        """Method call to know if the framework is installed"""
        return os.path.isdir(self.install_path)


class MainCategory(BaseCategory):

    def __init__(self):
        super().__init__(name="main", is_main_category=True)


def _is_categoryclass(o):
    return inspect.isclass(o) and issubclass(o, BaseCategory)


def _is_frameworkclass(o):
    return inspect.isclass(o) and issubclass(o, BaseFramework)


def load_frameworks():
    """Load all modules and assign to correct category"""
    main_category = MainCategory()
    print(os.path.dirname(__file__))
    for loader, module_name, ispkg in pkgutil.iter_modules(path=[os.path.dirname(__file__)]):
        module_name = "{}.{}".format(__package__, module_name)
        logger.debug("New framework module: {}".format(module_name))
        if module_name not in sys.modules:
            import_module(module_name)
        module = sys.modules[module_name]
        current_category = main_category  # if no category found -> we assign to main category
        for category_name, CategoryClass in inspect.getmembers(module, _is_categoryclass):
            logger.debug("Found category: {}".format(category_name))
            current_category = CategoryClass()
        for framework_name, FrameworkClass in inspect.getmembers(module, _is_frameworkclass):
            logger.debug("Attach framework {} to {}".format(framework_name, current_category.name))
            FrameworkClass(current_category)
