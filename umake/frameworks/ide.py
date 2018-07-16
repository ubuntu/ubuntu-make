# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Canonical
#
# Authors:
#  Didier Roche
#  Tin Tvrtković
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


"""Generic IDE module."""
from abc import ABCMeta, abstractmethod
from concurrent import futures
from contextlib import suppress
from gettext import gettext as _
import grp
from io import StringIO
import json
import logging
import os
from os.path import join
import pwd
import platform
import re
import subprocess
from urllib import parse
import shutil

import umake.frameworks.baseinstaller
from umake.frameworks.electronics import Arduino
from umake.interactions import DisplayMessage, LicenseAgreement
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.tools import as_root, create_launcher, get_application_desktop_file, ChecksumType, Checksum, MainLoop,\
    strip_tags, add_env_to_user, add_exec_link, get_current_arch
from umake.ui import UI

logger = logging.getLogger(__name__)


class IdeCategory(umake.frameworks.BaseCategory):
    def __init__(self):
        super().__init__(name="IDE", description=_("Generic IDEs"),
                         logo_path=None)


class BaseEclipse(umake.frameworks.baseinstaller.BaseInstaller, metaclass=ABCMeta):
    """The Eclipse Foundation distribution."""

    def __init__(self, *args, **kwargs):
        if self.executable:
            current_required_files_path = kwargs.get("required_files_path", [])
            current_required_files_path.append(os.path.join(self.executable))
            kwargs["required_files_path"] = current_required_files_path
        download_page = 'https://www.eclipse.org/downloads/eclipse-packages/'
        kwargs["download_page"] = download_page
        super().__init__(*args, **kwargs)
        self.icon_url = os.path.join("https://www.eclipse.org/downloads/", "images", self.icon_filename)
        self.bits = '' if platform.machine() == 'i686' else 'x86_64'
        self.headers = {'User-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu "
                                      "Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36"}

    @property
    @abstractmethod
    def download_keyword(self):
        pass

    @property
    @abstractmethod
    def executable(self):
        pass

    def download_provider_page(self):
        logger.debug("Download application provider page")
        DownloadCenter([DownloadItem(self.download_page, headers=self.headers)], self.get_metadata, download=False)

    def parse_download_link(self, line, in_download):
        """Parse Eclipse download links"""
        url_found = False
        if self.download_keyword in line and self.bits in line:
            in_download = True
        else:
            in_download = False
        if in_download:
            p = re.search(r'href="(.*)" title', line)
            with suppress(AttributeError):
                self.sha512_url = "https://www.eclipse.org/" + p.group(1) + '.sha512&mirror_id=1'
                url_found = True
                DownloadCenter(urls=[DownloadItem(self.sha512_url, None)],
                               on_done=self.get_sha_and_start_download, download=False)
        return (url_found, in_download)

    @MainLoop.in_mainloop_thread
    def get_metadata(self, result):
        """Download files to download + license and check it"""
        logger.debug("Parse download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        in_download = False
        url_found = False
        for line in result[self.download_page].buffer:
            line_content = line.decode()
            (_url_found, in_download) = self.parse_download_link(line_content, in_download)
            if not url_found:
                url_found = _url_found

        if not url_found:
            logger.error("Download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.sha512_url]
        sha512 = res.buffer.getvalue().decode('utf-8').split()[0]
        # you get and store self.download_url
        url = re.sub('.sha512', '', self.sha512_url)
        if url is None:
            logger.error("Download page changed its syntax or is not parsable (missing url)")
            UI.return_main_screen(status_code=1)
        if sha512 is None:
            logger.error("Download page changed its syntax or is not parsable (missing sha512)")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download link for {}, checksum: {}".format(url, sha512))
        self.download_requests.append(DownloadItem(url, Checksum(ChecksumType.sha512, sha512)))
        self.start_download_and_install()

    def post_install(self):
        """Create the Eclipse launcher"""
        DownloadCenter(urls=[DownloadItem(self.icon_url, None)],
                       on_done=self.save_icon, download=True)
        icon_path = join(self.install_path, self.icon_filename)
        comment = self.description
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=self.name,
                                                     icon_path=icon_path,
                                                     try_exec=self.exec_path,
                                                     exec=self.exec_link_name,
                                                     comment=comment,
                                                     categories=categories))

    def save_icon(self, download_result):
        """Save correct Eclipse icon"""
        icon = download_result.pop(self.icon_url).fd.name
        shutil.copy(icon, join(self.install_path, self.icon_filename))
        logger.debug("Copied icon: {}".format(self.icon_url))


