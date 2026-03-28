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
from gettext import gettext as _
from io import StringIO
import gnupg
import json
import logging
from progressbar import ProgressBar
import os
import shutil
import umake.frameworks
from umake.decompressor import Decompressor
from umake.interactions import InputText, YesNo, LicenseAgreement, DisplayMessage, UnknownProgress
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.network.requirements_handler import RequirementsHandler
from umake.ui import UI
from umake.settings import DEFAULT_INSTALL_TOOLS_PATH
from umake.tools import MainLoop, strip_tags, launcher_exists, get_icon_path, get_launcher_path, \
    Checksum, remove_framework_envs_from_user, add_exec_link, validate_url

logger = logging.getLogger(__name__)


class BaseInstaller(umake.frameworks.BaseFramework):

    DIRECT_COPY_EXT = ['.svg', '.png', '.ico', '.jpg', '.jpeg']
    # Framework environment variables are added to `~/.profile` which may
    # require logging back into your session for the changes to be picked up.
    # Use `RELOGIN_REQUIRE_MSG` to alert users to this fact, in `post_install`
    # function. {} in replaced with the framework name at runtime.
    RELOGIN_REQUIRE_MSG = _("You may need to log back in for your {} installation to work properly")

    def __new__(cls, *args, **kwargs):
        "This class is not meant to be instantiated, so __new__ returns None."
        if cls == BaseInstaller:
            return None
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        """The Downloader framework isn't instantiated directly, but is useful to inherit from for all frameworks

        having a set of downloads to proceed, some eventual supported_archs."""
        self.package_url = None
        self.download_page = kwargs["download_page"]
        self.checksum_type = kwargs.get("checksum_type", None)
        self.dir_to_decompress_in_tarball = kwargs.get("dir_to_decompress_in_tarball", "")
        self.required_files_path = kwargs.get("required_files_path", [])
        self.desktop_filename = kwargs.get("desktop_filename", None)
        self.icon_filename = kwargs.get("icon_filename", None)
        self.match_last_link = kwargs.get("match_last_link", False)
        self.json = kwargs.get("json", False)
        self.override_install_path = kwargs.get("override_install_path", None)
        for extra_arg in ["download_page", "checksum_type", "dir_to_decompress_in_tarball",
                          "desktop_filename", "icon_filename", "required_files_path",
                          "match_last_link"]:
            with suppress(KeyError):
                kwargs.pop(extra_arg)
        super().__init__(*args, **kwargs)

        self._install_done = False
        self._paths_to_clean = set()
        self._arg_install_path = None
        self.download_requests = []

    @property
    def exec_link_name(self):
        if self.desktop_filename:
            return self.desktop_filename.split('.')[0]
        return None

    @property
    def is_installed(self):
        # check path and requirements
        if not super().is_installed:
            return False
        for required_file_path in self.required_files_path:
            if not os.path.exists(os.path.join(self.install_path, required_file_path)):
                logger.debug("{} binary isn't installed".format(self.name))
                return False
        if self.desktop_filename:
            return launcher_exists(self.desktop_filename)
        logger.debug("{} is installed".format(self.name))
        return True

    def setup(self, install_path=None, auto_accept_license=False, dry_run=False, assume_yes=False):
        self.arg_install_path = install_path
        self.auto_accept_license = auto_accept_license
        self.dry_run = dry_run
        self.assume_yes = assume_yes
        super().setup()

        # first step, check if installed or dry_run
        if self.dry_run:
            self.download_provider_page()
        elif self.is_installed:
            if self.assume_yes:
                self.reinstall()
            else:
                UI.display(YesNo("{} is already installed on your system, do you want to reinstall "
                                 "it anyway?".format(self.name), self.reinstall, UI.return_main_screen))
        else:
            self.confirm_path(self.arg_install_path)

    def reinstall(self):
        logger.debug("Mark previous installation path for cleaning.")
        self._paths_to_clean.add(self.install_path)  # remove previous installation path
        self.confirm_path(self.arg_install_path)
        remove_framework_envs_from_user(self.name)

    def depends(self):
        """List necessary apt dependencies"""
        if not self.need_root_access:
            UI.display(DisplayMessage("Required packages are installed"))
        else:
            UI.display(DisplayMessage("Required packages will be installed"))
        UI.display(DisplayMessage(' '.join(self.packages_requirements)))
        UI.return_main_screen(status_code=0)

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
                os.remove(os.path.join(self.default_binary_link_path, self.exec_link_name))
        if self.icon_filename:
            with suppress(FileNotFoundError):
                os.remove(get_icon_path(self.icon_filename))
        with suppress(FileNotFoundError):
            shutil.rmtree(self.install_path)
            path = os.path.dirname(self.install_path)
            while path is not DEFAULT_INSTALL_TOOLS_PATH:
                if os.listdir(path) == []:
                    logger.debug("Empty folder, cleaning recursively: {}".format(path))
                    os.rmdir(path)
                    path = os.path.dirname(path)
                else:
                    break
        remove_framework_envs_from_user(self.name)
        self.remove_from_config()

        UI.delayed_display(DisplayMessage("Suppression done"))
        UI.return_main_screen()

    def set_exec_path(self):
        if self.desktop_filename:
            self.exec_path = os.path.join(self.install_path, self.required_files_path[0])

    def confirm_path(self, path_dir=""):
        """Confirm path dir"""

        if self.assume_yes:
            UI.display(DisplayMessage("Assuming default path: " + self.install_path))
            path_dir = self.install_path

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
        if self.override_install_path is not None:
            logger.info("Install Path has been overridden to fix an upstream issue.")
            self.install_path += "/" + self.override_install_path
        self.set_exec_path()
        self.download_provider_page()

    def set_installdir_to_clean(self):
        logger.debug("Mark non empty new installation path for cleaning.")
        self._paths_to_clean.add(self.install_path)
        self.set_exec_path()
        self.download_provider_page()

    def download_provider_page(self):
        logger.debug("Download application provider page")
        DownloadCenter([DownloadItem(self.download_page)], self.get_metadata_and_check_license, download=False)

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

    def store_package_url(self, result):
        logger.debug("Parse download metadata")
        self.auto_accept_license = True
        self.dry_run = True

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))

        self.new_download_url = None
        self.shasum_read_method = hasattr(self, 'get_sha_and_start_download')
        with StringIO() as license_txt:
            url, checksum = self.get_metadata(result, license_txt)
            self.package_url = url

    def get_metadata(self, result, license_txt):

        url, checksum = (None, None)
        page = result[self.download_page]
        if self.json is True:
            logger.debug("Using json parser")
            try:
                latest = json.loads(page.buffer.read().decode())
                # On a download from github, if the page is not .../releases/latest
                # we want to download the latest version (beta/development)
                # So we get the first element in the json tree.
                # In the framework we only change the url and this condition is satisfied.
                if self.download_page.startswith("https://api.github.com") and \
                        not self.download_page.endswith("/latest"):
                    latest = latest[0]
                url = None
                in_download = False
                (url, in_download) = self.parse_download_link(latest, in_download)
                if not url:
                    if not self.url:
                        raise IndexError
                    else:
                        logger.debug("We set a temporary url while fetching the checksum")
                        url = self.url
            except (json.JSONDecodeError, IndexError):
                logger.error("Can't parse the download URL from the download page.")
                UI.return_main_screen(status_code=1)
            logger.debug("Found download URL: " + url)

        else:
            in_license = False
            in_download = False
            for line in page.buffer:
                line_content = line.decode()

                if self.expect_license and not self.auto_accept_license:
                    in_license = self.parse_license(line_content, license_txt, in_license)

                # always take the first valid (url, checksum) if not match_last_link is set to True:
                download = None
                # if not in_download:
                if (url is None or (self.checksum_type and not checksum) or
                    self.match_last_link) and \
                        not (self.shasum_read_method and self.new_download_url):
                    (download, in_download) = self.parse_download_link(line_content, in_download)

                if download is not None:
                    (newurl, new_checksum) = download
                    url = newurl if newurl is not None else url
                    checksum = new_checksum if new_checksum is not None else checksum
                    if url is not None:
                        if self.checksum_type and checksum:
                            logger.debug("Found download link for {}, checksum: {}".format(url, checksum))
                        elif not self.checksum_type:
                            logger.debug("Found download link for {}".format(url))
        return url, checksum

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Download files to download + license and check it"""
        logger.debug("Parse download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)

        self.new_download_url = None
        self.shasum_read_method = hasattr(self, 'get_sha_and_start_download')
        with StringIO() as license_txt:
            url, checksum = self.get_metadata(result, license_txt)
            if hasattr(self, 'get_sha_and_start_download'):
                logger.debug('Run get_sha_and_start_download')
                DownloadCenter(urls=[DownloadItem(self.new_download_url, None)],
                               on_done=self.get_sha_and_start_download, download=False)
            else:
                self.check_data_and_start_download(url, checksum, license_txt)

    def check_data_and_start_download(self, url=None, checksum=None, license_txt=StringIO()):
        if url is None:
            logger.error("Download page changed its syntax or is not parsable (url missing)")
            UI.return_main_screen(status_code=1)
        if (self.checksum_type and checksum is None):
            logger.error("Download page changed its syntax or is not parsable (checksum missing)")
            logger.error("URL is: {}".format(url))
            UI.return_main_screen(status_code=1)
        self.download_requests.append(DownloadItem(url, Checksum(self.checksum_type, checksum)))

        if self.dry_run:
            if validate_url(url):
                UI.display(DisplayMessage("Found download URL: " + url))
            if checksum is not None:
                UI.display(DisplayMessage("Found download checksum: " + checksum))
            UI.return_main_screen(status_code=0)

        if license_txt.getvalue() != "":
            logger.debug("Check license agreement.")
            UI.display(LicenseAgreement(strip_tags(license_txt.getvalue()).strip(),
                                        self.start_download_and_install,
                                        UI.return_main_screen))
        elif self.expect_license and not self.auto_accept_license:
            logger.error("We were expecting to find a license on the download page, we didn't.")
            UI.return_main_screen(status_code=1)
        else:
            self.start_download_and_install()

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

        if not self.pbar.finished:  # drawing is delayed, so ensure we are not done first
            progress = self._calculate_progress()
            self.pbar.update(progress)

    def _calculate_progress(self):
        progress = self.balance_requirement_download * self.last_progress_requirement +\
            (1 - self.balance_requirement_download) * self.last_progress_download
        normalized_progress = max(0, progress)
        normalized_progress = min(normalized_progress, 100)
        return normalized_progress

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
        # don't push any progress until we have the total download size
        if len(downloads) != len(self.download_requests):
            return
        total_size = 0
        total_current_size = 0
        for download in downloads:
            total_size += downloads[download]["size"]
            total_current_size += downloads[download]["current"]
        self.total_download_size = total_size
        self.get_progress(total_current_size / total_size * 100, None)

    def requirement_done(self, result):
        # set requirement download as finished if no error
        if not result.error:
            self.get_progress(None, 100)
        self.result_requirement = result
        self.download_and_requirements_done()

    def download_done(self, result):
        # set download as finished if no error
        for url in result:
            if result[url].error:
                break
        else:
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
        if self.result_requirement.error:
            logger.error("Package requirements can't be met: {}".format(self.result_requirement.error))
            error_detected = True

        # check for any errors and collect fds
        fds = []
        for url in self.result_download:
            if self.result_download[url].error:
                logger.error(self.result_download[url].error)
                error_detected = True
            fds.append(self.result_download[url].fd)
        if error_detected:
            UI.return_main_screen(status_code=1)

        # now decompress
        self.decompress_and_install(fds)

    def decompress_and_install(self, fds):
        UI.display(DisplayMessage("Installing {}".format(self.name)))
        # empty destination directory if reinstall
        for dir_to_remove in self._paths_to_clean:
            with suppress(FileNotFoundError):
                shutil.rmtree(dir_to_remove)
            # marked them as cleaned
            self._paths_to_clean = []

        os.makedirs(self.install_path, exist_ok=True)
        decompress_fds = {}
        for fd in fds:
            direct_copy = False
            for ext in self.DIRECT_COPY_EXT:
                if fd.name.endswith(ext):
                    direct_copy = True
                    break
            if direct_copy:
                shutil.copy2(fd.name, os.path.join(self.install_path, os.path.basename(fd.name)))
            else:
                decompress_fds[fd] = Decompressor.DecompressOrder(dir=self.dir_to_decompress_in_tarball,
                                                                  dest=self.install_path)
        Decompressor(decompress_fds, self.decompress_and_install_done)
        UI.display(UnknownProgress(self.iterate_until_install_done))

    def _check_gpg_signature(gnupgdir, asc_content, sig):
        """check gpg signature (temporary stock in dir)"""
        gpg = gnupg.GPG(gnupghome=gnupgdir)
        imported_keys = gpg.import_keys(asc_content)
        if imported_keys.count == 0:
            logger.error("Keys not valid")
            UI.return_main_screen(status_code=1)
        verify = gpg.verify(sig)
        if verify is False:
            logger.error("Signature not valid")
            UI.return_main_screen(status_code=1)

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
            UI.return_main_screen(status_code=1)

        if self.exec_link_name:
            add_exec_link(self.exec_path, self.exec_link_name)
        self.post_install()
        # Mark as installation done in configuration
        self.mark_in_config()

        UI.delayed_display(DisplayMessage("Installation done"))
        UI.return_main_screen()

    def iterate_until_install_done(self):
        while not self._install_done:
            yield
