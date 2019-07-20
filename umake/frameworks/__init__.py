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
from contextlib import suppress
from gettext import gettext as _
from importlib import import_module, reload
import inspect
import logging
import os
import pkgutil
import sys
import subprocess
from umake.network.requirements_handler import RequirementsHandler
from umake.settings import DEFAULT_INSTALL_TOOLS_PATH, UMAKE_FRAMEWORKS_ENVIRON_VARIABLE, DEFAULT_BINARY_LINK_PATH
from umake.tools import ConfigHandler, NoneDict, classproperty, get_current_arch, get_current_ubuntu_version,\
    is_completion_mode, switch_to_current_user, MainLoop, get_user_frameworks_path
from umake.ui import UI


logger = logging.getLogger(__name__)


class BaseCategory():
    """Base Category class to be inherited"""

    NOT_INSTALLED, PARTIALLY_INSTALLED, FULLY_INSTALLED = range(3)
    categories = NoneDict()

    def __init__(self, name, description="", logo_path=None, is_main_category=False, packages_requirements=None):
        self.name = name
        self.description = description
        self.logo_path = logo_path
        self.is_main_category = is_main_category
        self.default = None
        self.frameworks = NoneDict()
        self.packages_requirements = [] if packages_requirements is None else packages_requirements
        if self.prog_name in self.categories:
            logger.warning("There is already a registered category with {} as a name. Don't register the second one."
                           .format(name))
        else:
            self.categories[self.prog_name] = self

    @classproperty
    def main_category(self):
        for category in self.categories.values():
            if category.is_main_category:
                return category
        return None

    @property
    def prog_name(self):
        """Get programmatic, path and CLI compatible names"""
        return self.name.lower().replace('/', '-').replace(' ', '-')

    @property
    def default_framework(self):
        """Get default framework"""
        for framework in self.frameworks.values():
            if framework.is_category_default:
                return framework
        return None

    def register_framework(self, framework):
        """Register a new framework"""
        if framework.prog_name in self.frameworks:
            logger.error("There is already a registered framework with {} as a name. Don't register the second one."
                         .format(framework.name))
        else:
            self.frameworks[framework.prog_name] = framework

    @property
    def is_installed(self):
        """Return if the category is installed"""
        installed_frameworks = [framework for framework in self.frameworks.values() if framework.is_installed]
        if len(installed_frameworks) == 0:
            return self.NOT_INSTALLED
        if len(installed_frameworks) == len(self.frameworks):
            return self.FULLY_INSTALLED
        return self.PARTIALLY_INSTALLED

    def install_category_parser(self, parser):
        """Install category parser and get frameworks"""
        if not self.has_frameworks():
            logging.debug("Skipping {} having no framework".format(self.name))
            return
        # framework parser is directly category parser
        if self.is_main_category:
            framework_parser = parser
        else:
            self.category_parser = parser.add_parser(self.prog_name, help=self.description)
            framework_parser = self.category_parser.add_subparsers(dest="framework")
        for framework in self.frameworks.values():
            framework.install_framework_parser(framework_parser)
        return framework_parser

    def has_frameworks(self):
        """Return if a category has at least one framework"""
        return len(self.frameworks) > 0

    def has_one_framework(self):
        """Return if a category has one framework"""
        return len(self.frameworks) == 1

    def run_for(self, args):
        """Running commands from args namespace"""
        # try to call default framework if any
        if not args.framework:
            if not self.default_framework:
                message = _("A default framework for category {} was requested where there is none".format(self.name))
                logger.error(message)
                self.category_parser.print_usage()
                UI.return_main_screen(status_code=2)
            self.default_framework.run_for(args)
            return
        self.frameworks[args.framework].run_for(args)


