# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
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

from gettext import gettext as _
import logging
import platform
from bs4 import BeautifulSoup
from abc import ABCMeta, abstractmethod

from os.path import join, isfile
import umake.frameworks.baseinstaller
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.tools import create_launcher, get_application_desktop_file, ChecksumType, Checksum, MainLoop
from umake.ui import UI


logger = logging.getLogger(__name__)


class IdeCategory(umake.frameworks.BaseCategory):
    def __init__(self):
        super().__init__(name="IDE", description=_("Generic IDEs"),
                         logo_path=None)


class Eclipse(umake.frameworks.baseinstaller.BaseInstaller):
    """The Eclipse Foundation distribution."""
    DOWNLOAD_URL_PAT = "https://www.eclipse.org/downloads/download.php?" \
                       "file=/technology/epp/downloads/release/luna/R/" \
                       "eclipse-standard-luna-R-linux-gtk{arch}.tar.gz{suf}" \
                       "&r=1"

    def __init__(self, category):
        super().__init__(name="Eclipse",
                         description=_("Pure Eclipse Luna (4.4)"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page=None,
                         dir_to_decompress_in_tarball='eclipse',
                         desktop_filename='eclipse.desktop',
                         packages_requirements=['openjdk-7-jdk'])

    def download_provider_page(self):
        """First, we need to fetch the MD5, then kick off the proceedings.

        This could actually be done in parallel, in a future version.
        """
        logger.debug("Preparing to download MD5.")

        arch = platform.machine()
        if arch == 'i686':
            md5_url = self.DOWNLOAD_URL_PAT.format(arch='', suf='.md5')
        elif arch == 'x86_64':
            md5_url = self.DOWNLOAD_URL_PAT.format(arch='-x86_64', suf='.md5')
        else:
            logger.error("Unsupported architecture: {}".format(arch))
            UI.return_main_screen()

        def done(download_result):
            res = download_result[md5_url]

            if res.error:
                logger.error(res.error)
                UI.return_main_screen()
                return

            # Should be ASCII anyway.
            md5 = res.buffer.getvalue().decode('utf-8').split()[0]
            logger.debug("Downloaded MD5 is {}".format(md5))

            logger.debug("Preparing to download the main archive.")
            if arch == 'i686':
                download_url = self.DOWNLOAD_URL_PAT.format(arch='', suf='')
            elif arch == 'x86_64':
                download_url = self.DOWNLOAD_URL_PAT.format(arch='-x86_64',
                                                            suf='')
            self.download_requests.append(DownloadItem(download_url, Checksum(ChecksumType.md5, md5)))
            self.start_download_and_install()

        DownloadCenter(urls=[DownloadItem(md5_url, None)], on_done=done, download=False)

    def post_install(self):
        """Create the Luna launcher"""
        icon_filename = "icon.xpm"
        icon_path = join(self.install_path, icon_filename)
        exec_path = '"{}" %f'.format(join(self.install_path, "eclipse"))
        comment = _("The Eclipse Luna Integrated Development Environment")
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=_("Eclipse Luna"),
                                                     icon_path=icon_path,
                                                     exec=exec_path,
                                                     comment=comment,
                                                     categories=categories))

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not isfile(join(self.install_path, "eclipse")):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True


class BaseJetBrains(umake.frameworks.baseinstaller.BaseInstaller, metaclass=ABCMeta):
    """The base for all JetBrains installers."""

    @property
    @abstractmethod
    def download_page_url(self):
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
            logger.error("An error occurred while downloading {}: {}".format(self.download_page_url, error_msg))
            UI.return_main_screen()

        soup = BeautifulSoup(page.buffer)
        link = soup.find('a', text="HTTPS")
        if link is None:
            logger.error("Can't parse the download URL from the download page.")
            UI.return_main_screen()
        download_url = link.attrs['href']
        checksum_url = download_url + '.sha256'
        logger.debug("Found download URL: " + download_url)
        logger.debug("Downloading checksum first, from " + checksum_url)

        def checksum_downloaded(results):
            checksum_result = next(iter(results.values()))  # Just get the first.
            if checksum_result.error:
                logger.error(checksum_result.error)
                UI.return_main_screen()
                return

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
        exec_path = '"{}" %f'.format(join(self.install_path, "bin", self.executable))
        comment = self.description + " (UDTC)"
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=self.description,
                                                     icon_path=icon_path,
                                                     exec=exec_path,
                                                     comment=comment,
                                                     categories=categories))

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not isfile(join(self.install_path, "bin", self.executable)):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        return True


