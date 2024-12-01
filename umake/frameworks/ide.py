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
import json
import subprocess
from abc import ABCMeta, abstractmethod
from contextlib import suppress
from gettext import gettext as _
import logging
import os
import platform
import re
import shutil

import umake.frameworks.baseinstaller
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.tools import create_launcher, get_application_desktop_file, ChecksumType, MainLoop,\
    get_current_arch, get_current_distro_version

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
        download_page = 'https://www.eclipse.org/downloads/packages/'
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
            p = re.search(r"href='(https:)?\/\/www.eclipse.org(.*)'", line)
            with suppress(AttributeError):
                self.new_download_url = "https://www.eclipse.org" + p.group(2) + '.sha512&r=1'
        return (None, in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        url = self.new_download_url.replace('.sha512', '')
        self.check_data_and_start_download(url, checksum)

    def post_install(self):
        """Create the Eclipse launcher"""
        icon_path = os.path.join(self.install_path, "icon.xpm")
        if not os.path.exists(icon_path):
            DownloadCenter(urls=[DownloadItem(self.icon_url, None)],
                           on_done=self.save_icon, download=True)
            icon_path = os.path.join(self.install_path, self.icon_filename)
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
        shutil.copy(icon, os.path.join(self.install_path, self.icon_filename))
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
                         packages_requirements=['openjdk-11-jdk | openjdk-17-jdk | openjdk-18-jdk | openjdk-19-jdk | openjdk-20-jdk"'],
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
                         packages_requirements=['openjdk-11-jdk | openjdk-17-jdk | openjdk-18-jdk | openjdk-19-jdk | openjdk-20-jdk"'],
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
                         packages_requirements=['openjdk-11-jdk | openjdk-17-jdk | openjdk-18-jdk | openjdk-19-jdk | openjdk-20-jdk"'],
                         icon_filename='php.png',
                         **kwargs)


class EclipseJS(BaseEclipse):
    """Eclipse IDE for JavaScript and Web distribution."""
    download_keyword = 'eclipse-javascript-'
    executable = 'eclipse'

    def __init__(self, **kwargs):
        super().__init__(name="Eclipse JavaScript",
                         description="For removal only (tarfile not supported upstream anymore)",
                         download_page=None, only_on_archs=['i386', 'amd64'],
                         icon_filename='js.png',
                         only_for_removal=True, **kwargs)


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
                         packages_requirements=['openjdk-11-jdk | openjdk-17-jdk | openjdk-18-jdk | openjdk-19-jdk | openjdk-20-jdk"'],
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

        return (None, in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        self.check_data_and_start_download(self.url, checksum)

    def post_install(self):
        """Create the appropriate JetBrains launcher."""
        icon_path = os.path.join(self.install_path, 'bin', self.icon_filename)
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
                         packages_requirements=['python3'],
                         dir_to_decompress_in_tarball='pycharm-community-*',
                         desktop_filename='jetbrains-pycharm-ce.desktop',
                         icon_filename='pycharm.png',
                         version_regex=r'(\d+\.\d+)',
                         **kwargs)

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                version_not_formatted = data.get('dataDirectoryName')
                return re.search(r'\d+\.\d+', version_not_formatted).group() if version_not_formatted else None
        except FileNotFoundError:
            return


class PyCharmEducational(BaseJetBrains):
    """The JetBrains PyCharm Educational Edition distribution."""
    download_keyword = 'PCE'
    executable = "pycharm.sh"

    def __init__(self, **kwargs):
        super().__init__(name="PyCharm Educational",
                         description=_("PyCharm Educational Edition"),
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['python3'],
                         dir_to_decompress_in_tarball='pycharm-edu*',
                         desktop_filename='jetbrains-pycharm-edu.desktop',
                         icon_filename='pycharm.png',
                         version_regex=r'(\d+\.\d+)',
                         **kwargs)


    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                version_not_formatted = data.get('dataDirectoryName')
                return re.search(r'\d+\.\d+', version_not_formatted).group() if version_not_formatted else None
        except FileNotFoundError:
            return


class PyCharmProfessional(BaseJetBrains):
    """The JetBrains PyCharm Professional Edition distribution."""
    download_keyword = 'PCP'
    executable = "pycharm.sh"

    def __init__(self, **kwargs):
        super().__init__(name="PyCharm Professional",
                         description=_("PyCharm Professional Edition"),
                         only_on_archs=['i386', 'amd64'],
                         packages_requirements=['python3'],
                         dir_to_decompress_in_tarball='pycharm-*',
                         desktop_filename='jetbrains-pycharm.desktop',
                         icon_filename='pycharm.png',
                         version_regex=r'(\d+\.\d+)',
                         **kwargs)


    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                version_not_formatted = data.get('dataDirectoryName')
                return re.search(r'\d+\.\d+', version_not_formatted).group() if version_not_formatted else None
        except FileNotFoundError:
            return