class EclipseJava(BaseEclipse):
    """The Eclipse Java Edition distribution."""
    download_keyword = 'eclipse-java-'
    executable = 'eclipse'

    def __init__(self, **kwargs):
        super().__init__(name="Eclipse",
                         description=_("Eclipse Java IDE"),
                         dir_to_decompress_in_tarball='eclipse',
                         desktop_filename='eclipse-java.desktop',
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         icon_filename='java.png',
                         **kwargs)


class EclipseJEE(BaseEclipse):
    """The Eclipse JEE Edition distribution."""
    download_keyword = 'eclipse-jee-'
    executable = 'eclipse'

    def __init__(self, **kwargs):
        super().__init__(name="Eclipse JEE",
                         description=_("Eclipse JEE IDE"),
                         dir_to_decompress_in_tarball='eclipse',
                         desktop_filename='eclipse-jee.desktop',
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         icon_filename='javaee.png',
                         **kwargs)


class EclipsePHP(BaseEclipse):
    """The Eclipse PHP Edition distribution."""
    download_keyword = 'eclipse-php-'
    executable = 'eclipse'

    def __init__(self, **kwargs):
        super().__init__(name="Eclipse PHP",
                         description=_("Eclipse PHP IDE"),
                         dir_to_decompress_in_tarball='eclipse',
                         desktop_filename='eclipse-php.desktop',
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         icon_filename='php.png',
                         **kwargs)


class EclipseJS(BaseEclipse):
    """Eclipse IDE for JavaScript and Web distribution."""
    download_keyword = 'eclipse-javascript-'
    executable = 'eclipse'

    def __init__(self, **kwargs):
        super().__init__(name="Eclipse JavaScript",
                         description=_("Eclipse IDE for JavaScript and Web Developers"),
                         dir_to_decompress_in_tarball='eclipse',
                         desktop_filename='eclipse-javascript.desktop',
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         icon_filename='javascript.png',
                         **kwargs)


class EclipseCPP(BaseEclipse):
    """The Eclipse CPP Edition distribution."""
    download_keyword = 'eclipse-cpp-'
    executable = 'eclipse'

    def __init__(self, **kwargs):
        super().__init__(name="Eclipse CPP",
                         description=_("Eclipse C/C++ IDE"),
                         dir_to_decompress_in_tarball='eclipse',
                         desktop_filename='eclipse-cpp.desktop',
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         icon_filename='cdt.png',
                         **kwargs)


