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
import subprocess
from contextlib import suppress
from functools import partial
from gettext import gettext as _
import logging
import os
import platform
import re
import umake.frameworks.baseinstaller
from umake.interactions import Choice, TextWithChoices, DisplayMessage
from umake.network.download_center import DownloadItem
from umake.ui import UI
from umake.tools import create_launcher, get_application_desktop_file, MainLoop,\
    get_current_arch, add_env_to_user

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class WebCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Web", description=_("Web Developer Environment"), logo_path=None)


class FirefoxDev(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Firefox Dev", description=_("Firefox Developer Edition"),
                         only_on_archs=_supported_archs,
                         download_page=f"https://www.mozilla.org/en-US/firefox/all/desktop-developer/linux{self.get_tag_machine()}/",
                         dir_to_decompress_in_tarball="firefox",
                         desktop_filename="firefox-developer.desktop",
                         required_files_path=["firefox"], **kwargs)
        self.arg_lang = None

    def get_tag_machine(self):
        return "64" if platform.machine() == "x86_64" else ""

    @MainLoop.in_mainloop_thread
    def language_select_callback(self, url):
        url = url.replace("&amp;", "&")
        logger.debug("Found download link for {}".format(url))
        if self.dry_run:
            UI.display(DisplayMessage("Found download URL: " + url))
            UI.return_main_screen(status_code=0)
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
        tag_machine = self.get_tag_machine()

        reg_expression = r'href="\S+desktop-developer\/linux{}\/([\w\-]+)\/"'.format(tag_machine)
        languages = []
        decoded_page = result[self.download_page].buffer.getvalue().decode()
        for index, p in enumerate(re.finditer(reg_expression, decoded_page)):
            with suppress(AttributeError):
                lang = p.group(1)

            with suppress(AttributeError):
                url = f'https://download.mozilla.org/?product=firefox-devedition-latest-ssl&os=linux{tag_machine}&lang={lang}'

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
                        icon_path=os.path.join(self.install_path,
                                               "browser", "chrome", "icons", "default", "default128.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("Firefox Aurora with Developer tools"),
                        categories="Development;IDE;",
                        extra="StartupWMClass=Firefox Developer Edition"))

    def install_framework_parser(self, parser):
        this_framework_parser = super().install_framework_parser(parser)
        this_framework_parser.add_argument('--lang', dest="lang", action="store",
                                           help=_("Install in given language without prompting"))
        return this_framework_parser

    def run_for(self, args):
        if args.lang:
            self.arg_lang = args.lang
        super().run_for(args)


class PhantomJS(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="PhantomJS", description=_("headless WebKit scriptable with a JavaScript API"),
                         is_category_default=False,
                         only_on_archs=['i386', 'amd64'],
                         download_page="http://phantomjs.org/download.html",
                         dir_to_decompress_in_tarball="phantomjs*",
                         required_files_path=[os.path.join("bin", "phantomjs")],
                         version_regex=r'(\d+\.\d+)',
                         supports_update=True,
                         **kwargs)

    arch_trans = {
        "amd64": "x86_64",
        "i386": "i686"
    }

    def parse_download_link(self, line, in_download):
        """Parse PhantomJS download link, expect to find a sha and a url"""
        url = None
        string = 'linux-{}.tar.bz2">'.format(self.arch_trans[get_current_arch()])
        if string in line:
            in_download = True
        if in_download is True:
            p = re.search(r'href="(.*)">', line)
            with suppress(AttributeError):
                url = p.group(1)

        if url is None:
            return (None, in_download)
        return ((url, None), in_download)

    def post_install(self):
        """Add phantomjs necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "bin")}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'ChangeLog'), 'r') as file:
                lines = ''.join(file.readline() for _ in range(3))
                match = re.search(r'(\d+\.\d+)', lines)
                return match.group(1) if match else None
        except FileNotFoundError:
            return


class Geckodriver(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Geckodriver",
                         description=_("Proxy for using W3C WebDriver compatible clients " +
                                       "to interact with Gecko-based browsers."),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/mozilla/geckodriver/releases/latest",
                         dir_to_decompress_in_tarball=".",
                         required_files_path=["geckodriver"],
                         version_regex=r'v(\d+\.\d+\.\d+)',
                         supports_update=True,
                         json=True, **kwargs)

    arch_trans = {
        "amd64": "linux64",
        "i386": "linux32",
        "armhf": "arm7hf"
    }

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if asset["browser_download_url"].endswith("{}.tar.gz".format(self.arch_trans[get_current_arch()])):
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Add the Geckodriver binary dir to PATH"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path)}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))

    @staticmethod
    def get_current_user_version(install_path):
        try:
            command = f"{os.path.join(install_path, 'geckodriver')} --version"
            result = subprocess.check_output(command, shell=True, text=True)
            first_line = result.split('\n')[0]
            match = re.search(r'geckodriver\s+(\d+\.\d+\.\d+)', first_line)
            return match.group(1) if match else None
        except subprocess.CalledProcessError:
            return



class Chromedriver(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Chromedriver", description=_("WebDriver for Chrome"),
                         only_on_archs=['amd64'],
                         download_page="https://chromedriver.storage.googleapis.com/LATEST_RELEASE",
                         dir_to_decompress_in_tarball=".",
                         required_files_path=["chromedriver"],
                         version_regex=r'/(\d+\.\d+\.\d+\.\d+)',
                         supports_update=True,
                         **kwargs)

    def parse_download_link(self, line, in_download):
        """Parse Chromedriver download links"""
        url = None
        with suppress(AttributeError):
            url = "https://chromedriver.storage.googleapis.com/{}/chromedriver_linux64.zip".format(line)
        return ((url, None), in_download)

    def post_install(self):
        """Add Chromedriver necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path)}})
        UI.delayed_display(DisplayMessage(self.RELOGIN_REQUIRE_MSG.format(self.name)))

    @staticmethod
    def get_current_user_version(install_path):
        try:
            command = f"{os.path.join(install_path, 'chromedriver')} --version"
            result = subprocess.check_output(command, shell=True, text=True)
            match = re.search(r'ChromeDriver\s+([\d.]+)', result)
            return match.group(1) if match else None
        except subprocess.CalledProcessError:
            return
