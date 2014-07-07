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


"""Android module"""

from contextlib import suppress
from gettext import gettext as _
from io import StringIO
import logging
from progressbar import ProgressBar
import os
import re
import shutil
from textwrap import dedent
import udtc.frameworks
from udtc.decompressor import Decompressor
from udtc.interactions import InputText, YesNo, LicenseAgreement, DisplayMessage, UnknownProgress
from udtc.network.download_center import DownloadCenter
from udtc.network.requirements_handler import RequirementsHandler
from udtc.ui import UI
from udtc.tools import MainLoop, strip_tags, create_launcher, get_application_desktop_file

logger = logging.getLogger(__name__)

_supported_archs = ['i386', 'amd64']


class AndroidCategory(udtc.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name=_("Android"), description=_("Android Developement Environment"),
                         logo_path=None,
                         packages_requirements=["openjdk-7-jdk", "libncurses5:i386", "libstdc++6:i386", "zlib1g:i386"])


class EclipseAdt(udtc.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="ADT", description="Android Developer Tools (using eclipse)",
                         category=category, install_path_dir="android/adt-eclipse",
                         only_on_archs=_supported_archs)
        self.ADT_DOWNLOAD_PAGE = "https://developer.android.com/sdk/index.html"

    def setup(self, install_path=None):
        print("Installing…")
        super().setup()