class BaseJetBrains(umake.frameworks.baseinstaller.BaseInstaller, metaclass=ABCMeta):
    """The base for all JetBrains installers."""

    def __init__(self, *args, **kwargs):
        """Add executable required file path to existing list"""
        if self.executable:
            current_required_files_path = kwargs.get("required_files_path", [])
            current_required_files_path.append(os.path.join("bin", self.executable))
            kwargs["required_files_path"] = current_required_files_path
        download_page = "https://data.services.jetbrains.com/products/releases?code={}".format(self.download_keyword)
        kwargs["download_page"] = download_page
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def download_keyword(self):
        pass

    @property
    @abstractmethod
    def executable(self):
        pass

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        logger.debug("Fetched download page, parsing.")

        page = result[self.download_page]

        error_msg = page.error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        try:
            key, content = json.loads(page.buffer.read().decode()).popitem()
        except (json.JSONDecodeError):
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)
        try:
            download_list = content[0]
        except (IndexError):
            if '&type=eap' in self.download_page:
                logger.error("No EAP version available.")
            else:
                logger.error("No Stable version available.")
            UI.return_main_screen(status_code=1)
        try:
            download_url = download_list['downloads']['linux']['link']
            checksum_url = download_list['downloads']['linux']['checksumLink']
        except (IndexError):
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download URL: " + download_url)
        logger.debug("Downloading checksum first, from " + checksum_url)

        def checksum_downloaded(results):
            checksum_result = next(iter(results.values()))  # Just get the first.
            if checksum_result.error:
                logger.error(checksum_result.error)
                UI.return_main_screen(status_code=1)

            checksum = checksum_result.buffer.getvalue().decode('utf-8').split()[0]
            logger.info('Obtained SHA256 checksum: ' + checksum)

            self.download_requests.append(DownloadItem(download_url,
                                                       checksum=Checksum(ChecksumType.sha256, checksum),
                                                       ignore_encoding=True))
            self.start_download_and_install()

        DownloadCenter([DownloadItem(checksum_url)], on_done=checksum_downloaded, download=False)

    def post_install(self):
        """Create the appropriate JetBrains launcher."""
        icon_path = join(self.install_path, 'bin', self.icon_filename)
        comment = self.description + " (UDTC)"
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=self.name,
                                                     icon_path=icon_path,
                                                     try_exec=self.exec_path,
                                                     exec=self.exec_link_name,
                                                     comment=comment,
                                                     categories=categories))

    def install_framework_parser(self, parser):
        this_framework_parser = super().install_framework_parser(parser)
        this_framework_parser.add_argument('--eap', action="store_true",
                                           help=_("Install EAP version if available"))
        return this_framework_parser

    def run_for(self, args):
        if args.eap:
            self.download_page += '&type=eap'
            self.name += " EAP"
            self.description += " EAP"
            self.desktop_filename = self.desktop_filename.replace(".desktop", "-eap.desktop")
            self.install_path += "-eap"
        super().run_for(args)


class PyCharm(BaseJetBrains):
    """The JetBrains PyCharm Community Edition distribution."""
    download_keyword = 'PCC'
    executable = "pycharm.sh"

    def __init__(self, **kwargs):
        super().__init__(name="PyCharm",
                         description=_("PyCharm Community Edition"),
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['python', 'python3'],
                         dir_to_decompress_in_tarball='pycharm-community-*',
                         desktop_filename='jetbrains-pycharm-ce.desktop',
                         icon_filename='pycharm.png',
                         **kwargs)


class PyCharmEducational(BaseJetBrains):
    """The JetBrains PyCharm Educational Edition distribution."""
    download_keyword = 'PCE'
    executable = "pycharm.sh"

    def __init__(self, **kwargs):
        super().__init__(name="PyCharm Educational",
                         description=_("PyCharm Educational Edition"),
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['python', 'python3'],
                         dir_to_decompress_in_tarball='pycharm-edu*',
                         desktop_filename='jetbrains-pycharm-edu.desktop',
                         icon_filename='pycharm.png',
                         **kwargs)


class PyCharmProfessional(BaseJetBrains):
    """The JetBrains PyCharm Professional Edition distribution."""
    download_keyword = 'PCP'
    executable = "pycharm.sh"

    def __init__(self, **kwargs):
        super().__init__(name="PyCharm Professional",
                         description=_("PyCharm Professional Edition"),
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['python', 'python3'],
                         dir_to_decompress_in_tarball='pycharm-*',
                         desktop_filename='jetbrains-pycharm.desktop',
                         icon_filename='pycharm.png',
                         **kwargs)


class Idea(BaseJetBrains):
    """The JetBrains IntelliJ Idea Community Edition distribution."""
    download_keyword = 'IIC'
    executable = "idea.sh"

    def __init__(self, **kwargs):
        super().__init__(name="Idea",
                         description=_("IntelliJ IDEA Community Edition"),
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         dir_to_decompress_in_tarball='idea-IC-*',
                         desktop_filename='jetbrains-idea-ce.desktop',
                         icon_filename='idea.png',
                         **kwargs)