class PyCharm(BaseJetBrains):
    """The JetBrains PyCharm Community Edition distribution."""
    download_page_url = "https://www.jetbrains.com/pycharm/download/download_thanks.jsp?edition=comm&os=linux"
    executable = "pycharm.sh"

    def __init__(self, category):
        super().__init__(name="PyCharm",
                         description=_("PyCharm Community Edition"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page=self.download_page_url,
                         dir_to_decompress_in_tarball='pycharm-community-*',
                         desktop_filename='jetbrains-pycharm.desktop',
                         packages_requirements=['openjdk-7-jdk', 'jayatana'],
                         icon_filename='pycharm.png')


class PyCharmEducational(BaseJetBrains):
    """The JetBrains PyCharm Educational Edition distribution."""
    download_page_url = "https://www.jetbrains.com/pycharm-educational/download/download_thanks.jsp?os=linux"
    executable = "pycharm.sh"

    def __init__(self, category):
        super().__init__(name="PyCharm Educational",
                         description=_("PyCharm Educational Edition"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page=self.download_page_url,
                         dir_to_decompress_in_tarball='pycharm-edu*',
                         desktop_filename='jetbrains-pycharm.desktop',
                         packages_requirements=['openjdk-7-jdk', 'jayatana'],
                         icon_filename='pycharm.png')


class PyCharmProfessional(BaseJetBrains):
    """The JetBrains PyCharm Professional Edition distribution."""
    download_page_url = "https://www.jetbrains.com/pycharm/download/download_thanks.jsp?os=linux"
    executable = "pycharm.sh"

    def __init__(self, category):
        super().__init__(name="PyCharm Professional",
                         description=_("PyCharm Professional Edition"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page=self.download_page_url,
                         dir_to_decompress_in_tarball='pycharm-*',
                         desktop_filename='jetbrains-pycharm.desktop',
                         packages_requirements=['openjdk-7-jdk', 'jayatana'],
                         icon_filename='pycharm.png')


class Idea(BaseJetBrains):
    """The JetBrains IntelliJ Idea Community Edition distribution."""
    download_page_url = "https://www.jetbrains.com/idea/download/download_thanks.jsp?edition=IC&os=linux"
    executable = "idea.sh"

    def __init__(self, category):
        super().__init__(name="Idea",
                         description=_("IntelliJ IDEA Community Edition"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page=self.download_page_url,
                         dir_to_decompress_in_tarball='idea-IC-*',
                         desktop_filename='jetbrains-idea.desktop',
                         packages_requirements=['openjdk-7-jdk', 'jayatana'],
                         icon_filename='idea.png')


class IdeaUltimate(BaseJetBrains):
    """The JetBrains IntelliJ Idea Ultimate Edition distribution."""
    download_page_url = "https://www.jetbrains.com/idea/download/download_thanks.jsp?edition=IU&os=linux"
    executable = "idea.sh"

    def __init__(self, category):
        super().__init__(name="Idea Ultimate",
                         description=_("IntelliJ IDEA"),
                         category=category, only_on_archs=['i386', 'amd64'],
                         download_page=self.download_page_url,
                         dir_to_decompress_in_tarball='idea-IU-*',
                         desktop_filename='jetbrains-idea.desktop',
                         packages_requirements=['openjdk-7-jdk', 'jayatana'],
                         icon_filename='idea.png')


class RubyMine(BaseJetBrains):
    """The JetBrains RubyMine IDE"""
    download_page_url = "https://www.jetbrains.com/ruby/download/download_thanks.jsp?os=linux"
    executable = "rubymine.sh"

    def __init__(self, category):
        super().__init__(name="RubyMine",
                         description=_("Ruby on Rails IDE"),
                         category=category,
                         only_on_archs=['i386', 'amd64'],
                         download_page=self.download_page_url,
                         dir_to_decompress_in_tarball='RubyMine-*',
                         desktop_filename='jetbrains-rubymine.desktop',
                         packages_requirements=['openjdk-7-jdk', 'jayatana'],
                         icon_filename='rubymine.png')


class WebStorm(BaseJetBrains):
    """The JetBrains WebStorm IDE"""
    download_page_url = "https://www.jetbrains.com/webstorm/download/download_thanks.jsp?os=linux"
    executable = "webstorm.sh"

    def __init__(self, category):
        super().__init__(name="WebStorm",
                         description=_("WebStorm"),
                         category=category,
                         only_on_archs=['i386', 'amd64'],
                         download_page=self.download_page_url,
                         dir_to_decompress_in_tarball='WebStorm-*',
                         desktop_filename='jetbrains-webstorm.desktop',
                         packages_requirements=['openjdk-7-jdk', 'jayatana'],
                         icon_filename='webide.png')


class PhpStorm(BaseJetBrains):
    """The JetBrains PhpStorm IDE"""
    download_page_url = "https://www.jetbrains.com/phpstorm/download/download_thanks.jsp?os=linux"
    executable = "phpstorm.sh"

    def __init__(self, category):
        super().__init__(name="PhpStorm",
                         description=_("PhpStorm"),
                         category=category,
                         only_on_archs=['i386', 'amd64'],
                         download_page=self.download_page_url,
                         dir_to_decompress_in_tarball='PhpStorm-*',
                         desktop_filename='jetbrains-phpstorm.desktop',
                         packages_requirements=['openjdk-7-jdk', 'jayatana'],
                         icon_filename='webide.png')