class AndroidStudio(udtc.frameworks.BaseFramework):

    def __init__(self, category):
        super().__init__(name="Android Studio", description="Android Studio (default)", is_category_default=True,
                         category=category, only_on_archs=_supported_archs)
        self._install_done = False
        self._reinstall = False
        self._arg_install_path = None
        self.STUDIO_DOWNLOAD_PAGE = "http://developer.android.com/sdk/installing/studio.html"

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if not os.path.join(self.install_path, "bin", "studio.sh"):
            logger.debug("{} binary isn't installed".format(self.name))
            return False
        # check pre-requisites

    def setup(self, arg_install_path=None):
        self.arg_install_path = arg_install_path
        super().setup(arg_install_path)

        # first step, check if installed
        if self.is_installed:
            UI.display(YesNo("Android Studio is already installed on your system, do you want to reinstall "
                             "it anyway?", self.reinstall, UI.return_main_screen))
        else:
            self.confirm_path(arg_install_path)

    def reinstall(self):
        self._reinstall = True
        self.confirm_path(self.arg_install_path)

    def confirm_path(self, path_dir=""):
        """Confirm path dir"""

        if not path_dir:
            logger.debug("No installation path provided. Requesting one.")
            UI.display(InputText("Choose installation path:", self.confirm_path, self.install_path))
            return

        logger.debug("Installation path provided. Checking if exists.")
        with suppress(FileNotFoundError):
            if os.listdir(path_dir):
                if self._reinstall:
                    self.set_dir_to_clean()
                else:
                    if path_dir == "/":
                        logger.error("This doesn't seem wise. We won't let you shoot in your feet.")
                        self.confirm_path()
                        return
                    UI.display(YesNo("{} isn't an empty directory, do you want to remove its content and install "
                                     "there?".format(path_dir), self.set_dir_to_clean, UI.return_main_screen))
                self.install_path = path_dir
                return
        self.install_path = path_dir
        self.download_provider_page()

    def set_dir_to_clean(self):
        logger.debug("Mark existing installation path for cleaning.")
        self._reinstall = True
        self.download_provider_page()

    def download_provider_page(self):
        # Mark nown known install place for later eventual reinstallation
        self.mark_in_config()

        logger.debug("Download android app provider page")
        DownloadCenter([(self.STUDIO_DOWNLOAD_PAGE, None)], self.get_metadata_and_check_license, download=False)

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Download files to download + license and check it"""
        logger.debug("Parse download metadata")

        error_msg = result[self.STUDIO_DOWNLOAD_PAGE].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.STUDIO_DOWNLOAD_PAGE, error_msg))
            UI.return_main_screen()

        self.to_download = {}
        with StringIO() as license_txt:
            in_license = False
            in_download = False
            for line in result[self.STUDIO_DOWNLOAD_PAGE].buffer:
                line_content = line.decode()

                # license part
                if line_content.startswith('<p class="sdk-terms-intro">'):
                    in_license = True
                if in_license:
                    if line_content.startswith('</div>'):
                        in_license = False
                    else:
                        license_txt.write(line_content)

                # download part
                if 'id="linux-studio"' in line_content:
                    in_download = True
                if in_download:
                    p = re.search(r'href="(.*)">', line_content)
                    with suppress(AttributeError):
                        self.to_download['url'] = p.group(1)
                    p = re.search(r'<td>(\w+)</td>', line_content)
                    with suppress(AttributeError):
                        self.to_download['md5sum'] = p.group(1)
                    if "</tr>" in line_content:
                        in_download = False

            if not "url" in self.to_download or not "md5sum" in self.to_download:
                logger.error("Couldn't find any download page")
                UI.return_main_screen()

            logger.debug("Check license agreement.")
            UI.display(LicenseAgreement(strip_tags(license_txt.getvalue()).strip(),
                                        self.start_download_and_install,
                                        UI.return_main_screen))
        return

    def start_download_and_install(self):
        self.last_progress_download = 0
        self.last_progress_requirement = 0
        self.balance_requirement_download = None
        self.result_requirement = None
        self.result_download = None
        UI.display(DisplayMessage("Downloading and installing requirements"))
        self.pbar = ProgressBar().start()
        self.pkg_num_install, self.pkg_size_download =\
            RequirementsHandler().install_bucket(self.packages_requirements, self.get_progress_requirement,
                                                 self.requirement_done)
        DownloadCenter(urls=[(self.to_download['url'], self.to_download['md5sum'])], on_done=self.check_download,
                       report=self.get_progress_download)

    @MainLoop.in_mainloop_thread
    def get_progress(self, progress_download, progress_requirement):
        """Global progress info. Don't use named parameters as idle_add doesn't like it"""

        if progress_download is not None:
            self.last_progress_download = progress_download
        if progress_requirement is not None:
            self.last_progress_requirement = progress_requirement

        # we wait to have the file size to start getting progress proportion info
        if self.balance_requirement_download is None:
            return

        progress = self.balance_requirement_download * self.last_progress_requirement +\
            (1 - self.balance_requirement_download) * self.last_progress_download
        self.pbar.update(progress)
        #print("global progress: {}".format(progress))
        return

    def get_progress_requirement(self, step, percentage):
        """Chain up to main get_progress, returning current value between 0 and 100"""
        # only unpacking
        if self.pkg_size_download == 0:
            progress = percentage
        else:
            # 60% is download, 40% is installing
            if step == RequirementsHandler.STATUS_DOWNLOADING:
                progress = 0.6 * percentage
            else:
                progress = 60 + 0.4 * percentage
        self.get_progress(None, progress)

    def get_progress_download(self, downloads):
        """Chain up to main get_progress, returning current value between 0 and 100

        First call initialize the balance between requirements and download progress"""
        total_size = 0
        total_current_size = 0
        for download in downloads:
            total_size += downloads[download]["size"]
            total_current_size += downloads[download]["current"]

        if self.balance_requirement_download is None:
            if self.pkg_num_install == 0:
                self.balance_requirement_download = 0
            else:
                # apply a minimum of 15% (no download or small download + install time)
                self.balance_requirement_download = max(self.pkg_size_download / (self.pkg_size_download + total_size),
                                                        0.15)
        self.get_progress(total_current_size / total_size * 100, None)

    def requirement_done(self, result):
        self.get_progress(None, 100)
        self.result_requirement = result
        self.download_and_requirements_done()

    def check_download(self, result):
        self.get_progress(100, None)
        self.result_download = result
        self.download_and_requirements_done()

    @MainLoop.in_mainloop_thread
    def download_and_requirements_done(self):
        # wait for both side to be done
        if not self.result_download or not self.result_requirement:
            return

        self.pbar.finish()
        # display eventual errors
        error_detected = False
        fd = None
        if self.result_requirement.error:
            logger.error(self.result_requirement.error)
            error_detected = True
        for url in self.result_download:
            if self.result_download[url].error:
                logger.error(self.result_download[url].error)
                error_detected = True
            fd = self.result_download[url].fd
        if error_detected:
            UI.return_main_screen()
            return

        self.decompress_and_install(fd)

    def decompress_and_install(self, fd):
        UI.display(DisplayMessage("Installing Android Studio"))
        # empty destination directory if reinstall
        if self._reinstall:
            with suppress(FileNotFoundError):
                shutil.rmtree(self.install_path)

        Decompressor({fd: Decompressor.DecompressOrder(dir="android-studio", dest=self.install_path)},
                     self.decompress_and_install_done)
        UI.display(UnknownProgress(self.iterate_until_install_done))

    def decompress_and_install_done(self, result):
        self._install_done = True
        error_detected = False
        for fd in result:
            if result[fd].error:
                logger.error(result[fd].error)
                error_detected = True
        if error_detected:
            UI.return_main_screen()
            return

        # install desktop file
        create_launcher("android-studio.desktop", get_application_desktop_file(name=_("Android Studio"),
                        icon_path=os.path.join(self.install_path, "bin", "idea.png"),
                        exec='"{}" %f'.format(os.path.join(self.install_path, "bin", "studio.sh")),
                        comment=_("Android Studio developer environment"),
                        categories="Development;IDE;",
                        extra="StartupWMClass=jetbrains-android-studio"))
        UI.delayed_display(DisplayMessage("Installation done"))
        UI.return_main_screen()

    def iterate_until_install_done(self):
        while not self._install_done:
            yield