class IdeaUltimate(BaseJetBrains):
    """The JetBrains IntelliJ Idea Ultimate Edition distribution."""
    download_keyword = 'IIU'
    executable = "idea.sh"

    def __init__(self, **kwargs):
        super().__init__(name="Idea Ultimate",
                         description=_("IntelliJ IDEA"),
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         dir_to_decompress_in_tarball='idea-IU-*',
                         desktop_filename='jetbrains-idea.desktop',
                         icon_filename='idea.png',
                         **kwargs)


class RubyMine(BaseJetBrains):
    """The JetBrains RubyMine IDE"""
    download_keyword = 'RM'
    executable = "rubymine.sh"

    def __init__(self, **kwargs):
        super().__init__(name="RubyMine",
                         description=_("Ruby on Rails IDE"),
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['ruby'],
                         dir_to_decompress_in_tarball='RubyMine-*',
                         desktop_filename='jetbrains-rubymine.desktop',
                         icon_filename='rubymine.png',
                         **kwargs)


class WebStorm(BaseJetBrains):
    """The JetBrains WebStorm IDE"""
    download_keyword = 'WS'
    executable = "webstorm.sh"

    def __init__(self, **kwargs):
        super().__init__(name="WebStorm",
                         description=_("Complex client-side and server-side javascript IDE"),
                         only_on_archs=['i386', 'amd64'],
                         dir_to_decompress_in_tarball='WebStorm-*',
                         desktop_filename='jetbrains-webstorm.desktop',
                         icon_filename='webstorm.svg',
                         **kwargs)


class PhpStorm(BaseJetBrains):
    """The JetBrains PhpStorm IDE"""
    download_keyword = 'PS'
    executable = "phpstorm.sh"

    def __init__(self, **kwargs):
        super().__init__(name="PhpStorm",
                         description=_("PHP and web development IDE"),
                         only_on_archs=['i386', 'amd64'],
                         dir_to_decompress_in_tarball='PhpStorm-*',
                         desktop_filename='jetbrains-phpstorm.desktop',
                         icon_filename='phpstorm.png',
                         **kwargs)


class CLion(BaseJetBrains):
    """The JetBrains CLion IDE"""
    download_keyword = 'CL'
    executable = "clion.sh"

    def __init__(self, **kwargs):
        super().__init__(name="CLion",
                         description=_("CLion integrated C/C++ IDE"),
                         only_on_archs=['amd64'],
                         dir_to_decompress_in_tarball='clion-*',
                         desktop_filename='jetbrains-clion.desktop',
                         icon_filename='clion.svg',
                         **kwargs)


class DataGrip(BaseJetBrains):
    """The JetBrains DataGrip IDE"""
    download_keyword = 'DG'
    executable = "datagrip.sh"

    def __init__(self, **kwargs):
        super().__init__(name="DataGrip",
                         description=_("DataGrip SQL and databases IDE"),
                         only_on_archs=['i386', 'amd64'],
                         dir_to_decompress_in_tarball='DataGrip-*',
                         desktop_filename='jetbrains-datagrip.desktop',
                         icon_filename='datagrip.png',
                         **kwargs)


class GoLand(BaseJetBrains):
    """The JetBrains GoLand IDE"""
    download_keyword = 'GO'
    executable = "goland.sh"

    def __init__(self, **kwargs):
        super().__init__(name="GoLand",
                         description=_("The Drive to Develop"),
                         only_on_archs=['i386', 'amd64'],
                         dir_to_decompress_in_tarball='GoLand-*',
                         desktop_filename='jetbrains-goland.desktop',
                         icon_filename='goland.png',
                         **kwargs)


class Rider(BaseJetBrains):
    """The JetBrains  cross-platform .NET IDE"""
    download_keyword = 'RD'
    executable = "rider.sh"

    def __init__(self, **kwargs):
        super().__init__(name="Rider",
                         description=_("The JetBrains cross-platform .NET IDE"),
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['mono-devel'],
                         dir_to_decompress_in_tarball='JetBrains Rider-*',
                         desktop_filename='jetbrains-rider.desktop',
                         icon_filename='rider.png',
                         **kwargs)