class Idea(BaseJetBrains):
    """The JetBrains IntelliJ Idea Community Edition distribution."""
    download_keyword = 'IIC'
    executable = "idea.sh"

    def __init__(self, **kwargs):
        super().__init__(name="Idea",
                         description=_("IntelliJ IDEA Community Edition"),
                         only_on_archs=['i386', 'amd64'],
                         dir_to_decompress_in_tarball='idea-IC-*',
                         desktop_filename='jetbrains-idea-ce.desktop',
                         icon_filename='idea.png',
                         version_regex=r'(\d+\.\d+)',
                         **kwargs)

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                version_not_formatted = data.get('dataDirectoryName')
                return re.search(r'\d+\.\d+', version_not_formatted).group() if version_not_formatted else None
        except FileNotFoundError:
            return


class IdeaUltimate(BaseJetBrains):
    """The JetBrains IntelliJ Idea Ultimate Edition distribution."""
    download_keyword = 'IIU'
    executable = "idea.sh"

    def __init__(self, **kwargs):
        super().__init__(name="Idea Ultimate",
                         description=_("IntelliJ IDEA"),
                         only_on_archs=['i386', 'amd64'],
                         dir_to_decompress_in_tarball='idea-IU-*',
                         desktop_filename='jetbrains-idea.desktop',
                         icon_filename='idea.png',
                         version_regex=r'(\d+\.\d+)',
                         **kwargs)

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                version_not_formatted = data.get('dataDirectoryName')
                return re.search(r'\d+\.\d+', version_not_formatted).group() if version_not_formatted else None
        except FileNotFoundError:
            return


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
                         version_regex=r'WebStorm-(\d+(\.\d+)+)',
                         **kwargs)

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                return data.get('version')
        except FileNotFoundError:
            return


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
                         version_regex=r'-(\d+\.\d+\.\d+)',
                         **kwargs)

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                return data.get('version')
        except FileNotFoundError:
            return


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
                         version_regex=r'-(\d+\.\d+\.\d+)',
                         **kwargs)

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                return data.get('version')
        except FileNotFoundError:
            return


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
                         version_regex=r'-(\d+\.\d+\.\d+)',
                         **kwargs)

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                return data.get('version')
        except FileNotFoundError:
            return


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
                         version_regex=r'-(\d+\.\d+\.\d+)',
                         **kwargs)

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'product-info.json'), 'r') as file:
                data = json.load(file)
                return data.get('version')
        except FileNotFoundError:
            return


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


class Netbeans(umake.frameworks.baseinstaller.BaseInstaller, metaclass=ABCMeta):

    def __init__(self, **kwargs):
        super().__init__(name=_("Netbeans"),
                         description=_("Extensible Java IDE"),
                         only_on_archs=['i386', 'amd64'],
                         desktop_filename="netbeans.desktop",
                         download_page='https://downloads.apache.org/netbeans/netbeans/?C=M;O=D',
                         dir_to_decompress_in_tarball="netbeans*",
                         packages_requirements=['openjdk-8-jdk | openjdk-11-jdk'],
                         checksum_type=ChecksumType.sha512,
                         required_files_path=["bin/netbeans"],
                         **kwargs)

    def parse_download_link(self, line, in_download):
        """Parse NetBeans download links"""
        if '[DIR]' in line:
            in_download = True
        else:
            in_download = False
        if in_download:
            p = re.search(r'\[DIR\]\"> <a href=\"(\S+)\/\"', line)
            with suppress(AttributeError):
                self.new_download_url = self.download_page.replace('?C=M;O=D',
                                                                   '{}/'.format(p.group(1)) +
                                                                   'netbeans-{}-bin.zip.sha512'.format(p.group(1)))
        return (None, in_download)

    @MainLoop.in_mainloop_thread
    def get_sha_and_start_download(self, download_result):
        res = download_result[self.new_download_url]
        checksum = res.buffer.getvalue().decode('utf-8').split()[0]
        url = self.new_download_url.replace('.sha512', '')
        self.check_data_and_start_download(url, checksum)

    def post_install(self):
        """Create the Apache Netbeans launcher"""
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=self.name,
                                                     icon_path=os.path.join(self.install_path, "nb", "netbeans.png"),
                                                     try_exec=self.exec_path,
                                                     exec=self.exec_link_name,
                                                     comment=self.description,
                                                     categories="Development;IDE;"))


