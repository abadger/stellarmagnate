# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2019 Toshio Kuratomi <toshio@fedoraproject.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
New Account Dialog
"""
import itertools

import urwid

from magnate.logging import log


mlog = log.fields(mod=__name__)


class NewAccountDialog(urwid.Filler):
    """
    Form for New Account Signup
    """
    _selectable = True
    signals = ['close_new_account_dialog']

    def __init__(self, pubpen):
        flog = mlog.fields(func='NewAccountDialog.__init__')
        flog.fields(pubpen=pubpen).debug('Initializing NewAccountDialog')

        self.pubpen = pubpen

        flog.debug('Creating widgets')
        username_label = urwid.Text('Username: ', align='right')
        password_label = urwid.Text('Password: ', align='right')
        confirm_password_label = urwid.Text('Confirm password: ', align='right')
        self.username = urwid.Edit()
        self.password = urwid.Edit(mask='*')
        self.confirm_password = urwid.Edit(mask='*')

        self.apply_button = urwid.Button('Sign up')
        decorated_apply_button = urwid.AttrMap(self.apply_button, None, focus_map='reversed')
        cancel_button = urwid.Button('Cancel')
        decorated_cancel_button = urwid.AttrMap(cancel_button, None, focus_map='reversed')

        self.buttons = urwid.Columns((
            (len('Sign up') + 4, decorated_apply_button),
            (len('Cancel') + 4, decorated_cancel_button),
            ), focus_column=1)

        labels = urwid.Pile([username_label, password_label, confirm_password_label])
        self.fields = urwid.Pile([self.username, self.password, self.confirm_password,
                                  self.buttons], focus_item=0)
        entry_box = urwid.Columns([labels, self.fields])

        self.status_message = urwid.Text(' ', align='center')
        entry_with_status = urwid.Pile([('flow', entry_box), self.status_message])

        decorated_entry = urwid.LineBox(entry_with_status, tlcorner='\u2554',
                                        tline='\u2550', trcorner='\u2557',
                                        blcorner='\u255A', bline='\u2550',
                                        brcorner='\u255D', lline='\u2551',
                                        rline='\u2551')

        padded_entry_with_status = urwid.Padding(decorated_entry, align='center',
                                                 width=(len('Confirm password: ') + 4
                                                        + len('Sign up') + len('Cancel') + 10))
        dialog = urwid.Filler(padded_entry_with_status, valign='middle',
                              height=len(self.fields.contents) + 2)

        super().__init__(padded_entry_with_status, valign='middle')

        flog.debug('connecting to the urwid events')
        urwid.connect_signal(self.apply_button, 'click', self.create_account)
        urwid.connect_signal(cancel_button, 'click', self.return_to_auth)

        flog.debug('connecting to backend events')

        self.reset()
        flog.debug('Leaving New Account initialization')
        pass
        return

        flog.debug('connecting to backend events')
        self.pubpen.subscribe('user.login_success', self.handle_login_success)
        self.pubpen.subscribe('user.login_failure', self.handle_login_failure)

        self.reset()

    def reset(self):
        flog = mlog.fields(func='NewAccountDialog.reset')
        flog.debug('Clear the New Account Form')

        self.username.set_edit_text('')
        self.password.set_edit_text('')
        self.confirm_password.set_edit_text('')
        self.fields.focus_position = 0
        self.buttons.focus_position = 0

        flog.debug('setting focus order')
        self.focusable_widgets = (w for w in itertools.cycle((
            ((self.fields, 1),),
            ((self.fields, 2),),
            ((self.fields, 3), (self.buttons, 0)),
            ((self.fields, 3), (self.buttons, 1)),
            ((self.fields, 0),),
        )))

    def finalize(self):
        """Cleanup any game menu state when the dialog is hidden"""
        pass

    def create_account(self, *args):
        """Ask the backend to create an account for us"""
        flog = mlog.fields(func='NewAccountDialog.create_account')
        flog.fields(args=args).debug('Creating a new account')
        import traceback
        flog.fields(stack=traceback.format_stack()).debug('stacktrace')

        # Verify that a username was entered
        username = self.username.get_text()[0].strip()
        if not username:
            self.username.set_edit_text('')
            self.fields.focus_position = 0
            self.status_message.set_text(('reversed', 'Must enter a username'))
            flog.debug('Leaving create_account with username error')
            return

        # Verify that the passwords match
        password = self.password.get_text()[0]
        confirm_password = self.confirm_password.get_text()[0]
        if password != confirm_password:
            flog.debug('Passwords did not match')
            self.password.set_edit_text('')
            self.confirm_password.set_edit_text('')
            self.fields.focus_position = 1
            self.status_message.set_text(('reversed', 'Passwords do not match'))
            flog.debug('Leaving create_account with password error')
            return

        # Submit the information to the backend to make a request
        flog.debug('request new account from backend')
        self.pubpen.publish('action.account.new_user', username, password)
        flog.debug('Leaving create_account')

    def return_to_auth(self, *args):
        """Close the game menu and continue playing"""
        self.reset()
        urwid.emit_signal(self, 'close_new_account_dialog')

    def keypress(self, size, key):
        flog = mlog.fields(func='NewAccountDialog.keypress')
        flog.fields(size=size, key=key).debug('Handling keypress')

        super().keypress(size, key)
        if key == 'tab':
            focus_paths = next(self.focusable_widgets)
            for widget, position in focus_paths:
                widget.focus_position = position
        elif key == 'esc':
            self.return_to_auth()
        flog.debug('Returning None')
        return None
