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
        kwargs["checksum_type"] = ChecksumType.sha512
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
        DownloadCenter([DownloadItem(self.download_page, headers=self.headers)],
                       self.get_metadata_and_check_license, download=False)

    def parse_download_link(self, line, in_download):
        """Parse Eclipse download links"""
        if self.download_keyword in line and self.bits in line and 'linux' in line:
            in_download = True
        else:
            in_download = False
        if in_download:
            p = re.search(r"href='(http://www\.eclipse\.org\/downloads/download\.php\?file=.*\.tar\.gz)'", line)
            with suppress(AttributeError):
                self.new_download_url = p.group(1).replace('download.php', 'sums.php').replace('http://', 'https://')
                self.https = True if parse.splittype(self.new_download_url)[0] is "https" else False
        return ((None, None), in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        url = self.new_download_url.replace('sums.php', 'download.php') + '&r=1'
        if not self.https:
            self.new_download_url = 'https://' + parse.splittype(self.new_download_url)[1]
        self.check_data_and_start_download(url, checksum)

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
        kwargs["json"] = True
        kwargs["checksum_type"] = ChecksumType.sha256
        super().__init__(*args, **kwargs)

    @property
    @abstractmethod
    def download_keyword(self):
        pass

    @property
    @abstractmethod
    def executable(self):
        pass

    def parse_download_link(self, line, in_download):
        key, content = line.popitem()
        content = content[0]
        self.url = content['downloads']['linux']['link']
        self.new_download_url = content['downloads']['linux']['checksumLink']

        # Url is not defined here, but later on in the start_download
        return (None, in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        self.check_data_and_start_download(self.url, checksum)

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


class BaseNetBeans(umake.frameworks.baseinstaller.BaseInstaller, metaclass=ABCMeta):
    """The base for all Netbeans installers."""

    BASE_URL = "http://download.netbeans.org/netbeans"
    EXECUTABLE = "nb/netbeans"

    def __init__(self, *args, **kwargs):
        """Add executable required file path to existing list"""
        if self.executable:
            current_required_files_path = kwargs.get("required_files_path", [])
            current_required_files_path.append(os.path.join("bin", self.executable))
            kwargs["required_files_path"] = current_required_files_path
        download_page = "https://netbeans.org/downloads/zip.html"
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

    def parse_download_link(self, line, in_download):
        """Parse Netbeans download links"""
        url, checksum = (None, None)
        if 'var PAGE_ARTIFACTS_LOCATION' in line:
            in_download = True
        else:
            in_download = False
        if in_download:
            p = re.search(r'var PAGE_ARTIFACTS_LOCATION = \"/images_www/v6/download/(\S+)/final/\";', line)
            with suppress(AttributeError):
                # url set to check in baseinstaller if missing
                self.version = p.group(1)
                self.new_download_url = "https://netbeans.org/images_www/v6/download/" + \
                                        "{}/final/js/files.js".format(self.version)
        return ((None, None), in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url].buffer.getvalue().decode('utf-8').split('\n')

        preg = re.compile(r'add_file\(\"zip/netbeans-{}-[0-9]{{12}}-?{}.zip"'.format(self.version,
                                                                                     self.download_keyword))

        for line in res:
            if preg.match(line):
                # Clean up the string from js (it's a function call)
                line = line.replace("add_file(", "").replace(");", "").replace('"', "")
                url_string = line

        string_array = url_string.split(", ")
        url_suffix = string_array[0]
        checksum = string_array[2]

        url = "{}/{}/final/{}".format(self.BASE_URL, self.version, url_suffix)
        self.check_data_and_start_download(url, checksum)

    def post_install(self):
        """Create the Netbeans launcher"""
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=self.name,
                                                     icon_path=join(self.install_path, "nb", "netbeans.png"),
                                                     try_exec=self.exec_path,
                                                     exec=self.exec_link_name,
                                                     comment=self.description,
                                                     categories="Development;IDE;"))


class Netbeans(BaseNetBeans):
    download_keyword = ''
    executable = "netbeans"

    def __init__(self, **kwargs):
        super().__init__(name=_("Netbeans"),
                         description=_("Extensible Java IDE"),
                         only_on_archs=['i386', 'amd64'],
                         desktop_filename="netbeans.desktop",
                         dir_to_decompress_in_tarball="netbeans*",
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         checksum_type=ChecksumType.sha256,
                         **kwargs)