class BaseNetBeans(umake.frameworks.baseinstaller.BaseInstaller):
    """The base for all Netbeans installers."""

    BASE_URL = "http://download.netbeans.org/netbeans"
    EXECUTABLE = "nb/netbeans"

    def __init__(self, flavour="", **kwargs):
        """The constructor.
        @param category The IDE category.
        @param flavour The Netbeans flavour (plugins bundled).
        """
        # add a separator to the string, like -cpp
        if flavour:
            flavour = '-' + flavour
        self.flavour = flavour

        super().__init__(name="Netbeans",
                         description=_("Netbeans IDE"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://netbeans.org/downloads/zip.html",
                         dir_to_decompress_in_tarball="netbeans*",
                         desktop_filename="netbeans{}.desktop".format(flavour),
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         required_files_path=[os.path.join("bin", "netbeans")],
                         **kwargs)

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Get the latest version and trigger the download of the download_page file.
        :param result: the file downloaded by DownloadCenter, contains a web page
        """
        # Processing the string to obtain metadata (version)
        try:
            url_version_str = result[self.download_page].buffer.read().decode('utf-8')
        except AttributeError:
            # The file could not be parsed or there is no network connection
            logger.error("The download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

        preg = re.compile(".*/images_www/v6/download/.*")
        for line in url_version_str.split("\n"):
            if preg.match(line):
                line = line.replace("var PAGE_ARTIFACTS_LOCATION = \"/images"
                                    "_www/v6/download/", "").replace("/\";", "").replace('/final', '')
                self.version = line.strip()

        if not self.version:
            # Fallback
            logger.error("Could not determine latest version")
            UI.return_main_screen(status_code=1)

        self.version_download_page = "https://netbeans.org/images_www/v6/download/" \
                                     "{}/final/js/files.js".format(self.version)
        DownloadCenter([DownloadItem(self.version_download_page)], self.parse_download_page_callback, download=False)

    @MainLoop.in_mainloop_thread
    def parse_download_page_callback(self, result):
        """Get the download_url and trigger the download and installation of the app.
        :param result: the file downloaded by DownloadCenter, contains js functions with download urls
        """
        logger.info("Netbeans {}".format(self.version))

        # Processing the string to obtain metadata (download url)
        try:
            url_file = result[self.version_download_page].buffer.read().decode('utf-8')
        except AttributeError:
            # The file could not be parsed
            logger.error("The download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

        preg = re.compile('add_file\("zip/netbeans-{}-[0-9]{{12}}{}.zip"'.format(self.version,
                                                                                 self.flavour))
        for line in url_file.split("\n"):
            if preg.match(line):
                # Clean up the string from js (it's a function call)
                line = line.replace("add_file(", "").replace(");", "").replace('"', "")
                url_string = line

        if not url_string:
            # The file could not be parsed
            logger.error("The download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

        string_array = url_string.split(", ")
        try:
            url_suffix = string_array[0]
            sha256 = string_array[2]
        except IndexError:
            # The file could not be parsed
            logger.error("The download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

        download_url = "{}/{}/final/{}".format(self.BASE_URL, self.version, url_suffix)
        self.download_requests.append(DownloadItem(download_url, Checksum(ChecksumType.sha256, sha256)))
        self.start_download_and_install()

    def post_install(self):
        """Create the Netbeans launcher"""
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=_("Netbeans IDE"),
                                                     icon_path=join(self.install_path, "nb", "netbeans.png"),
                                                     try_exec=self.exec_path,
                                                     exec=self.exec_link_name,
                                                     comment=_("Netbeans IDE"),
                                                     categories="Development;IDE;"))


class VisualStudioCode(umake.frameworks.baseinstaller.BaseInstaller):

    PERM_DOWNLOAD_LINKS = {
        "i686": "https://go.microsoft.com/fwlink/?LinkID=620885",
        "x86_64": "https://go.microsoft.com/fwlink/?LinkID=620884",
        "i686-insiders": "https://go.microsoft.com/fwlink/?LinkId=723969",
        "x86_64-insiders": "https://go.microsoft.com/fwlink/?LinkId=723968"
    }

    def __init__(self, **kwargs):
        super().__init__(name="Visual Studio Code", description=_("Visual Studio focused on modern web and cloud"),
                         only_on_archs=['i386', 'amd64'], expect_license=True,
                         download_page="https://code.visualstudio.com/License",
                         desktop_filename="visual-studio-code.desktop",
                         required_files_path=["bin/code"],
                         dir_to_decompress_in_tarball="VSCode-linux-*",
                         packages_requirements=["libgtk2.0-0", "libgconf-2-4"],
                         **kwargs)

    def parse_license(self, line, license_txt, in_license):
        """Parse Android Studio download page for license"""
        if 'SOFTWARE LICENSE TERMS' in line:
            in_license = True
        if in_license and "</div>" in line:
            in_license = False

        if in_license:
            license_txt.write(line.strip() + "\n")
        return in_license

    def parse_download_link(self, line, in_download):
        """We have persistent links for Visual Studio Code, return it right away"""
        url = None
        version = platform.machine()
        if 'Insiders' in self.name:
            version += '-insiders'
        with suppress(KeyError):
            url = self.PERM_DOWNLOAD_LINKS[version]
        return ((url, None), in_download)

    def post_install(self):
        """Create the Visual Studio Code launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Visual Studio Code"),
                        icon_path=os.path.join(self.install_path, "resources", "app", "resources", "linux",
                                               "code.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("Visual Studio focused on modern web and cloud"),
                        categories="Development;IDE;",
                        extra="StartupWMClass=Code"))

    def install_framework_parser(self, parser):
        this_framework_parser = super().install_framework_parser(parser)
        this_framework_parser.add_argument('--insiders', action="store_true",
                                           help=_("Install Insiders version if available"))
        return this_framework_parser

    def run_for(self, args):
        if args.insiders:
            self.name += " Insiders"
            self.description += " insiders"
            self.desktop_filename = self.desktop_filename.replace(".desktop", "-insiders.desktop")
            self.install_path += "-insiders"
            self.required_files_path = ["bin/code-insiders"]
        super().run_for(args)


