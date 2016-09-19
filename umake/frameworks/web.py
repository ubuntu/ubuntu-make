# -*- coding: utf-8 -*-
# Copyright (C) 2015 Canonical
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


"""Web module"""

from contextlib import suppress
from functools import partial
from gettext import gettext as _
import logging
import os
import platform
import re
import umake.frameworks.baseinstaller
from umake.frameworks.ide import VisualStudioCode
from umake.interactions import Choice, TextWithChoices
from umake.network.download_center import DownloadItem
from umake.ui import UI
from umake.tools import create_launcher, get_application_desktop_file, MainLoop

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class WebCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Web", description=_("Web Developer Environment"), logo_path=None)


class FirefoxDev(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Firefox Dev", description=_("Firefox Developer Edition"),
                         category=category, only_on_archs=_supported_archs,
                         download_page="https://www.mozilla.org/en-US/firefox/developer/all",
                         dir_to_decompress_in_tarball="firefox",
                         desktop_filename="firefox-developer.desktop",
                         required_files_path=["firefox"])
        self.arg_lang = None

    @MainLoop.in_mainloop_thread
    def language_select_callback(self, url):
        url = url.replace("&amp;", "&")
        logger.debug("Found download link for {}".format(url))
        self.download_requests.append(DownloadItem(url, None))
        self.start_download_and_install()

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Diverge from the baseinstaller implementation in order to allow language selection"""

        logger.debug("Parse download metadata")
        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        arch = platform.machine()
        arg_lang_url = None
        default_label = ''
        tag_machine = ''
        if arch == 'x86_64':
            tag_machine = '64'

        reg_expression = r'href="(\S+os=linux{}&amp;lang=\S+)"'.format(tag_machine)
        languages = []
        decoded_page = result[self.download_page].buffer.getvalue().decode()
        for index, p in enumerate(re.finditer(reg_expression, decoded_page)):
            with suppress(AttributeError):
                url = p.group(1)

            m = re.search(r'lang=(.*)', url)
            with suppress(AttributeError):
                lang = m.group(1)

            if self.arg_lang and self.arg_lang.lower() == lang.lower():
                arg_lang_url = url
                break
            else:
                is_default_choice = False
                if lang == "en-US":
                    default_label = "(default: en-US)"
                    is_default_choice = True
                choice = Choice(index, lang, partial(self.language_select_callback, url), is_default=is_default_choice)
                languages.append(choice)

        if self.arg_lang:
            logger.debug("Selecting {} lang".format(self.arg_lang))
            if not arg_lang_url:
                logger.error("Could not find a download url for language {}".format(self.arg_lang))
                UI.return_main_screen(status_code=1)
            self.language_select_callback(arg_lang_url)
        else:
            if not languages:
                logger.error("Download page changed its syntax or is not parsable")
                UI.return_main_screen(status_code=1)
            logger.debug("Check list of installable languages.")
            UI.delayed_display(TextWithChoices(_("Choose language: {}".format(default_label)), languages, True))

    def post_install(self):
        """Create the Firefox Developer launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Firefox Developer Edition"),
                        icon_path=os.path.join(self.install_path, "browser", "icons", "mozicon128.png"),
                        exec="{} %u".format(os.path.join(self.install_path, "firefox")),
                        comment=_("Firefox Aurora with Developer tools"),
                        categories="Development;IDE;"))

    def install_framework_parser(self, parser):
        this_framework_parser = super().install_framework_parser(parser)
        this_framework_parser.add_argument('--lang', dest="lang", action="store",
                                           help=_("Install in given language without prompting"))
        return this_framework_parser

    def run_for(self, args):
        if args.lang:
            self.arg_lang = args.lang
        super().run_for(args)


class VisualStudioCode(VisualStudioCode):

    def setup(self, *args, **kwargs):
        '''Print a deprecation warning before calling parent setup()'''
        logger.warning("Visual Studio Code is now in the ide category, please refer it from this category from now on. "
                       "This compatibility will be dropped after Ubuntu 16.04 LTS.")
        super().setup(*args, **kwargs)
