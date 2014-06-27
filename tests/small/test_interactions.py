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

"""Tests the various udtc available interactions"""

from ..tools import LoggedTestCase
from udtc.interactions import Choice, TextWithChoices, LicenseAgreement
from unittest.mock import Mock


class TestInteractions(LoggedTestCase):
    """Test various interactions"""

    def test_choices(self):
        """We can instantiate with a choices interactions"""
        choices = [Choice(0, "Choice0", "A", lambda: ""), Choice(1, "Choice1", "B", lambda: ""),
                   Choice(2, "Choice2", "C", lambda: "")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choices, choices)
        self.assertEquals(inter.content, "Foo Content")

    def test_choices_choose_return_right_callback(self):
        """Choose call the correct callback"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", "A", Mock()), Choice(1, "Choice1", "B", callback1),
                   Choice(2, "Choice2", "C", callback2)]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choose(choice_id=1), callback1)
        self.assertEquals(inter.choose(choice_id=2), callback2)

    def test_choices_choose_with_shorcut_return_right_callback(self):
        """Choose  with text shorcut call the correct callback"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", "A", Mock()), Choice(1, "Choice1", "B", callback1),
                   Choice(2, "Choice2", "C", callback2)]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choose(txt_shorcut='B'), callback1)
        self.assertEquals(inter.choose(txt_shorcut='C'), callback2)

    def test_reject_invalid_choices(self):
        """TestChoice with Choices with the same idea raises"""
        choices = [Choice(0, "Choice0", "A", lambda: ""), Choice(1, "Choice1", "B", lambda: ""),
                   Choice(0, "Choice2", "C", lambda: "")]
        self.assertRaises(BaseException, TextWithChoices, "Foo Content", choices)
        self.expect_warn_error = True

    def test_choices_wrong_choice_id_raise(self):
        """Wrong choice_id raises an exception"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", "A", Mock()), Choice(1, "Choice1", "B", callback1),
                   Choice(2, "Choice2", "C", callback2)]
        inter = TextWithChoices("Foo Content", choices)

        self.assertRaises(BaseException, inter.choose(choice_id=3))
        self.expect_warn_error = True

    def test_choices_wrong_txt_shortcut_raise(self):
        """Wrong txt shortcut raises an exception"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", "A", Mock()), Choice(1, "Choice1", "B", callback1),
                   Choice(2, "Choice2", "C", callback2)]
        inter = TextWithChoices("Foo Content", choices)

        self.assertRaises(BaseException, inter.choose(txt_shorcut='Z'))
        self.expect_warn_error = True

    def test_license_agreement(self):
        """We can instantiate a license agreement interaction"""
        callback_yes = Mock()
        callback_no = Mock()
        inter = LicenseAgreement("License content", callback_yes, callback_no)
        self.assertEquals(inter.content, "License content")
        self.assertEquals(len(inter.choices), 2)

    def test_license_agreement_choice(self):
        """We have right callbacks called in license choices"""
        callback_yes = Mock()
        callback_no = Mock()
        inter = LicenseAgreement("License content", callback_yes, callback_no)

        self.assertEquals(inter.choose(choice_id=0), callback_yes)
        self.assertEquals(inter.choose(choice_id=1), callback_no)
        self.assertEquals(inter.choose(txt_shorcut='a'), callback_yes)
        self.assertEquals(inter.choose(txt_shorcut='N'), callback_no)
