# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2016-2017 Toshio Kuratomi <toshio@fedoraproject.org>
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
Login Screen widget
"""

import itertools

import urwid

from magnate.logging import log


mlog = log.fields(mod=__name__)


class LoginScreen(urwid.WidgetWrap):
    """
    Screen that prompts the user to login
    """
    signals = ['logged_in']

    def __init__(self, pubpen):
        flog = mlog.fields(func='LoginScreen.__init__')
        flog.fields(pubpen=pubpen).debug('Initializing LoginScreen')

        self.pubpen = pubpen

        flog.debug('Creating widgets')
        username_label = urwid.Text('Username: ', align='right')
        password_label = urwid.Text('Password: ', align='right')
        self.username = urwid.Edit()
        self.password = urwid.Edit()
        login_button = urwid.Button('Login')
        decorated_login_button = urwid.AttrMap(login_button, None, focus_map='reversed')
        quit_button = urwid.Button('Quit')
        decorated_quit_button = urwid.AttrMap(quit_button, None, focus_map='reversed')
        buttons = urwid.Columns((
            (len('Login') + 4, decorated_login_button),
            (len('Quit') + 4, decorated_quit_button),
            ), focus_column=1)

        labels = urwid.Pile([username_label, password_label])
        self.fields = urwid.Pile([self.username, self.password, buttons],
                                 focus_item=0)
        entry_box = urwid.Columns([labels, self.fields])

        self.status_message = urwid.Text(' ', align='center')
        entry_with_status = urwid.Pile([entry_box, self.status_message])

        padded_entry_with_status = urwid.Padding(entry_with_status, align='center')
        self.display = urwid.Filler(padded_entry_with_status, valign='middle')
        decorate = urwid.LineBox(self.display)
        super().__init__(decorate)

        flog.debug('setting focus order')
        self.focusable_widgets = (w for w in itertools.cycle((
            ((self.fields, 1),),
            ((self.fields, 2), (buttons, 0)),
            ((self.fields, 2), (buttons, 1)),
            ((self.fields, 0),)
        )))

        flog.debug('connecting to the urwid events')
        urwid.connect_signal(login_button, 'click', self.attempt_login)
        urwid.connect_signal(quit_button, 'click', self.quit)

        flog.debug('connecting to backend events')
        self.pubpen.subscribe('user.login_success', self.handle_login_success)
        self.pubpen.subscribe('user.login_failure', self.handle_login_failure)

        flog.debug('Leaving LoginScreen initialization')

    def reset(self):
        """Reset the login form"""
        flog = mlog.fields(func='LoginScreen.reset')
        flog.debug('Clear the login forms')

        self.username.set_edit_text('')
        self.password.set_edit_text('')
        self.fields.focus_position = 0

        flog.debug('Leaving reset()')

    def attempt_login(self, *args):
        """Notify the dispatcher to attempt to login"""
        flog = mlog.fields(func='LoginScreen.attempt_login')
        flog.debug('Initializing LoginScreen')
        self.pubpen.publish('action.account.login_attempt',
                            self.username.get_text()[0],
                            self.password.get_text()[0])

    @staticmethod
    def quit(button):
        """End the game"""
        raise urwid.ExitMainLoop()

    def handle_login_success(self, username):
        """Show that the user has been logged in"""
        flog = mlog.fields(func='LoginScreen.handle_login_success')
        flog.fields(username=username).debug('Handling backend login success')

        self.reset()
        urwid.emit_signal(self, 'logged_in')

        flog.debug('Leaving handle_login_success()')

    def handle_login_failure(self, username, reason):
        """Handle a login failure"""
        flog = mlog.fields(func='LoginScreen.handle_login_failure')
        flog.fields(username=username, reason=reason).debug('Handling backend login failure')

        self.reset()
        self.status_message.set_text(('reversed', f'Failed to login {username}'))

        flog.debug('Leaving handle_login_failure()')

    def keypress(self, size, key):
        """Handle cycling through inputs and submitting login data"""
        super().keypress(size, key)  # pylint: disable=not-callable
        if key == 'enter':
            self.attempt_login()
            return
        elif key == 'tab':
            focus_paths = next(self.focusable_widgets)
            for widget, position in focus_paths:
                widget.focus_position = position
            return
        return key
