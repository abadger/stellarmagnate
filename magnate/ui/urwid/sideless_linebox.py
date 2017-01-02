# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Toshio Kuratomi
#
# The code in this file and this file alone is based on the urwid library by
# Ian Ward.  It is licensed the same as Urwid.  The terms and conditions are
# reproduced below:
#
# Urwid graphics widgets
#    Copyright (C) 2004-2011  Ian Ward
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Urwid web site: http://excess.org/urwid/

from urwid.widget import WidgetWrap, Divider, SolidFill, Text
from urwid.container import Pile, Columns
from urwid.decoration import WidgetDecoration

class SidelessLineBox(WidgetDecoration, WidgetWrap):

    def __init__(self, original_widget, title="", title_align="center",
                 tlcorner='┌', tline='─', lline='│',
                 trcorner='┐', blcorner='└', rline='│',
                 bline='─', brcorner='┘'):
        """
        Draw a line around original_widget.

        Use 'title' to set an initial title text with will be centered
        on top of the box.

        Use `title_align` to align the title to the 'left', 'right', or 'center'.
        The default is 'center'.

        You can also override the widgets used for the lines/corners:
            tline: top line
            bline: bottom line
            lline: left line
            rline: right line
            tlcorner: top left corner
            trcorner: top right corner
            blcorner: bottom left corner
            brcorner: bottom right corner

        .. note:: This differs from the vanilla urwid LineBox by discarding
            the a line if the middle of the line is set to either None or the
            empty string.
        """

        if tline:
            tline = Divider(tline)
        if bline:
            bline = Divider(bline)
        if lline:
            lline = SolidFill(lline)
        if rline:
            rline = SolidFill(rline)
        tlcorner, trcorner = Text(tlcorner), Text(trcorner)
        blcorner, brcorner = Text(blcorner), Text(brcorner)

        if not tline and title:
            raise ValueError('Cannot have a title when tline is unset')

        self.title_widget = Text(self.format_title(title))

        if tline:
            if title_align not in ('left', 'center', 'right'):
                raise ValueError('title_align must be one of "left", "right", or "center"')
            if title_align == 'left':
                tline_widgets = [('flow', self.title_widget), tline]
            else:
                tline_widgets = [tline, ('flow', self.title_widget)]
                if title_align == 'center':
                    tline_widgets.append(tline)
            self.tline_widget = Columns(tline_widgets)
            top = Columns([
                ('fixed', 1, tlcorner),
                self.tline_widget,
                ('fixed', 1, trcorner)
            ])

        else:
            self.tline_widget = None
            top = None

        middle_widgets = []
        if lline:
            middle_widgets.append(('fixed', 1, lline))
        middle_widgets.append(original_widget)
        focus_col = len(middle_widgets) - 1
        if rline:
            middle_widgets.append(('fixed', 1, rline))

        middle = Columns(middle_widgets,
                         box_columns=[0, 2],
                         focus_column=focus_col)

        if bline:
            bottom = Columns([
                ('fixed', 1, blcorner), bline, ('fixed', 1, brcorner)
            ])
        else:
            bottom = None

        pile_widgets = []
        if top:
            pile_widgets.append(('flow', top))
        pile_widgets.append(middle)
        focus_pos = len(pile_widgets) - 1
        if bottom:
            pile_widgets.append(('flow', bottom))
        pile = Pile(pile_widgets, focus_item=focus_pos)

        WidgetDecoration.__init__(self, original_widget)
        WidgetWrap.__init__(self, pile)

    def format_title(self, text):
        if len(text) > 0:
            return " %s " % text
        else:
            return ""

    def set_title(self, text):
        if not self.title_widget:
            raise ValueError('Cannot set title when tline is unset')
        self.title_widget.set_text(self.format_title(text))
        self.tline_widget._invalidate()
