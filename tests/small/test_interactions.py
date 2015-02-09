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

"""Tests the various umake available interactions"""

from ..tools import LoggedTestCase
from umake.tools import InputError
from umake.interactions import Choice, TextWithChoices, LicenseAgreement, InputText, YesNo, DisplayMessage,\
    UnknownProgress
from unittest.mock import Mock


class TestInteractions(LoggedTestCase):
    """Test various interactions"""

    def test_choices(self):
        """We can instantiate with a choices interactions"""
        choices = [Choice(0, "Choice0", lambda: ""), Choice(1, "Choice1", lambda: ""),
                   Choice(2, "Choice2", lambda: "")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.choices, choices)
        self.assertEqual(inter.content, "Foo Content")

    def test_choices_with_text_shorcut(self):
        """We can instantiate choices interactions with shortcut"""
        choices = [Choice(0, "Choice0", lambda: "", txt_shorcut="A"), Choice(1, "Choice1", lambda: "", txt_shorcut="B"),
                   Choice(2, "Choice2", lambda: "", txt_shorcut="C")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.choices, choices)
        self.assertEqual(inter.content, "Foo Content")

    def test_choices_with_default(self):
        """We can instantiate choices interactions with a default"""
        choices = [Choice(0, "Choice0", lambda: ""), Choice(1, "Choice1", lambda: "", is_default=True),
                   Choice(2, "Choice2", lambda: "")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.choices, choices)
        self.assertEqual(inter.content, "Foo Content")

    def test_choices_prompt(self):
        """We give a prompt for normal choice"""
        choices = [Choice(0, "Choice0", lambda: ""), Choice(1, "Choice1", lambda: ""),
                   Choice(2, "Choice2", lambda: "")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.prompt, "Foo Content [Choice0/Choice1/Choice2] ")

    def test_choices_prompt_with_newline(self):
        """We give a prompt with newline before options if requested"""
        choices = [Choice(0, "Choice0", lambda: ""), Choice(1, "Choice1", lambda: ""),
                   Choice(2, "Choice2", lambda: "")]
        inter = TextWithChoices("Foo Content", choices, newline_before_option=True)

        self.assertEqual(inter.prompt, "Foo Content\n[Choice0/Choice1/Choice2] ")

    def test_choices_prompt_with_txt_shortcut(self):
        """We give a prompt with txt shortcut if any"""
        choices = [Choice(0, "Choice0", lambda: "", txt_shorcut="A"), Choice(1, "Choice1", lambda: "", txt_shorcut="B"),
                   Choice(2, "Choice2", lambda: "", txt_shorcut="c")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.prompt, "Foo Content [Choice0 (A)/Choice1 (B)/Choice2 (c)] ")

    def test_choices_prompt_with_partial_txt_shortcut(self):
        """We give a prompt, some choices having txt shortcut"""
        choices = [Choice(0, "Choice0", lambda: "", txt_shorcut="A"), Choice(1, "Choice1", lambda: ""),
                   Choice(2, "Choice2", lambda: "", txt_shorcut="c")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.prompt, "Foo Content [Choice0 (A)/Choice1/Choice2 (c)] ")

    def test_instantiate_with_multiple_defaults_raises(self):
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

        self.assertEqual(inter.choose(choice_id=1), callback1.return_value)
        self.assertEqual(inter.choose(choice_id=2), callback2.return_value)

    def test_choices_choose_with_shorcut_run_right_callback(self):
        """Choose with text shortcut calls the correct callback"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", Mock(), txt_shorcut="A"), Choice(1, "Choice1", callback1, txt_shorcut="B"),
                   Choice(2, "Choice2", callback2, txt_shorcut="C")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.choose(answer='B'), callback1.return_value)
        self.assertEqual(inter.choose(answer='C'), callback2.return_value)

    def test_choices_choose_with_label_run_right_callback(self):
        """Choose with label calls the correct callback"""
        callback1 = Mock()
        callback2 = Mock()
        choices = [Choice(0, "Choice0", Mock(), txt_shorcut="A"), Choice(1, "Choice1", callback1, txt_shorcut="B"),
                   Choice(2, "Choice2", callback2, txt_shorcut="C")]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.choose(answer='Choice1'), callback1.return_value)
        self.assertEqual(inter.choose(answer='Choice2'), callback2.return_value)

    def test_choices_choose_with_partial_shorcut_run_right_callback(self):
        """Choose with some having text shortcut calls the correct callback"""
        callback1 = Mock()
        choices = [Choice(0, "Choice0", Mock()), Choice(1, "Choice1", callback1, txt_shorcut="B"),
                   Choice(2, "Choice2", Mock())]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.choose(answer='B'), callback1.return_value)

    def test_choices_choose_with_shorcut_no_right_casse(self):
        """Choose with shortcut without respecting the casse"""
        callback1 = Mock()
        choices = [Choice(0, "Choice0", Mock(), txt_shorcut="A"), Choice(1, "Choice1", callback1, txt_shorcut="B"),
                   Choice(2, "Choice2", Mock())]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.choose(answer='b'), callback1.return_value)

    def test_choices_choose_with_label_no_right_casse(self):
        """Choose with label without respecting the casse"""
        callback1 = Mock()
        choices = [Choice(0, "Choice0", Mock()), Choice(1, "Choice1", callback1),
                   Choice(2, "Choice2", Mock())]
        inter = TextWithChoices("Foo Content", choices)

        self.assertEqual(inter.choose(answer='chOIce1'), callback1.return_value)

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

        self.assertEqual(inter.choose(), callback1.return_value)

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
        self.assertEqual(inter.content, "License content")
        self.assertEqual(len(inter.choices), 2, str(inter.choices))

    def test_license_agreement_choice(self):
        """We have right callbacks called in license choices"""
        callback_yes = Mock()
        callback_no = Mock()
        inter = LicenseAgreement("License content", callback_yes, callback_no)

        self.assertEqual(inter.choose(choice_id=0), callback_yes.return_value)
        self.assertEqual(inter.choose(choice_id=1), callback_no.return_value)
        self.assertEqual(inter.choose(answer='a'), callback_yes.return_value)
        self.assertEqual(inter.choose(answer='N'), callback_no.return_value)
        self.assertEqual(inter.choose(), callback_no.return_value)

    def test_license_agreement_input(self):
        """We return a license agreement input"""
        inter = LicenseAgreement("License content", lambda: "", lambda: "")
        self.assertEqual(inter.input, "[I Accept (a)/I don't accept (N)] ")

    def test_input_text(self):
        """We can instantiate an input text"""
        inter = InputText("Content", lambda: "")

        self.assertEqual(inter.content, "Content")
        self.assertEqual(inter.default_input, "")

    def test_input_text_with_default_input(self):
        """We can instantiate an input text with a default input"""
        inter = InputText("Content", lambda: "", default_input="This is a default input")

        self.assertEqual(inter.default_input, "This is a default input")

    def test_input_text_callback(self):
        """An input text runs callback with the result as argument"""
        callback_fn = Mock()
        inter = InputText("Content", callback_fn)
        inter.run_callback("Foo Bar Baz")

        callback_fn.assert_called_once_with("Foo Bar Baz")

    def test_yesno(self):
        """We can instantiate a YesNo"""
        inter = YesNo("Content?", lambda: "", lambda: "")

        self.assertEqual(inter.content, "Content?")
        self.assertEqual(len(inter.choices), 2, str(inter.choices))
        self.assertEqual(inter.prompt, "Content? [Yes (y)/No (N)] ")

    def test_yesno_choose_default(self):
        """Default is No"""
        yes_callback = Mock()
        no_callback = Mock()
        inter = YesNo("Content?", yes_callback, no_callback)
        inter.choose("")

        self.assertTrue(no_callback.called)
        self.assertFalse(yes_callback.called)

    def test_yesno_choose_default_overriden(self):
        """Default is No"""
        yes_callback = Mock()
        no_callback = Mock()
        inter = YesNo("Content?", yes_callback, no_callback, default_is_yes=True)
        inter.choose("")

        self.assertTrue(yes_callback.called)
        self.assertFalse(no_callback.called)

    def test_yesno_run_answers(self):
        """Yes runs yes in different ways"""
        yes_callback = Mock()
        no_callback = Mock()
        inter = YesNo("Content?", yes_callback, no_callback)

        self.assertEqual(inter.choose(choice_id=0), yes_callback.return_value)
        self.assertEqual(inter.choose(choice_id=1), no_callback.return_value)
        self.assertEqual(inter.choose(answer='Y'), yes_callback.return_value)
        self.assertEqual(inter.choose(answer='N'), no_callback.return_value)
        self.assertEqual(inter.choose(answer='yEs'), yes_callback.return_value)
        self.assertEqual(inter.choose(answer='nO'), no_callback.return_value)

    def test_display_message(self):
        """We can instantiate a message display"""
        inter = DisplayMessage("Content")
        self.assertEqual(inter.text, "Content")

    def test_unknown_progress(self):
        """We can instantiate an unknown progress"""
        def foo():
            yield
        inter = UnknownProgress(foo)
        inter.bar = "BarElement"

        self.assertEqual(inter.bar, "BarElement")