class LightTable(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="LightTable", description=_("LightTable code editor"),
                         only_on_archs=['amd64'],
                         download_page="https://api.github.com/repos/LightTable/LightTable/releases/latest",
                         desktop_filename="lighttable.desktop",
                         required_files_path=["LightTable"],
                         dir_to_decompress_in_tarball="lighttable-*",
                         checksum_type=ChecksumType.md5,
                         **kwargs)

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        logger.debug("Fetched download page, parsing.")
        page = result[self.download_page]
        error_msg = page.error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        try:
            assets = json.loads(page.buffer.read().decode())["assets"]
            download_url = None
            for asset in assets:
                if "linux" in asset["browser_download_url"]:
                    download_url = asset["browser_download_url"]
            if not download_url:
                raise IndexError
        except (json.JSONDecodeError, IndexError):
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download URL: " + download_url)

        self.download_requests.append(DownloadItem(download_url, None))
        self.start_download_and_install()

    def post_install(self):
        """Create the LightTable Code launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("LightTable"),
                        icon_path=os.path.join(self.install_path, "resources", "app", "core", "img",
                                               "lticon.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("LightTable code editor"),
                        categories="Development;IDE;"))


class Atom(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Atom", description=_("The hackable text editor"),
                         only_on_archs=['amd64'],
                         download_page="https://api.github.com/repos/Atom/Atom/releases/latest",
                         desktop_filename="atom.desktop",
                         required_files_path=["atom", "resources/app/apm/bin/apm"],
                         dir_to_decompress_in_tarball="atom-*",
                         packages_requirements=["libgconf-2-4"],
                         checksum_type=ChecksumType.md5, **kwargs)

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        logger.debug("Fetched download page, parsing.")
        page = result[self.download_page]
        error_msg = page.error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        try:
            if "beta" in self.description:
                latest_beta = json.loads(page.buffer.read().decode())[0]
                if "beta" not in latest_beta["tag_name"]:
                    logger.error("Latest version is not beta.")
                    UI.return_main_screen(status_code=1)
                assets = latest_beta["assets"]
            else:
                assets = json.loads(page.buffer.read().decode())["assets"]
            download_url = None
            for asset in assets:
                if "tar.gz" in asset["browser_download_url"]:
                    download_url = asset["browser_download_url"]
            if not download_url:
                raise IndexError
        except (json.JSONDecodeError, IndexError):
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download URL: " + download_url)

        self.download_requests.append(DownloadItem(download_url, None))
        self.start_download_and_install()

    def post_install(self):
        """Create the Atom Code launcher"""
        # Add apm to PATH
        add_exec_link(os.path.join(self.install_path, "resources", "app", "apm", "bin", "apm"),
                      os.path.join(self.default_binary_link_path, 'apm'))
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Atom"),
                        icon_path=os.path.join(self.install_path, "atom.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("The hackable text editor"),
                        categories="Development;IDE;"))

    def install_framework_parser(self, parser):
        this_framework_parser = super().install_framework_parser(parser)
        this_framework_parser.add_argument('--beta', action="store_true",
                                           help=_("Install Beta version if available"))
        return this_framework_parser

    def run_for(self, args):
        if args.beta:
            self.name += " Beta"
            self.description += " beta"
            self.desktop_filename = self.desktop_filename.replace(".desktop", "-beta.desktop")
            self.download_page = "https://api.github.com/repos/Atom/Atom/releases"
            self.install_path += "-beta"
        super().run_for(args)


class DBeaver(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="DBeaver", description=_("Free universal database manager and SQL client"),
                         only_on_archs=['amd64', 'i386'],
                         download_page="https://api.github.com/repos/DBeaver/DBeaver/releases/latest",
                         desktop_filename="dbeaver.desktop",
                         required_files_path=["dbeaver"],
                         dir_to_decompress_in_tarball="dbeaver",
                         packages_requirements=['openjdk-8-jre-headless'],
                         **kwargs)
    arch_trans = {
        "amd64": "x86_64",
        "i386": "x86"
    }

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        logger.debug("Fetched download page, parsing.")
        page = result[self.download_page]
        error_msg = page.error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        try:
            assets = json.loads(page.buffer.read().decode())["assets"]
            download_url = None
            for asset in assets:
                if "linux.gtk.{}.tar.gz".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                    download_url = asset["browser_download_url"]
            if not download_url:
                raise IndexError
        except (json.JSONDecodeError, IndexError):
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download URL: " + download_url)

        self.download_requests.append(DownloadItem(download_url, None))
        self.start_download_and_install()

    def post_install(self):
        """Create the DBeaver launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=self.name,
                        icon_path=os.path.join(self.install_path, "dbeaver.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;"))


