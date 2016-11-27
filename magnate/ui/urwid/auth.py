#
# Stellar Magnate - A space-themed commodity trading game
# Copyright (C) 2016, Toshio Kuratomi <toshio@fedoraproject.org>
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

import itertools

import urwid


class LoginScreen(urwid.WidgetWrap):
    signals = ['logged_in']

    def __init__(self, pubpen):
        self.pubpen = pubpen

        # Grid widget
        # label: Username    # entrybox
        # label: Password    # entrybox
        username_label = urwid.Text('Username: ', align='right')
        password_label = urwid.Text('Password: ', align='right')
        self.username = urwid.Edit()
        self.password = urwid.Edit()
        self.quit_button = urwid.Button('Quit')
        self.login_button = urwid.Button('Login')
        self.buttons = urwid.Columns((
            (len('Quit') + 4, self.quit_button),
            (len('Login') + 4, self.login_button),
            ), focus_column=1)

        labels = urwid.Pile([username_label, password_label])
        self.fields = urwid.Pile([self.username, self.password, self.buttons], focus_item=0)
        entry_box = urwid.Columns([labels, self.fields])
        self.display = urwid.Filler(entry_box,  valign='middle')
        decorate = urwid.LineBox(self.display)
        super().__init__(decorate)

        self.focusable_widgets = (w for w in itertools.cycle((
            ((self.fields, 1),),
            ((self.fields, 2), (self.buttons, 1)),
            ((self.fields, 2), (self.buttons, 0)),
            ((self.fields, 0),)
            )))

        urwid.connect_signal(self.login_button, 'click', self.attempt_login)
        urwid.connect_signal(self.quit_button, 'click', self.quit)
        self.pubpen.subscribe('user.login_success', self.handle_login_success)
        self.pubpen.subscribe('user.login_failure', self.handle_login_failure)

#    def selectable(self):
#        # Decoration widgets like LineBox override selectable() so we need to
#        # use an actual method
#        return True
#
    def logged_in(self, username):
        urwid.emit_signal(self, 'logged_in')

    def reset(self):
        self.username.set_edit_text('')
        self.password.set_edit_text('')
        self.fields.focus_position = 0

    def attempt_login(self, *args):
        self.pubpen.publish('action.user.login_attempt', self.username.get_text()[0], self.password.get_text()[0])

    def quit(self, button):
        raise urwid.ExitMainLoop()

    def handle_login_success(self, username):
        self.reset()
        self.logged_in(username)

    def handle_login_failure(self, username):
        self.reset()


    def keypress(self, size, key):
        super().keypress(size, key)
        if key == 'enter':
            self.attempt_login()
            return
        elif key == 'tab':
            focus_paths = next(self.focusable_widgets)
            for widget, position in focus_paths:
                widget.focus_position = position
            return
        return key

