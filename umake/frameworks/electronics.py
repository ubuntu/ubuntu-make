# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 Canonical
#
# Authors:
#  Didier Roche
#  Galileo Sartor
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


"""Generic Electronics module."""
from contextlib import suppress
from gettext import gettext as _
import logging
import grp
import os
import platform
import pwd
import re
import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.tools import add_env_to_user, MainLoop, ChecksumType, Checksum,\
    create_launcher, get_application_desktop_file
from umake.ui import UI

logger = logging.getLogger(__name__)


class ElectronicsCategory(umake.frameworks.BaseCategory):
    def __init__(self):
        super().__init__(name="Electronics", description=_("Electronics software"),
                         logo_path=None)


class Arduino(umake.frameworks.baseinstaller.BaseInstaller):
    """The Arduino Software distribution."""

    ARDUINO_GROUP = "dialout"

    def __init__(self, **kwargs):

        if os.geteuid() != 0:
            self._current_user = os.getenv("USER")
        self._current_user = pwd.getpwuid(int(os.getenv("SUDO_UID", default=0))).pw_name
        for group_name in [g.gr_name for g in grp.getgrall() if self._current_user in g.gr_mem]:
            if group_name == self.ARDUINO_GROUP:
                self.was_in_arduino_group = True
                break
        else:
            self.was_in_arduino_group = False

        super().__init__(name="Arduino",
                         description=_("The Arduino Software Distribution"),
                         only_on_archs=['i386', 'amd64'],
                         download_page='http://www.arduino.cc/en/Main/Software',
                         dir_to_decompress_in_tarball='arduino-*',
                         desktop_filename='arduino.desktop',
                         packages_requirements=['gcc-avr', 'avr-libc'],
                         need_root_access=not self.was_in_arduino_group,
                         required_files_path=["arduino"], **kwargs)
        self.scraped_checksum_url = None
        self.scraped_download_url = None

        # This is needed later in several places.
        # The framework covers other cases, in combination with self.only_on_archs
        self.bits = '32' if platform.machine() == 'i686' else '64'

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """We diverge from the BaseInstaller implementation a little here."""
        logger.debug("Parse download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        soup = BeautifulSoup(result[self.download_page].buffer, 'html.parser')

        # We need to avoid matching arduino-nightly-...
        download_link_pat = r'arduino-[\d\.\-r]+-linux' + self.bits + '.tar.xz$'

        # Trap no match found, then, download/checksum url will be empty and will raise the error
        # instead of crashing.
        with suppress(TypeError):
            self.scraped_download_url = soup.find('a', href=re.compile(download_link_pat))['href']
            self.scraped_checksum_url = soup.find('a', text=re.compile('Checksums'))['href']

            self.scraped_download_url = 'http:' + self.scraped_download_url
            self.scraped_checksum_url = 'http:' + self.scraped_checksum_url

        if not self.scraped_download_url:
            logger.error("Can't parse the download link from %s.", self.download_page)
            UI.return_main_screen(status_code=1)
        if not self.scraped_checksum_url:
            logger.error("Can't parse the checksum link from %s.", self.download_page)
            UI.return_main_screen(status_code=1)

        DownloadCenter([DownloadItem(self.scraped_download_url), DownloadItem(self.scraped_checksum_url)],
                       on_done=self.prepare_to_download_archive, download=False)

    @MainLoop.in_mainloop_thread
    def prepare_to_download_archive(self, results):
        """Store the md5 for later and fire off the actual download."""
        download_page = results[self.scraped_download_url]
        checksum_page = results[self.scraped_checksum_url]
        if download_page.error:
            logger.error("Error fetching download page: %s", download_page.error)
            UI.return_main_screen(status_code=1)
        if checksum_page.error:
            logger.error("Error fetching checksums: %s", checksum_page.error)
            UI.return_main_screen(status_code=1)

        match = re.search(r'^(\S+)\s+arduino-[\d\.\-r]+-linux' + self.bits + '.tar.xz$',
                          checksum_page.buffer.getvalue().decode('ascii'),
                          re.M)
        if not match:
            logger.error("Can't find a checksum.")
            UI.return_main_screen(status_code=1)
        checksum = match.group(1)

        soup = BeautifulSoup(download_page.buffer.getvalue(), 'html.parser')
        btn = soup.find('button', text=re.compile('JUST DOWNLOAD'))

        if not btn:
            logger.error("Can't parse download button.")
            UI.return_main_screen(status_code=1)

        base_url = download_page.final_url
        cookies = download_page.cookies

        final_download_url = parse.urljoin(base_url, btn.parent['href'])

        logger.info('Final download url: %s, cookies: %s.', final_download_url, cookies)

        self.download_requests = [DownloadItem(final_download_url,
                                               checksum=Checksum(ChecksumType.md5, checksum),
                                               cookies=cookies)]

        # add the user to arduino group
        if not self.was_in_arduino_group:
            with futures.ProcessPoolExecutor(max_workers=1) as executor:
                f = executor.submit(_add_to_group, self._current_user, self.ARDUINO_GROUP)
                if not f.result():
                    UI.return_main_screen(status_code=1)

        self.start_download_and_install()

    def post_install(self):
        """Create the Arduino launcher"""
        icon_path = join(self.install_path, 'lib', 'arduino_icon.ico')
        comment = _("The Arduino Software IDE")
        categories = "Development;IDE;"
        create_launcher(self.desktop_filename,
                        get_application_desktop_file(name=_("Arduino"),
                                                     icon_path=icon_path,
                                                     exec='"{}" %f'.format(self.exec_path),
                                                     comment=comment,
                                                     categories=categories))
        if not self.was_in_arduino_group:
            UI.delayed_display(DisplayMessage(_("You need to logout and login again for your installation to work")))


class Eagle(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, **kwargs):
        super().__init__(name="Eagle", description=_("PCB design software for students, makers, and professionals"),
                         only_on_archs=['amd64'],
                         download_page="https://eagle-updates.circuits.io/downloads/latest.html",
                         desktop_filename="eagle.desktop",
                         required_files_path=["eagle"],
                         dir_to_decompress_in_tarball="eagle-*",
                         **kwargs)

    def parse_download_link(self, line, in_download):
        """Parse Eagle download links"""
        url = None
        if '.tar.gz' in line:
            p = re.search(r'href="([^<]*.tar.gz)"', line)
            with suppress(AttributeError):
                url = p.group(1)
        return ((url, None), in_download)

    def post_install(self):
        """Create the Eagle launcher"""
        create_launcher(self.desktop_filename, get_application_desktop_file(name=_("Eagle"),
                        icon_path=os.path.join(self.install_path, "bin", "eagleicon50.png"),
                        exec=self.exec_path,
                        comment=self.description,
                        categories="Development;"))