class SublimeText(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Sublime Text", description=_("Sophisticated text editor for code, markup and prose"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://sublimetext.com/3",
                         desktop_filename="sublime-text.desktop",
                         required_files_path=["sublime_text"],
                         dir_to_decompress_in_tarball="sublime_text_*",
                         **kwargs)

    arch_trans = {
        "amd64": "x64",
        "i386": "x32"
    }

    def parse_download_link(self, line, in_download):
        """Parse SublimeText download links"""
        url = None
        if '.tar.bz2' in line:
            p = re.search(r'href="([^<]*{}.tar.bz2)"'.format(self.arch_trans[get_current_arch()]), line)
            with suppress(AttributeError):
                url = p.group(1)
        return ((url, None), in_download)

    def post_install(self):
        """Create the Sublime Text Code launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Sublime Text"),
                        icon_path=os.path.join(self.install_path, "Icon", "128x128", "sublime-text.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("Sophisticated text editor for code, markup and prose"),
                        categories="Development;TextEditor;"))


class SpringToolsSuite(umake.frameworks.baseinstaller.BaseInstaller):
    def __init__(self, **kwargs):
        super().__init__(name="Spring Tools Suite",
                         description=_("Spring Tools Suite IDE"),
                         download_page="https://spring.io/tools/sts/all",
                         dir_to_decompress_in_tarball='sts-bundle/sts-*',
                         checksum_type=ChecksumType.sha1,
                         desktop_filename='STS.desktop',
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         icon_filename='icon.xpm',
                         required_files_path=["STS"],
                         **kwargs)
        self.arch = '' if platform.machine() == 'i686' else '-x86_64'
        self.checksum_url = None

    def parse_download_link(self, line, in_download):
        """Parse STS download links"""
        url_found = False
        if 'linux-gtk{}.tar.gz'.format(self.arch) in line:
            in_download = True
        else:
            in_download = False
        if in_download:
            p = re.search(r'href="(.*.tar.gz)"', line)
            with suppress(AttributeError):
                self.checksum_url = p.group(1) + '.sha1'
                url_found = True
                DownloadCenter(urls=[DownloadItem(self.checksum_url, None)],
                               on_done=self.get_sha_and_start_download, download=False)
        return (url_found, in_download)

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Download files to download + license and check it"""
        logger.debug("Parse download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        in_download = False
        url_found = False
        for line in result[self.download_page].buffer:
            line_content = line.decode()
            (_url_found, in_download) = self.parse_download_link(line_content, in_download)
            if not url_found:
                url_found = _url_found

        if not url_found:
            logger.error("Download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.checksum_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        # you get and store self.download_url
        url = re.sub('.sha1', '', self.checksum_url)
        if url is None:
            logger.error("Download page changed its syntax or is not parsable (missing url)")
            UI.return_main_screen(status_code=1)
        if checksum is None:
            logger.error("Download page changed its syntax or is not parsable (missing sha512)")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download link for {}, checksum: {}".format(url, checksum))
        self.download_requests.append(DownloadItem(url, Checksum(self.checksum_type, checksum)))
        self.start_download_and_install()

    def post_install(self):
        """Create the Spring Tools Suite launcher"""
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_(self.name),
                                                                            icon_path=os.path.join(self.install_path,
                                                                                                   self.icon_filename),
                                                                            try_exec=self.exec_path,
                                                                            exec=self.exec_link_name,
                                                                            comment=_(self.description),
                                                                            categories=categories))