class CodeiumWindsurf(umake.frameworks.baseinstaller.BaseInstaller):
    def __init__(self, **kwargs):
        super().__init__(name="Codeium Windsurf", description=_("Codeium Windsurf focused on modern web and cloud"),
                         only_on_archs=['amd64'],
                         download_page="https://windsurf-stable.codeium.com/api/update/linux-x64/stable/latest",
                         desktop_filename="codeium-windsurf.desktop",
                         required_files_path=["bin/windsurf"],
                         dir_to_decompress_in_tarball="Windsurf",
                         packages_requirements=["libgtk2.0-0"],
                         checksum_type=ChecksumType.sha256,
                         **kwargs)

    def parse_download_link(self, line, in_download):
        data = json.loads(line)

        in_download = True if 'url' in data else in_download

        return (data.get('url'), data.get('sha256hash')), in_download

    def post_install(self):
        """Create the Codeium Windsurf launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Codeium Windsurf"),
                        icon_path=os.path.join(self.install_path, "resources", "app", "resources", "linux",
                                               "code.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("Codeium Windsurf focused on modern web and cloud"),
                        categories="Development;IDE;",
                        extra="StartupWMClass=Windsurf"))


class VisualStudioCode(umake.frameworks.baseinstaller.BaseInstaller):

    PERM_DOWNLOAD_LINKS = {
        "x86_64": "https://go.microsoft.com/fwlink/?LinkID=620884",
        "x86_64-insiders": "https://go.microsoft.com/fwlink/?LinkId=723968",
        "armhf": "https://aka.ms/linux-armhf",
        "armhf-insiders": "https://aka.ms/linux-armhf-insider",
        "arm64": "https://aka.ms/linux-arm64",
        "arm64-insiders": "https://aka.ms/linux-arm64-insider"
    }

    def __init__(self, **kwargs):
        super().__init__(name="Visual Studio Code", description=_("Visual Studio focused on modern web and cloud"),
                         only_on_archs=['i386', 'amd64', 'arm', 'arm64'], expect_license=True,
                         download_page="https://code.visualstudio.com/License",
                         desktop_filename="visual-studio-code.desktop",
                         required_files_path=["bin/code"],
                         dir_to_decompress_in_tarball="VSCode-linux-*",
                         packages_requirements=["libgtk2.0-0"],
                         **kwargs)

    def parse_license(self, line, license_txt, in_license):
        """Parse Visual Studio Code download page for license"""
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
                         json=True,
                         version_regex=r'(\d+\.\d+)',
                         supports_update=True,
                         **kwargs)

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

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'resources', 'app', 'package.json'), 'r') as file:
                data = json.load(file)
                return data.get('version')
        except FileNotFoundError:
            return


class Atom(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Atom", description=_("The hackable text editor (not supported upstream anymore)"),
                         download_page=None, only_on_archs=['amd64'], only_for_removal=True, **kwargs)


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
                         only_on_archs=['amd64', 'aarch64'],
                         download_page="https://www.sublimetext.com/download_thanks",
                         desktop_filename="sublime-text.desktop",
                         required_files_path=["sublime_text"],
                         dir_to_decompress_in_tarball="sublime_text",
                         version_regex=r'_build_(\d+)',
                         supports_update=True,
                         **kwargs)

    arch_trans = {
        "amd64": "x64",
        "aarch64": "arm64"
    }

    def parse_download_link(self, line, in_download):
        """Parse SublimeText download links"""
        url = None
        if '{}.tar.xz'.format(self.arch_trans[get_current_arch()]) in line:
            p = re.search(r'href="([^<]*{}.tar.xz)"'.format(self.arch_trans[get_current_arch()]), line)
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

    @staticmethod
    def get_current_user_version(install_path):
        try:
            command = f"{os.path.join(install_path, 'sublime_text')} --version"
            result = subprocess.check_output(command, shell=True, text=True)
            match = re.search(r'(\d+)', result)
            return match.group(1) if match else None
        except subprocess.CalledProcessError:
            return


class SpringToolsSuite(umake.frameworks.baseinstaller.BaseInstaller):
    def __init__(self, **kwargs):
        super().__init__(name="Spring Tools Suite",
                         description=_("Spring Tools Suite IDE"),
                         download_page="https://spring.io/tools/",
                         dir_to_decompress_in_tarball='sts-*',
                         desktop_filename='STS.desktop',
                         only_on_archs=['amd64'],
                         packages_requirements=['openjdk-11-jdk | openjdk-17-jdk | openjdk-18-jdk | openjdk-19-jdk | openjdk-20-jdk"'],
                         icon_filename='icon.xpm',
                         required_files_path=["SpringToolSuite4"],
                         **kwargs)
        self.new_download_url = None

    arch_trans = {
        "amd64": "x86_64",
        "aarch64": "aarch64"
    }

    def parse_download_link(self, line, in_download):
        """Parse STS download links"""    
        url = None
        if '{}.tar.gz'.format(self.arch_trans[get_current_arch()]) in line:
            p = re.search(r'href="([^<]*{}.tar.gz)"'.format(self.arch_trans[get_current_arch()]), line)
            with suppress(AttributeError):
                url = p.group(1)
        return ((url, None), in_download)

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
                         json=True,
                         version_regex=r'(\d+\.\d+)',
                         supports_update=True,
                         **kwargs)

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

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'revisions.txt'), 'r') as file:
                first_line = file.readline().strip()
                match = re.search(r'(\d+\.\d+\.\d+)', first_line)
                return match.group(1) if match else None
        except FileNotFoundError:
            return


class LiteIDE(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="LiteIDE", description=_("LiteIDE is a simple, open source, cross-platform Go IDE."),
                         only_on_archs=['i386', 'amd64'],
                         download_page="https://api.github.com/repos/visualfc/liteide/releases/latest",
                         packages_requirements=["libqt5core5a"],
                         desktop_filename="liteide.desktop",
                         required_files_path=["bin/liteide"],
                         dir_to_decompress_in_tarball="liteide",
                         json=True,
                         version_regex=r'(\d+\.\d+)',
                         supports_update=True,
                         **kwargs)

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

    @staticmethod
    def get_current_user_version(install_path):
        try:
            with open(os.path.join(install_path, 'README.md'), 'r') as file:
                content = ''.join(file.readline() for _ in range(15))
                match = re.search(r'(\d+\.\d+)', content)
                return match.group(1) if match else None
        except FileNotFoundError:
            return


class RStudio(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="RStudio", description=_("RStudio code editor"),
                         only_on_archs=['amd64'],
                         download_page="https://posit.co/download/rstudio-desktop/",
                         packages_requirements=["libjpeg62", "libedit2", "libssl1.1 | libssl3",
                                                "libclang-dev", "libpq5", "r-base"],
                         desktop_filename="rstudio.desktop",
                         required_files_path=["bin/rstudio"],
                         dir_to_decompress_in_tarball="rstudio-*",
                         **kwargs)

    def parse_download_link(self, line, in_download):
        """Parse RStudio download links"""
        url = None
        checksum = None
        if int(get_current_distro_version(distro_name="debian").split('.')[0]) == 9 or\
            int(get_current_distro_version().split('.')[0]) == 20:
            ubuntu_version = "focal"
        else:
            ubuntu_version = 'jammy'
        if '-debian.tar.gz' in line:
            p = re.search(r'href=\"([^<]*{}.*-debian\.tar\.gz)\"'.format(ubuntu_version), line)
            with suppress(AttributeError):
                url = p.group(1)
        return ((url, checksum), in_download)

    def post_install(self):
        """Create the RStudio launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("RStudio"),
                        icon_path=os.path.join(self.install_path, "rstudio.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=_("RStudio makes R easier to use."
                                  "It includes a code editor, debugging & visualization tools."),
                        categories="Development;IDE;"))


class VSCodium(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="VSCodium", description=_("Free/Libre Open Source Software Binaries of VSCode"),
                         download_page="https://api.github.com/repos/VSCodium/VSCodium/releases/latest",
                         desktop_filename="vscodium.desktop",
                         only_on_archs=["amd64"],  # TODO: add arm builds
                         required_files_path=["bin/codium"],
                         dir_to_decompress_in_tarball=".",
                         packages_requirements=["libgtk2.0-0", "libgconf-2-4"],
                         json=True, **kwargs)

    arch_trans = {
        "amd64": "x64"
    }

    def parse_download_link(self, line, in_download):
        url = None
        for asset in line["assets"]:
            if "linux-{}".format(self.arch_trans[get_current_arch()]) in asset["browser_download_url"]\
               and asset["browser_download_url"].endswith(".tar.gz"):
                in_download = True
                url = asset["browser_download_url"]
        return (url, in_download)

    def post_install(self):
        """Create the VSCodium Code launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("VSCodium"),
                        icon_path=os.path.join(self.install_path, "resources/app/resources/linux/code.png"),
                        try_exec=self.exec_path,
                        exec=self.exec_link_name,
                        comment=self.description,
                        categories="Development;IDE;"))
