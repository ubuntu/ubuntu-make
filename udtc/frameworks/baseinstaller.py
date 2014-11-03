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


"""Downloader abstract module"""

from contextlib import suppress
from io import StringIO
import logging
from progressbar import ProgressBar
import os
import shutil
import udtc.frameworks
from udtc.decompressor import Decompressor
from udtc.interactions import InputText, YesNo, LicenseAgreement, DisplayMessage, UnknownProgress
from udtc.network.download_center import DownloadCenter, DownloadItem
from udtc.network.requirements_handler import RequirementsHandler
from udtc.ui import UI
from udtc.tools import MainLoop, strip_tags, launcher_exists, get_icon_path, get_launcher_path, \
    Checksum, remove_framework_envs_from_user

logger = logging.getLogger(__name__)


class BaseInstaller(udtc.frameworks.BaseFramework):

    def __new__(cls, *args, **kwargs):
        "This class is not meant to be instantiated, so __new__ returns None."
        if cls == BaseInstaller:
            return None
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        """The Downloader framework isn't instantiated directly, but is useful to inherit from for all frameworks

        having a set of downloads to proceed, some eventual supported_archs."""
        self.expect_license = kwargs.get("expect_license", False)
        self.download_page = kwargs["download_page"]
        self.checksum_type = kwargs.get("checksum_type", None)
        self.dir_to_decompress_in_tarball = kwargs.get("dir_to_decompress_in_tarball", None)
        self.desktop_filename = kwargs.get("desktop_filename", None)
        self.icon_filename = kwargs.get("icon_filename", None)
        for extra_arg in ["expect_license", "download_page", "checksum_type",  "dir_to_decompress_in_tarball",
                          "desktop_filename", "icon_filename"]:
            with suppress(KeyError):
                kwargs.pop(extra_arg)
        super().__init__(*args, **kwargs)

        self._install_done = False
        self._paths_to_clean = set()
        self._arg_install_path = None
        self.download_requests = []

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        if self.desktop_filename:
            return launcher_exists(self.desktop_filename)
        return True

    def setup(self, arg_install_path=None):
        self.arg_install_path = arg_install_path
        super().setup()

        # first step, check if installed
        if self.is_installed:
            UI.display(YesNo("{} is already installed on your system, do you want to reinstall "
                             "it anyway?".format(self.name), self.reinstall, UI.return_main_screen))
        else:
            self.confirm_path(arg_install_path)

    def reinstall(self):
        logger.debug("Mark previous installation path for cleaning.")
        self._paths_to_clean.add(self.install_path)  # remove previous installation path
        self.confirm_path(self.arg_install_path)
        remove_framework_envs_from_user(self.name)

    def remove(self):
        """Remove current framework if installed

        Not that we only remove desktop file, launcher icon and dir content, we do not remove
        packages as they might be in used for other framework"""
        # check if it's installed and so on.
        super().remove()

        UI.display(DisplayMessage("Removing {}".format(self.name)))
        if self.desktop_filename:
            with suppress(FileNotFoundError):
                os.remove(get_launcher_path(self.desktop_filename))
        if self.icon_filename:
            with suppress(FileNotFoundError):
                os.remove(get_icon_path(self.icon_filename))
        with suppress(FileNotFoundError):
            shutil.rmtree(self.install_path)
        remove_framework_envs_from_user(self.name)
        self.remove_from_config()

        UI.delayed_display(DisplayMessage("Suppression done"))
        UI.return_main_screen()

    def confirm_path(self, path_dir=""):
        """Confirm path dir"""

        if not path_dir:
            logger.debug("No installation path provided. Requesting one.")
            UI.display(InputText("Choose installation path:", self.confirm_path, self.install_path))
            return

        logger.debug("Installation path provided. Checking if exists.")
        with suppress(FileNotFoundError):
            if os.listdir(path_dir):
                # we already told we were ok to overwrite as it was the previous install path
                if path_dir not in self._paths_to_clean:
                    if path_dir == "/":
                        logger.error("This doesn't seem wise. We won't let you shoot in your feet.")
                        self.confirm_path()
                        return
                    self.install_path = path_dir  # we don't set it before to not repropose / as installation path
                    UI.display(YesNo("{} isn't an empty directory, do you want to remove its content and install "
                                     "there?".format(path_dir), self.set_installdir_to_clean, UI.return_main_screen))
                    return
        self.install_path = path_dir
        self.download_provider_page()

    def set_installdir_to_clean(self):
        logger.debug("Mark non empty new installation path for cleaning.")
        self._paths_to_clean.add(self.install_path)
        self.download_provider_page()

    def download_provider_page(self):
        logger.debug("Download application provider page")
        DownloadCenter([DownloadItem(self.download_page, None)], self.get_metadata_and_check_license, download=False)

    def parse_license(self, line, license_txt, in_license):
        """Parse license per line, eventually write to license_txt if it's in the license part.

        A flag in_license that is returned by the same function helps to decide if we are in the license part"""
        pass

    def parse_download_link(self, line, in_download):
        """Parse download_link per line. in_download is a helper that the function return to know if it's in the
        download part.

        return a tuple of (None, in_download=True/False) if no parsable is found or
                          ((url, md5sum), in_download=True/False)"""
        pass

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Download files to download + license and check it"""
        logger.debug("Parse download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen()

        url, checksum = (None, None)
        with StringIO() as license_txt:
            in_license = False
            in_download = False
            for line in result[self.download_page].buffer:
                line_content = line.decode()

                if self.expect_license:
                    in_license = self.parse_license(line_content, license_txt, in_license)

                (download, in_download) = self.parse_download_link(line_content, in_download)
                if download is not None:
                    (newurl, new_checksum) = download
                    url = newurl if newurl is not None else url
                    checksum = new_checksum if new_checksum is not None else checksum
                    logger.debug("Found download link for {}, checksum: {}".format(url, checksum))
                    if url is not None:
                        if self.checksum_type and checksum:
                            logger.debug("Found download link for {}, checksum: {}".format(url, checksum))
                            break
                        elif not self.checksum_type:
                            logger.debug("Found download link for {}".format(url))
                            break

            if url is None or (self.checksum_type and checksum is None):
                logger.error("Download page changed its syntax or is not parsable")
                UI.return_main_screen()
            self.download_requests.append(DownloadItem(url, Checksum(self.checksum_type, checksum)))

            if license_txt.getvalue() != "":
                logger.debug("Check license agreement.")
                UI.display(LicenseAgreement(strip_tags(license_txt.getvalue()).strip(),
                                            self.start_download_and_install,
                                            UI.return_main_screen))
            elif self.expect_license:
                logger.error("We were expecting to find a license on the download page, we didn't.")
                UI.return_main_screen()
            else:
                self.start_download_and_install()
        return

    def start_download_and_install(self):
        self.last_progress_download = None
        self.last_progress_requirement = None
        self.balance_requirement_download = None
        self.pkg_size_download = 0
        self.result_requirement = None
        self.result_download = None
        self._download_done_callback_called = False
        UI.display(DisplayMessage("Downloading and installing requirements"))
        self.pbar = ProgressBar().start()
        self.pkg_to_install = RequirementsHandler().install_bucket(self.packages_requirements,
                                                                   self.get_progress_requirement,
                                                                   self.requirement_done)
        DownloadCenter(urls=self.download_requests, on_done=self.download_done, report=self.get_progress_download)

    @MainLoop.in_mainloop_thread
    def get_progress(self, progress_download, progress_requirement):
        """Global progress info. Don't use named parameters as idle_add doesn't like it"""

        if progress_download is not None:
            self.last_progress_download = progress_download
        if progress_requirement is not None:
            self.last_progress_requirement = progress_requirement

        # we wait to have the file size to start getting progress proportion info

        # try to compute balance requirement
        if self.balance_requirement_download is None:
            if not self.pkg_to_install:
                self.balance_requirement_download = 0
                self.last_progress_requirement = 0
                if self.last_progress_download is None:
                    return
            else:
                # we only update if we got a progress from both sides
                if self.last_progress_download is None or self.last_progress_requirement is None:
                    return
                else:
                    # apply a minimum of 15% (no download or small download + install time)
                    self.balance_requirement_download = max(self.pkg_size_download /
                                                            (self.pkg_size_download + self.total_download_size),
                                                            0.15)

        progress = self.balance_requirement_download * self.last_progress_requirement +\
            (1 - self.balance_requirement_download) * self.last_progress_download
        if not self.pbar.finished:  # drawing is delayed, so ensure we are not done first
            self.pbar.update(progress)

    def get_progress_requirement(self, status):
        """Chain up to main get_progress, returning current value between 0 and 100"""

        percentage = status["percentage"]
        # 60% is download, 40% is installing
        if status["step"] == RequirementsHandler.STATUS_DOWNLOADING:
            self.pkg_size_download = status["pkg_size_download"]
            progress = 0.6 * percentage
        else:
            if self.pkg_size_download == 0:
                progress = percentage  # no download, only install
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
        self.total_download_size = total_size
        self.get_progress(total_current_size / total_size * 100, None)

    def requirement_done(self, result):
        self.get_progress(None, 100)
        self.result_requirement = result
        self.download_and_requirements_done()

    def download_done(self, result):
        self.get_progress(100, None)
        self.result_download = result
        self.download_and_requirements_done()

    @MainLoop.in_mainloop_thread
    def download_and_requirements_done(self):
        # wait for both side to be done
        if self._download_done_callback_called or (not self.result_download or not self.result_requirement):
            return
        self._download_done_callback_called = True

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
        UI.display(DisplayMessage("Installing {}".format(self.name)))
        # empty destination directory if reinstall
        for dir_to_remove in self._paths_to_clean:
            with suppress(FileNotFoundError):
                shutil.rmtree(dir_to_remove)

        Decompressor({fd: Decompressor.DecompressOrder(dir=self.dir_to_decompress_in_tarball, dest=self.install_path)},
                     self.decompress_and_install_done)
        UI.display(UnknownProgress(self.iterate_until_install_done))

    def post_install(self):
        """Call the post_install process, like creating a launcher, adding env variables…"""
        pass

    @MainLoop.in_mainloop_thread
    def decompress_and_install_done(self, result):
        self._install_done = True
        error_detected = False
        for fd in result:
            if result[fd].error:
                logger.error(result[fd].error)
                error_detected = True
            fd.close()
        if error_detected:
            UI.return_main_screen()
            return

        self.post_install()

        # Mark as installation done in configuration
        self.mark_in_config()

        UI.delayed_display(DisplayMessage("Installation done"))
        UI.return_main_screen()

    def iterate_until_install_done(self):
        while not self._install_done:
            yield