class Processing(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Processing", description=_("Processing code editor"),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/processing/processing/releases/latest",
                         desktop_filename="processing.desktop",
                         required_files_path=["processing"],
                         dir_to_decompress_in_tarball="processing-*",
                         **kwargs)

    arch_trans = {
        "amd64": "64",
        "i386": "32"
    }

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        logger.debug("Fetched download page, parsing.")
        page = result[self.download_page]
        error_msg = page.error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        try:
            assets = json.loads(page.buffer.read().decode())["assets"]
            download_url = None
            for asset in assets:
                if "linux{}".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                    download_url = asset["browser_download_url"]
            if not download_url:
                raise IndexError
        except (json.JSONDecodeError, IndexError):
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download URL: " + download_url)

        self.download_requests.append(DownloadItem(download_url, None))
        self.start_download_and_install()

    def post_install(self):
        """Create the Processing Code launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Processing"),
                        icon_path=os.path.join(self.install_path, "lib", "icons", "pde-256.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("Processing is a flexible software sketchbook"),
                        categories="Development;IDE;"))


class Arduino(Arduino):

    def setup(self, *args, **kwargs):
        '''Print a deprecation warning before calling parent setup()'''
        logger.warning("Arduino is now in the electronics category, please refer it from this category from now on. "
                       "This compatibility will be dropped in the future.")
        super().setup(*args, **kwargs)