class BaseFramework(metaclass=abc.ABCMeta):

    def __init__(self, name, description, category, force_loading=False, logo_path=None, is_category_default=False,
                 install_path_dir=None, only_on_archs=None, only_ubuntu_version=None, packages_requirements=None,
                 only_for_removal=False, expect_license=False, need_root_access=False, json=False):
        self.name = name
        self.description = description
        self.logo_path = None
        self.category = category
        self.is_category_default = is_category_default
        self.only_on_archs = [] if only_on_archs is None else only_on_archs
        self.only_ubuntu_version = [] if only_ubuntu_version is None else only_ubuntu_version
        self.packages_requirements = [] if packages_requirements is None else packages_requirements
        self.packages_requirements.extend(self.category.packages_requirements)
        self.only_for_removal = only_for_removal
        self.expect_license = expect_license

        # don't detect anything for completion mode (as we need to be quick), so avoid opening apt cache and detect
        # if it's installed.
        if is_completion_mode():
            # only show it in shell completion if it was already installed
            if self.only_for_removal:
                config = ConfigHandler().config
                try:
                    if not os.path.isdir(config["frameworks"][category.prog_name][self.prog_name]["path"]):
                        # don't show the framework in shell completion as for removal only and not installed
                        return
                except (TypeError, KeyError, FileNotFoundError):
                    # don't show the framework in shell completion as for removal only and not installed
                    return
            category.register_framework(self)
            return

        self.need_root_access = need_root_access
        if not need_root_access:
            with suppress(KeyError):
                self.need_root_access = not RequirementsHandler().is_bucket_installed(self.packages_requirements)

        if self.is_category_default:
            if self.category == BaseCategory.main_category:
                logger.error("Main category can't have default framework as {} requires".format(name))
                self.is_category_default = False
            elif self.category.default_framework is not None:
                logger.error("Can't set {} as default for {}: this category already has a default framework ({}). "
                             "Don't set any as default".format(category.name, name,
                                                               self.category.default_framework.name))
                self.is_category_default = False
                self.category.default_framework.is_category_default = False

        if not install_path_dir:
            install_path_dir = os.path.join("" if category.is_main_category else category.prog_name, self.prog_name)
        self.default_install_path = os.path.join(DEFAULT_INSTALL_TOOLS_PATH, install_path_dir)
        self.default_binary_link_path = DEFAULT_BINARY_LINK_PATH
        self.install_path = self.default_install_path
        # check if we have an install path previously set
        config = ConfigHandler().config
        try:
            self.install_path = config["frameworks"][category.prog_name][self.prog_name]["path"]
        except (TypeError, KeyError, FileNotFoundError):
            pass

        # This requires install_path and will register need_root or not
        if not force_loading and not self.is_installed and not self.is_installable:
            logger.info("Don't register {} as it's not installable on this configuration.".format(name))
            return

        category.register_framework(self)

    @property
    def is_installable(self):
        """Return if the framework can be installed on that arch"""
        if self.only_for_removal:
            return False
        try:
            if len(self.only_on_archs) > 0:
                # we have some restricted archs, check we support it
                current_arch = get_current_arch()
                if current_arch not in self.only_on_archs:
                    logger.debug("{} only supports {} archs and you are on {}.".format(self.name, self.only_on_archs,
                                                                                       current_arch))
                    return False
            if len(self.only_ubuntu_version) > 0:
                current_version = get_current_ubuntu_version()
                if current_version not in self.only_ubuntu_version:
                    logger.debug("{} only supports {} and you are on {}.".format(self.name, self.only_ubuntu_version,
                                                                                 current_version))
                    return False
            if not RequirementsHandler().is_bucket_available(self.packages_requirements):
                return False
        except:
            logger.error("An error occurred when detecting platform, don't register {}".format(self.name))
            return False
        return True

    @property
    def prog_name(self):
        """Get programmatic, path and CLI compatible names"""
        return self.name.lower().replace('/', '-').replace(' ', '-')

    @abc.abstractmethod
    def setup(self):
        """Method call to setup the Framework"""
        if not self.is_installable:
            logger.error(_("You can't install that framework on this machine"))
            UI.return_main_screen(status_code=2)

        if self.need_root_access and os.geteuid() != 0:
            logger.debug("Requesting root access")
            cmd = ["sudo", "-E", "env"]
            for var in ["PATH", "LD_LIBRARY_PATH", "PYTHONUSERBASE", "PYTHONHOME"]:
                if os.getenv(var):
                    cmd.append("{}={}".format(var, os.getenv(var)))
            if os.getenv("SNAP"):
                logger.debug("Found snap environment. Running correct python version")
                cmd.extend(["{}/usr/bin/python3".format(os.getenv("SNAP"))])
            cmd.extend(sys.argv)
            MainLoop().quit(subprocess.call(cmd))

        # be a normal, kind user as we don't want normal files to be written as root
        switch_to_current_user()

    @abc.abstractmethod
    def remove(self):
        """Method call to remove the current framework"""
        if not self.is_installed:
            logger.error(_("You can't remove {} as it isn't installed".format(self.name)))
            UI.return_main_screen(status_code=2)

    def mark_in_config(self):
        """Mark the installation as installed in the config file"""
        config = ConfigHandler().config
        config.setdefault("frameworks", {})\
              .setdefault(self.category.prog_name, {})\
              .setdefault(self.prog_name, {})["path"] = self.install_path
        ConfigHandler().config = config

    def remove_from_config(self):
        """Remove current framework from config"""
        config = ConfigHandler().config
        del(config["frameworks"][self.category.prog_name][self.prog_name])
        ConfigHandler().config = config

    @property
    def is_installed(self):
        """Method call to know if the framework is installed"""
        if not os.path.isdir(self.install_path):
            return False
        if not RequirementsHandler().is_bucket_installed(self.packages_requirements):
            return False
        return True

    def install_framework_parser(self, parser):
        """Install framework parser"""
        this_framework_parser = parser.add_parser(self.prog_name, help=self.description)
        this_framework_parser.add_argument('destdir', nargs='?', help=_("If the default framework name isn't provided, "
                                                                        "destdir should contain a /"))
        this_framework_parser.add_argument('-r', '--remove', action="store_true",
                                           help=_("Remove framework if installed"))
        if self.expect_license:
            this_framework_parser.add_argument('--accept-license', dest="accept_license", action="store_true",
                                               help=_("Accept license without prompting"))
        return this_framework_parser

    def run_for(self, args):
        """Running commands from args namespace"""
        logger.debug("Call run_for on {}".format(self.name))
        if args.remove:
            if args.destdir:
                message = "You can't specify a destination dir while removing a framework"
                logger.error(message)
                UI.return_main_screen(status_code=2)
            self.remove()
        else:
            install_path = None
            auto_accept_license = False
            if args.destdir:
                install_path = os.path.abspath(os.path.expanduser(args.destdir))
            if self.expect_license and args.accept_license:
                auto_accept_license = True
            self.setup(install_path=install_path, auto_accept_license=auto_accept_license)


