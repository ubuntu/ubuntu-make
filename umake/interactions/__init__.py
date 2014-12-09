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
from umake.tools import InputError

logger = logging.getLogger(__name__)


class Choice:

    def __init__(self, id, label, callback_fn, txt_shorcut=None, is_default=False):
        """Choice element containing label and callback function"""
        self.id = id
        self.label = label
        self.txt_shorcut = txt_shorcut
        self.callback_fn = callback_fn
        self.is_default = is_default


class TextWithChoices:

    def __init__(self, content, choices=[], newline_before_option=False):
        """Content text with a list of multiple Choice elements"""
        current_ids = []
        default_found = False
        for choice in choices:
            if choice.id in current_ids:
                message = "{} choice id is already in registered ids. Can't instantiate this " \
                          "interaction".format(choice.id)
                logger.error(message)
                raise BaseException(message)
            current_ids.append(choice.id)
            if choice.is_default:
                if default_found:
                    message = "One default was already registered, can't register a second one in that choices set: {}"\
                              .format([choice.label for choice in choices])
                    logger.error(message)
                    raise BaseException(message)
                default_found = True
        self.content = content
        self.choices = choices
        self.newline_before_option = newline_before_option

    def choose(self, choice_id=None, answer=None):
        """Return associated callback for choice"""
        for choice in self.choices:
            if (choice_id is not None and choice.id == choice_id) or\
                    (answer is not None and (choice.label.lower() == answer.lower() or
                                             (choice.txt_shorcut is not None and
                                              choice.txt_shorcut.lower() == answer.lower()))):
                return choice.callback_fn()
        msg = _("No suitable answer provided")
        if choice_id is not None:
            msg = _("Your entry '{}' isn't an acceptable choice. choices are: {}")\
                .format(choice_id, [choice.id for choice in self.choices])
        if answer is not None:
            msg = _("Your entry '{}' isn't an acceptable choice. choices are: {} and {}")\
                .format(answer, [choice.txt_shorcut for choice in self.choices if choice.txt_shorcut is not None],
                        [choice.label for choice in self.choices])
        if not choice_id and not answer:
            for choice in self.choices:
                if choice.is_default:
                    return choice.callback_fn()
        logger.error(msg)
        raise InputError(msg)

    @property
    def prompt(self):
        """Text prompt handling if we do have some shortcuts"""
        possible_answers = []
        for choice in self.choices:
            answer = choice.label
            if choice.txt_shorcut:
                # NOTE: sum of answers
                answer += _(" ({})").format((choice.txt_shorcut))
            possible_answers.append(answer)
        if self.newline_before_option:
            # NOTE: first is prompt, newline and then set of answers
            prompt = _("{}\n[{}] ").format(self.content, '/'.join(possible_answers))
        else:
                # NOTE: first is prompt, then set of answers:
            prompt = _("{} [{}] ").format(self.content, '/'.join(possible_answers))
        return prompt


class LicenseAgreement(TextWithChoices):

    def __init__(self, content, callback_yes, callback_no):
        """License agreement text with accept/decline"""
        choices = [Choice(0, _("I Accept"), callback_yes, txt_shorcut=_("a")),
                   Choice(1, _("I don't accept"), callback_no,  txt_shorcut=_("N"), is_default=True)]
        super().__init__(content, choices=choices, newline_before_option=True)

    @property
    def input(self):
        """Text input prompt handling if we do have some shortcuts"""
        answers = []
        for choice in self.choices:
            # NOTE: first element is choice, and then shortcut
            _("{} ({})")
            answer = _("{} ({})").format(choice.label, choice.txt_shorcut)
            answers.append(answer)
        # append different possible choices
        return _("[{}] ").format('/'.join(answers))


class InputText:

    def __init__(self, content, callback_fn, default_input=""):
        """Content text with an line input"""
        self.content = content
        self._callback_fn = callback_fn
        self.default_input = default_input

    def run_callback(self, result):
        self._callback_fn(result)


class YesNo(TextWithChoices):

    def __init__(self, content, callback_yes, callback_no, default_is_yes=False):
        """Return a basic Yes No question, default being false or overriden"""
        super().__init__(content, [Choice(0, _("Yes"), callback_yes, txt_shorcut=_('y'), is_default=default_is_yes),
                                   Choice(1, _("No"), callback_no, txt_shorcut=_("N"),
                                          is_default=(not default_is_yes))])


class DisplayMessage:
    def __init__(self, text):
        self.text = text


class UnknownProgress:
    def __init__(self, iterator):
        self.bar = None
        self._iterator = iterator
