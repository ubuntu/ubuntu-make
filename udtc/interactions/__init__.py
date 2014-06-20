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


# module gather different types of interactions with the UI

from gettext import gettext as _
import logging

logger = logging.getLogger(__name__)


class Choice:

    def __init__(self, id, label, callback_fn):
        """Choice element containing label and callback function"""
        self.id = id
        self.label = label
        self.callback_fn = callback_fn


class TextWithChoices:

    def __init__(self, content, choices=[]):
        """Content text with a list of multiple Choice elements"""
        current_ids = []
        for choice in choices:
            if choice.id in current_ids:
                message = "{} choice id is already in registered ids. Can't instantiate this " \
                          "interaction".format(choice.id)
                logger.error(message)
                raise BaseException(message)
            current_ids.append(choice.id)
        self.content = content
        self.choices = choices

    def choose(self, choice_id):
        """Return associated callback for choice"""
        for choice in self.choices:
            if choice.id == choice_id:
                return choice.callback_fn
        logger.error("{} isn't an acceptable choice. choices list is: "
                     "{}".format(choice_id, [choice.id for choice in self.choices]))


class LicenseAgreement(TextWithChoices):

    def __init__(self, content, callback_yes, callback_no):
        """License agreement text with accept/decline"""
        choices = [Choice(0, _("I Accept"), callback_yes),
                   Choice(1, _("I don't accept"), callback_no)]
        super().__init__(content, choices=choices)
