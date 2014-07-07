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
from udtc.tools import InputError
from udtc.interactions import Choice, TextWithChoices, LicenseAgreement
from unittest.mock import Mock


class TestInteractions(LoggedTestCase):
    """Test various interactions"""

    def test_choices(self):
        """We can instantiate with a choices interactions"""
        choices = [Choice(0, "Choice0", lambda: ""), Choice(1, "Choice1", lambda: ""),
                   Choice(2, "Choice2", lambda: "")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choices, choices)
        self.assertEquals(inter.content, "Foo Content")

    def test_choices_with_text_shorcut(self):
        """We can instantiate choices interactions with shortcut"""
        choices = [Choice(0, "Choice0", lambda: "", txt_shorcut="A"), Choice(1, "Choice1", lambda: "", txt_shorcut="B"),
                   Choice(2, "Choice2", lambda: "", txt_shorcut="C")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choices, choices)
        self.assertEquals(inter.content, "Foo Content")

    def test_choices_with_default(self):
        """We can instantiate choices interactions with a default"""
        choices = [Choice(0, "Choice0", lambda: ""), Choice(1, "Choice1", lambda: "", is_default=True),
                   Choice(2, "Choice2", lambda: "")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choices, choices)
        self.assertEquals(inter.content, "Foo Content")

    def test_instantate_with_multiple_defaults_raises(self):
        """Instantiating with multiple defaults raises"""
        choices = [Choice(0, "Choice0", lambda: "", is_default=True), Choice(1, "Choice1", lambda: "", is_default=True),
                   Choice(2, "Choice2", lambda: "")]

        self.assertRaises(BaseException, TextWithChoices, "Foo Content", choices)
        self.expect_warn_error = True

    def test_choices_choose_run_right_callback(self):
        """Choose call the correct callback"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", Mock()), Choice(1, "Choice1", callback1),
                   Choice(2, "Choice2", callback2)]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choose(choice_id=1), callback1.return_value)
        self.assertEquals(inter.choose(choice_id=2), callback2.return_value)

    def test_choices_choose_with_shorcut_run_right_callback(self):
        """Choose with text shortcut calls the correct callback"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", Mock(), txt_shorcut="A"), Choice(1, "Choice1", callback1, txt_shorcut="B"),
                   Choice(2, "Choice2", callback2, txt_shorcut="C")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choose(answer='B'), callback1.return_value)
        self.assertEquals(inter.choose(answer='C'), callback2.return_value)

    def test_choices_choose_with_label_run_right_callback(self):
        """Choose with label calls the correct callback"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", Mock(), txt_shorcut="A"), Choice(1, "Choice1", callback1, txt_shorcut="B"),
                   Choice(2, "Choice2", callback2, txt_shorcut="C")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choose(answer='Choice1'), callback1.return_value)
        self.assertEquals(inter.choose(answer='Choice2'), callback2.return_value)

    def test_choices_choose_with_partial_shorcut_run_right_callback(self):
        """Choose with some having text shortcut calls the correct callback"""
        callback1 = Mock()
        choices = [Choice(0, "Choice0", Mock()), Choice(1, "Choice1", callback1, txt_shorcut="B"),
                   Choice(2, "Choice2", Mock())]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choose(answer='B'), callback1.return_value)

    def test_choices_choose_with_shorcut_no_right_casse(self):
        """Choose with shortcut without respecting the casse"""
        callback1 = Mock()
        choices = [Choice(0, "Choice0", Mock(), txt_shorcut="A"), Choice(1, "Choice1", callback1, txt_shorcut="B"),
                   Choice(2, "Choice2", Mock())]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choose(answer='b'), callback1.return_value)

    def test_choices_choose_with_label_no_right_casse(self):
        """Choose with label without respecting the casse"""
        callback1 = Mock()
        choices = [Choice(0, "Choice0", Mock()), Choice(1, "Choice1", callback1),
                   Choice(2, "Choice2", Mock())]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choose(answer='chOIce1'), callback1.return_value)

    def test_reject_invalid_choices(self):
        """TestChoice with Choices with the same id raises"""
        choices = [Choice(0, "Choice0", lambda: ""), Choice(1, "Choice1", lambda: ""),
                   Choice(0, "Choice2", lambda: "")]
        self.assertRaises(BaseException, TextWithChoices, "Foo Content", choices)
        self.expect_warn_error = True

    def test_choices_wrong_choice_id_raise(self):
        """Wrong choice_id raises an exception"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", Mock()), Choice(1, "Choice1", callback1),
                   Choice(2, "Choice2", callback2)]
        inter = TextWithChoices("Foo Content", choices)

        self.assertRaises(InputError, inter.choose, choice_id=3)
        self.expect_warn_error = True

    def test_choices_wrong_txt_shortcut_raise(self):
        """Wrong txt shortcut raises an exception"""
        choices = [Choice(0, "Choice0", Mock(), txt_shorcut='A'), Choice(1, "Choice1", Mock(), txt_shorcut='B'),
                   Choice(2, "Choice2", Mock(), txt_shorcut='C')]
        inter = TextWithChoices("Foo Content", choices)

        self.assertRaises(InputError, inter.choose, answer='Z')
        self.expect_warn_error = True

    def test_choices_wrong_label_raise(self):
        """Wrong label answer raises an exception"""
        choices = [Choice(0, "Choice0", Mock()), Choice(1, "Choice1", Mock()), Choice(2, "Choice2", Mock())]
        inter = TextWithChoices("Foo Content", choices)

        self.assertRaises(InputError, inter.choose, answer='abc')
        self.expect_warn_error = True

    def test_choices_choose_default(self):
        """Choices with a default without any answer return callback"""
        callback1 = Mock()
        choices = [Choice(0, "Choice0", Mock()), Choice(1, "Choice1", callback1, is_default=True),
                   Choice(2, "Choice2", Mock())]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEquals(inter.choose(), callback1.return_value)

    def test_choices_choose_no_default_raises(self):
        """We raise an exception if there is no default and we choose without any answer"""
        choices = [Choice(0, "Choice0", Mock()), Choice(1, "Choice1", Mock()),
                   Choice(2, "Choice2", Mock())]
        inter = TextWithChoices("Foo Content", choices)

        self.assertRaises(InputError, inter.choose)
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

        self.assertEquals(inter.choose(choice_id=0), callback_yes.return_value)
        self.assertEquals(inter.choose(choice_id=1), callback_no.return_value)
        self.assertEquals(inter.choose(answer='a'), callback_yes.return_value)
        self.assertEquals(inter.choose(answer='N'), callback_no.return_value)
        self.assertEquals(inter.choose(), callback_no.return_value)
