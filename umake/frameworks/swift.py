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


"""Swift module"""

from contextlib import suppress
from gettext import gettext as _
import gnupg
import logging
import os
import re
import tempfile

import umake.frameworks.baseinstaller
from umake.interactions import DisplayMessage
from umake.tools import add_env_to_user, as_root, MainLoop, get_current_ubuntu_version
from umake.network.download_center import DownloadCenter, DownloadItem
from umake.ui import UI

logger = logging.getLogger(__name__)


class SwiftCategory(umake.frameworks.BaseCategory):

    def __init__(self):
        super().__init__(name="Swift", description=_("Swift language"),
                         logo_path=None)


class SwiftLang(umake.frameworks.baseinstaller.BaseInstaller):

    def __init__(self, category):
        super().__init__(name="Swift Lang", description=_("Swift compiler (default)"), is_category_default=True,
                         packages_requirements=["clang", "libicu-dev"],
                         category=category, only_on_archs=['amd64'],
                         download_page="https://swift.org/download/",
                         dir_to_decompress_in_tarball="swift*",
                         required_files_path=[os.path.join("usr", "bin", "swift")])
        self.asc_url = "https://swift.org/keys/all-keys.asc"

    def parse_download_link(self, line, in_download):
        """Parse Swift download link, expect to find a .sig file"""
        sig_url = None
        if '.tar.gz.sig' in line:
            in_download = True
        if in_download:
            p = re.search(r'href="(.*)" title="PGP Signature"', line)
            with suppress(AttributeError):
                sig_url = "https://swift.org" + p.group(1)
                logger.debug("Found signature link: {}".format(sig_url))
        return (sig_url, in_download)

    @MainLoop.in_mainloop_thread
    def get_metadata_and_check_license(self, result):
        """Download files to download + license and check it"""
        logger.debug("Parse download metadata")

        error_msg = result[self.download_page].error
        if error_msg:
            logger.error("An error occurred while downloading {}: {}".format(self.download_page, error_msg))
            UI.return_main_screen(status_code=1)
        in_download = False
        sig_url = None
        for line in result[self.download_page].buffer:
            line_content = line.decode()
            (new_sig_url, in_download) = self.parse_download_link(line_content, in_download)
            if str(new_sig_url) > str(sig_url):
                tmp_release = re.search("ubuntu(.....).tar", new_sig_url).group(1)
                if tmp_release <= get_current_ubuntu_version():
                    sig_url = new_sig_url

        if not sig_url:
            logger.error("Download page changed its syntax or is not parsable")
            UI.return_main_screen(status_code=1)

        DownloadCenter(urls=[DownloadItem(sig_url, None), DownloadItem(self.asc_url, None)],
                       on_done=self.check_gpg_and_start_download, download=False)

    def _check_gpg_signature(self, gnupgdir, asc_content, sig):
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

    @MainLoop.in_mainloop_thread
    def check_gpg_and_start_download(self, download_result):
        asc_content = download_result.pop(self.asc_url).buffer.getvalue().decode('utf-8')
        sig_url = list(download_result.keys())[0]
        res = download_result[sig_url]
        sig = res.buffer.getvalue().decode('utf-8').split()[0]

        # When we install new packages, we are executing as root and then dropping
        # as the user for extracting and such. However, for signature verification,
        # we use gpg. This one doesn't like priviledge drop (if uid = 0 and
        # euid = 1000) and asserts if uid != euid.
        # Importing the key as root as well creates new gnupg files owned as root if
        # new keys weren't imported first.
        # Consequently, run gpg as root if we needed root access or as the user
        # otherwise. We store the gpg public key in a temporary gnupg directory that
        # will be removed under the same user rights (this directory needs to be owned
        # by the same user id to not be rejected by gpg).Z
        if self.need_root_access:
            with as_root():
                with tempfile.TemporaryDirectory() as tmpdirname:
                    self._check_gpg_signature(tmpdirname, asc_content, sig)
        else:
            with tempfile.TemporaryDirectory() as tmpdirname:
                self._check_gpg_signature(tmpdirname, asc_content, sig)

        # you get and store self.download_url
        url = re.sub('.sig', '', sig_url)
        if url is None:
            logger.error("Download page changed its syntax or is not parsable (missing url)")
            UI.return_main_screen(status_code=1)
        logger.debug("Found download link for {}".format(url))
        self.download_requests.append(DownloadItem(url, None))
        self.start_download_and_install()

    def post_install(self):
        """Add swift necessary env variables"""
        add_env_to_user(self.name, {"PATH": {"value": os.path.join(self.install_path, "usr", "bin")}})
        UI.delayed_display(DisplayMessage(_("You need to restart your current shell session for your {} installation "
                                            "to work properly").format(self.name)))