class MainCategory(BaseCategory):

    def __init__(self):
        super().__init__(name="main", is_main_category=True)


def _is_categoryclass(o):
    return inspect.isclass(o) and issubclass(o, BaseCategory)


def _is_frameworkclass(o):
    """Filter concrete (non-abstract) subclasses of BaseFramework."""
    return inspect.isclass(o) and issubclass(o, BaseFramework) and not inspect.isabstract(o)


def load_module(module_abs_name, main_category, force_loading):
    logger.debug("New framework module: {}".format(module_abs_name))
    if module_abs_name not in sys.modules:
        import_module(module_abs_name)
    else:
        reload(sys.modules[module_abs_name])
    module = sys.modules[module_abs_name]
    current_category = main_category  # if no category found -> we assign to main category
    for category_name, CategoryClass in inspect.getmembers(module, _is_categoryclass):
        logger.debug("Found category: {}".format(category_name))
        current_category = CategoryClass()
    # if we didn't register the category: escape the framework registration
    if current_category not in BaseCategory.categories.values():
        return
    for framework_name, FrameworkClass in inspect.getmembers(module, _is_frameworkclass):
        if FrameworkClass(category=current_category, force_loading=force_loading) is not None:
            logger.debug("Attach framework {} to {}".format(framework_name, current_category.name))


def list_frameworks():
    """ Return frameworks and categories description as:
        [
            {
                'category_name':
                'category_description':
                'is_installed': BaseCategory.NOT_INSTALLED or
                                BaseCategory.PARTIALLY_INSTALLED or
                                BaseCategory.FULLY_INSTALLED
                'frameworks':
                    [
                        {
                            'framework_name':
                            'framework_description':
                            'install_path': None or Path string
                            'is_installed': True or False
                            'is_installable': True or False
                            'is_category_default': True or False
                            'only_for_removal': True or False
                        },
                    ]
            },
        ]
    """
    categories_dict = list()
    for category in BaseCategory.categories.values():
        frameworks_dict = list()
        for framework in category.frameworks.values():
            new_fram = {
                "framework_name": framework.prog_name,
                "framework_description": framework.description,
                "install_path": framework.install_path,
                "is_installed": framework.is_installed,
                "is_installable": framework.is_installable,
                "is_category_default": framework.is_category_default,
                "only_for_removal": framework.only_for_removal
            }

            frameworks_dict.append(new_fram)

        new_cat = {
            "category_name": category.prog_name,
            "category_description": category.description,
            "is_installed": category.is_installed,
            "frameworks": frameworks_dict
        }

        categories_dict.append(new_cat)

    return categories_dict


def load_frameworks(force_loading=False):
    """Load all modules and assign to correct category"""
    main_category = MainCategory()

    # Prepare local paths (1. environment path, 2. local path, 3. system paths).
    # If we have duplicated categories, only consider the first loaded one.
    local_paths = [get_user_frameworks_path()]
    sys.path.insert(0, get_user_frameworks_path())
    environment_path = os.environ.get(UMAKE_FRAMEWORKS_ENVIRON_VARIABLE)
    if environment_path:
        sys.path.insert(0, environment_path)
        local_paths.insert(0, environment_path)

    for loader, module_name, ispkg in pkgutil.iter_modules(path=local_paths):
        load_module(module_name, main_category, force_loading)
    for loader, module_name, ispkg in pkgutil.iter_modules(path=[os.path.dirname(__file__)]):
        module_name = "{}.{}".format(__package__, module_name)
        load_module(module_name, main_category, force_loading)