class NetbeansJavaEE(BaseNetBeans):
    download_keyword = 'javaee'
    executable = "netbeans"

    def __init__(self, **kwargs):
        super().__init__(name=_("Netbeans JavaEE"),
                         description=_("Extensible Java IDE, JavaEE edition"),
                         only_on_archs=['i386', 'amd64'],
                         desktop_filename='netbeansjee.desktop',
                         dir_to_decompress_in_tarball="netbeans*",
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         checksum_type=ChecksumType.sha256,
                         **kwargs)


class NetbeansHTML(BaseNetBeans):
    download_keyword = 'html'
    executable = "netbeans"

    def __init__(self, **kwargs):
        super().__init__(name=_("Netbeans HTML"),
                         description=_("Extensible Java IDE, HTML edition"),
                         only_on_archs=['i386', 'amd64'],
                         desktop_filename='netbeanshtml.desktop',
                         dir_to_decompress_in_tarball="netbeans*",
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         checksum_type=ChecksumType.sha256,
                         **kwargs)


class NetbeansJavaEE(BaseNetBeans):
    download_keyword = 'cpppp'
    executable = "netbeans"

    def __init__(self, **kwargs):
        super().__init__(name=_("Netbeans JEE"),
                         description=_("Extensible Java IDE, C C++ edition"),
                         only_on_archs=['i386', 'amd64'],
                         desktop_filename='netbeansc.desktop',
                         dir_to_decompress_in_tarball="netbeans*",
                         packages_requirements=['openjdk-7-jdk | openjdk-8-jdk'],
                         checksum_type=ChecksumType.sha256,
                         **kwargs)


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
                         json=True, **kwargs)

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if "linux" in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

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
                         json=True, **kwargs)

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if "tar.gz" in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

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
                         json=True, **kwargs)
    arch_trans = {
        "amd64": "x86_64",
        "i386": "x86"
    }

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if "linux.gtk.{}.tar.gz".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

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
        self.new_download_url = None

    def parse_download_link(self, line, in_download):
        """Parse STS download links"""
        url, checksum = (None, None)
        if 'linux-gtk{}.tar.gz'.format(self.arch) in line:
            in_download = True
        else:
            in_download = False
        if in_download:
            p = re.search(r'href="(.*.tar.gz)"', line)
            with suppress(AttributeError):
                # url set to check in baseinstaller if missing
                url = p.group(1) + '.sha1'
                self.new_download_url = url
        return ((None, None), in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        # you get and store self.download_url
        url = re.sub('.sha1', '', self.new_download_url)
        self.check_data_and_start_download(url, checksum)

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
                         json=True, **kwargs)

    arch_trans = {
        "amd64": "64",
        "i386": "32"
    }

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if "linux{}".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Create the Processing Code launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Processing"),
                        icon_path=os.path.join(self.install_path, "lib", "icons", "pde-256.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("Processing is a flexible software sketchbook"),
                        categories="Development;IDE;"))


class LiteIDE(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="LiteIDE", description=_("LiteIDE is a simple, open source, cross-platform Go IDE."),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/visualfc/liteide/releases/latest",
                         packages_requirements=["libqt5core5a"],
                         desktop_filename="liteide.desktop",
                         required_files_path=["bin/liteide"],
                         dir_to_decompress_in_tarball="liteide",
                         json=True, **kwargs)

    arch_trans = {
        "amd64": "64",
        "i386": "32"
    }

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if "linux{}-qt5".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]:
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Create the LiteIDE Code launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("LiteIDE"),
                        icon_path=os.path.join(self.install_path, "share", "liteide",
                                               "welcome", "images", "liteide128.xpm"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("LiteIDE is a simple, open source, cross-platform Go IDE."),
                        categories="Development;IDE;"))


class Arduino(Arduino):

    def setup(self, *args, **kwargs):
        '''Print a deprecation warning before calling parent setup()'''
        logger.warning("Arduino is now in the electronics category, please refer it from this category from now on. "
                       "This compatibility will be dropped in the future.")
        super().setup(*args, **kwargs)
