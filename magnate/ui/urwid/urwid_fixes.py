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
"""Bugfix and additional features for several urwid widgets"""

# Classes that we're monkeypatching
from urwid import Edit, LineBox

# Classes to implement these fixes
import urwid
from urwid import Columns, Divider, Pile, SolidFill, Text, WidgetDecoration, WidgetWrap
# To implement Edit and IntEdit
from urwid.widget import (CURSOR_DOWN, CURSOR_LEFT, CURSOR_RIGHT, CURSOR_UP,
                          CURSOR_MAX_LEFT, CURSOR_MAX_RIGHT,
                          LEFT, RIGHT, SPACE,
                          CompositeCanvas, EditError, calc_coords, calc_pos,
                          decompose_tagmarkup, is_wide_char,
                          move_next_char, move_prev_char, python3_repr,
                          remove_defaults, shift_line)

# These two get transformed by 2to3 when urwid is installed
unicode = str
long = int

# See https://github.com/urwid/urwid/pull/214/files
# for the actual changes to this class
class EditFix(urwid.Text):
    """
    Text editing widget implements cursor movement, text insertion and
    deletion.  A caption may prefix the editing area.  Uses text class
    for text layout.

    Users of this class may listen for ``"change"`` or ``"postchange"``
    events.  See :func:``connect_signal``.

    * ``"change"`` is sent just before the value of edit_text changes.
      It receives the new text as an argument.  Note that ``"change"`` cannot
      change the text in question as edit_text changes the text afterwards.
    * ``"postchange"`` is sent after the value of edit_text changes.
      It receives the old value of the text as an argument and thus is
      appropriate for changing the text.  It is possible for a ``"postchange"``
      event handler to get into a loop of changing the text and then being
      called when the event is re-emitted.  It is up to the event
      handler to guard against this case (for instance, by not changing the
      text if it is signaled for for text that it has already changed once).
    """
    # (this variable is picked up by the MetaSignals metaclass)
    signals = ["change", "postchange"]

    def valid_char(self, ch):
        """
        Filter for text that may be entered into this widget by the user

        :param ch: character to be inserted
        :type ch: bytes or unicode

        This implementation returns True for all printable characters.
        """
        return is_wide_char(ch,0) or (len(ch)==1 and ord(ch) >= 32)

    def selectable(self): return True

    def __init__(self, caption=u"", edit_text=u"", multiline=False,
            align=LEFT, wrap=SPACE, allow_tab=False,
            edit_pos=None, layout=None, mask=None):
        """
        :param caption: markup for caption preceeding edit_text, see
                        :class:`Text` for description of text markup.
        :type caption: text markup
        :param edit_text: initial text for editing, type (bytes or unicode)
                          must match the text in the caption
        :type edit_text: bytes or unicode
        :param multiline: True: 'enter' inserts newline  False: return it
        :type multiline: bool
        :param align: typically 'left', 'center' or 'right'
        :type align: text alignment mode
        :param wrap: typically 'space', 'any' or 'clip'
        :type wrap: text wrapping mode
        :param allow_tab: True: 'tab' inserts 1-8 spaces  False: return it
        :type allow_tab: bool
        :param edit_pos: initial position for cursor, None:end of edit_text
        :type edit_pos: int
        :param layout: defaults to a shared :class:`StandardTextLayout` instance
        :type layout: text layout instance
        :param mask: hide text entered with this character, None:disable mask
        :type mask: bytes or unicode

        >>> Edit()
        <Edit selectable flow widget '' edit_pos=0>
        >>> Edit(u"Y/n? ", u"yes")
        <Edit selectable flow widget 'yes' caption='Y/n? ' edit_pos=3>
        >>> Edit(u"Name ", u"Smith", edit_pos=1)
        <Edit selectable flow widget 'Smith' caption='Name ' edit_pos=1>
        >>> Edit(u"", u"3.14", align='right')
        <Edit selectable flow widget '3.14' align='right' edit_pos=4>
        """

        self.__super.__init__("", align, wrap, layout)
        self.multiline = multiline
        self.allow_tab = allow_tab
        self._edit_pos = 0
        self.set_caption(caption)
        self._edit_text = ''
        self.set_edit_text(edit_text)
        if edit_pos is None:
            edit_pos = len(edit_text)
        self.set_edit_pos(edit_pos)
        self.set_mask(mask)
        self._shift_view_to_cursor = False

    def _repr_words(self):
        return self.__super._repr_words()[:-1] + [
            python3_repr(self._edit_text)] + [
            'caption=' + python3_repr(self._caption)] * bool(self._caption) + [
            'multiline'] * (self.multiline is True)

    def _repr_attrs(self):
        attrs = dict(self.__super._repr_attrs(),
            edit_pos=self._edit_pos)
        return remove_defaults(attrs, Edit.__init__)

    def get_text(self):
        """
        Returns ``(text, display attributes)``. See :meth:`Text.get_text`
        for details.

        Text returned includes the caption and edit_text, possibly masked.

        >>> Edit(u"What? ","oh, nothing.").get_text() # ... = u in Python 2
        (...'What? oh, nothing.', [])
        >>> Edit(('bright',u"user@host:~$ "),"ls").get_text()
        (...'user@host:~$ ls', [('bright', 13)])
        >>> Edit(u"password:", u"seekrit", mask=u"*").get_text()
        (...'password:*******', [])
        """

        if self._mask is None:
            return self._caption + self._edit_text, self._attrib
        else:
            return self._caption + (self._mask * len(self._edit_text)), self._attrib

    def set_text(self, markup):
        """
        Not supported by Edit widget.

        >>> Edit().set_text("test")
        Traceback (most recent call last):
        EditError: set_text() not supported.  Use set_caption() or set_edit_text() instead.
        """
        # FIXME: this smells. reimplement Edit as a WidgetWrap subclass to
        # clean this up

        # hack to let Text.__init__() work
        if not hasattr(self, '_text') and markup == "":
            self._text = None
            return

        raise EditError("set_text() not supported.  Use set_caption()"
            " or set_edit_text() instead.")

    def get_pref_col(self, size):
        """
        Return the preferred column for the cursor, or the
        current cursor x value.  May also return ``'left'`` or ``'right'``
        to indicate the leftmost or rightmost column available.

        This method is used internally and by other widgets when
        moving the cursor up or down between widgets so that the
        column selected is one that the user would expect.

        >>> size = (10,)
        >>> Edit().get_pref_col(size)
        0
        >>> e = Edit(u"", u"word")
        >>> e.get_pref_col(size)
        4
        >>> e.keypress(size, 'left')
        >>> e.get_pref_col(size)
        3
        >>> e.keypress(size, 'end')
        >>> e.get_pref_col(size)
        'right'
        >>> e = Edit(u"", u"2\\nwords")
        >>> e.keypress(size, 'left')
        >>> e.keypress(size, 'up')
        >>> e.get_pref_col(size)
        4
        >>> e.keypress(size, 'left')
        >>> e.get_pref_col(size)
        0
        """
        (maxcol,) = size
        pref_col, then_maxcol = self.pref_col_maxcol
        if then_maxcol != maxcol:
            return self.get_cursor_coords((maxcol,))[0]
        else:
            return pref_col

    def update_text(self):
        """
        No longer supported.

        >>> Edit().update_text()
        Traceback (most recent call last):
        EditError: update_text() has been removed.  Use set_caption() or set_edit_text() instead.
        """
        raise EditError("update_text() has been removed.  Use "
            "set_caption() or set_edit_text() instead.")

    def set_caption(self, caption):
        """
        Set the caption markup for this widget.

        :param caption: markup for caption preceeding edit_text, see
                        :meth:`Text.__init__` for description of text markup.

        >>> e = Edit("")
        >>> e.set_caption("cap1")
        >>> print e.caption
        cap1
        >>> e.set_caption(('bold', "cap2"))
        >>> print e.caption
        cap2
        >>> e.attrib
        [('bold', 4)]
        >>> e.caption = "cap3"  # not supported because caption stores text but set_caption() takes markup
        Traceback (most recent call last):
        AttributeError: can't set attribute
        """
        self._caption, self._attrib = decompose_tagmarkup(caption)
        self._invalidate()

    caption = property(lambda self:self._caption)

    def set_edit_pos(self, pos):
        """
        Set the cursor position with a self.edit_text offset.
        Clips pos to [0, len(edit_text)].

        :param pos: cursor position
        :type pos: int

        >>> e = Edit(u"", u"word")
        >>> e.edit_pos
        4
        >>> e.set_edit_pos(2)
        >>> e.edit_pos
        2
        >>> e.edit_pos = -1  # Urwid 0.9.9 or later
        >>> e.edit_pos
        0
        >>> e.edit_pos = 20
        >>> e.edit_pos
        4
        """
        if pos < 0:
            pos = 0
        if pos > len(self._edit_text):
            pos = len(self._edit_text)
        self.highlight = None
        self.pref_col_maxcol = None, None
        self._edit_pos = pos
        self._invalidate()

    edit_pos = property(lambda self:self._edit_pos, set_edit_pos)

    def set_mask(self, mask):
        """
        Set the character for masking text away.

        :param mask: hide text entered with this character, None:disable mask
        :type mask: bytes or unicode
        """

        self._mask = mask
        self._invalidate()

    def set_edit_text(self, text):
        """
        Set the edit text for this widget.

        :param text: text for editing, type (bytes or unicode)
                     must match the text in the caption
        :type text: bytes or unicode

        >>> e = Edit()
        >>> e.set_edit_text(u"yes")
        >>> print e.edit_text
        yes
        >>> e
        <Edit selectable flow widget 'yes' edit_pos=0>
        >>> e.edit_text = u"no"  # Urwid 0.9.9 or later
        >>> print e.edit_text
        no
        """
        text = self._normalize_to_caption(text)
        self.highlight = None
        self._emit("change", text)
        old_text = self._edit_text
        self._edit_text = text
        if self.edit_pos > len(text):
            self.edit_pos = len(text)
        self._emit("postchange", old_text)
        self._invalidate()

    def get_edit_text(self):
        """
        Return the edit text for this widget.

        >>> e = Edit(u"What? ", u"oh, nothing.")
        >>> print e.get_edit_text()
        oh, nothing.
        >>> print e.edit_text
        oh, nothing.
        """
        return self._edit_text

    edit_text = property(get_edit_text, set_edit_text, doc="""
        Read-only property returning the edit text for this widget.
        """)

    def insert_text(self, text):
        """
        Insert text at the cursor position and update cursor.
        This method is used by the keypress() method when inserting
        one or more characters into edit_text.

        :param text: text for inserting, type (bytes or unicode)
                     must match the text in the caption
        :type text: bytes or unicode

        >>> e = Edit(u"", u"42")
        >>> e.insert_text(u".5")
        >>> e
        <Edit selectable flow widget '42.5' edit_pos=4>
        >>> e.set_edit_pos(2)
        >>> e.insert_text(u"a")
        >>> print e.edit_text
        42a.5
        """
        text = self._normalize_to_caption(text)
        result_text, result_pos = self.insert_text_result(text)
        self.set_edit_text(result_text)
        self.set_edit_pos(result_pos)
        self.highlight = None

    def _normalize_to_caption(self, text):
        """
        Return text converted to the same type as self.caption
        (bytes or unicode)
        """
        tu = isinstance(text, unicode)
        cu = isinstance(self._caption, unicode)
        if tu == cu:
            return text
        if tu:
            return text.encode('ascii') # follow python2's implicit conversion
        return text.decode('ascii')

    def insert_text_result(self, text):
        """
        Return result of insert_text(text) without actually performing the
        insertion.  Handy for pre-validation.

        :param text: text for inserting, type (bytes or unicode)
                     must match the text in the caption
        :type text: bytes or unicode
        """

        # if there's highlighted text, it'll get replaced by the new text
        text = self._normalize_to_caption(text)
        if self.highlight:
            start, stop = self.highlight
            btext, etext = self.edit_text[:start], self.edit_text[stop:]
            result_text =  btext + etext
            result_pos = start
        else:
            result_text = self.edit_text
            result_pos = self.edit_pos

        try:
            result_text = (result_text[:result_pos] + text +
                result_text[result_pos:])
        except:
            assert 0, repr((self.edit_text, result_text, text))
        result_pos += len(text)
        return (result_text, result_pos)

    def keypress(self, size, key):
        """
        Handle editing keystrokes, return others.

        >>> e, size = Edit(), (20,)
        >>> e.keypress(size, 'x')
        >>> e.keypress(size, 'left')
        >>> e.keypress(size, '1')
        >>> print e.edit_text
        1x
        >>> e.keypress(size, 'backspace')
        >>> e.keypress(size, 'end')
        >>> e.keypress(size, '2')
        >>> print e.edit_text
        x2
        >>> e.keypress(size, 'shift f1')
        'shift f1'
        """
        (maxcol,) = size

        p = self.edit_pos
        if self.valid_char(key):
            if (isinstance(key, unicode) and not
                    isinstance(self._caption, unicode)):
                # screen is sending us unicode input, must be using utf-8
                # encoding because that's all we support, so convert it
                # to bytes to match our caption's type
                key = key.encode('utf-8')
            self.insert_text(key)

        elif key=="tab" and self.allow_tab:
            key = " "*(8-(self.edit_pos%8))
            self.insert_text(key)

        elif key=="enter" and self.multiline:
            key = "\n"
            self.insert_text(key)

        elif self._command_map[key] == CURSOR_LEFT:
            if p==0: return key
            p = move_prev_char(self.edit_text,0,p)
            self.set_edit_pos(p)

        elif self._command_map[key] == CURSOR_RIGHT:
            if p >= len(self.edit_text): return key
            p = move_next_char(self.edit_text,p,len(self.edit_text))
            self.set_edit_pos(p)

        elif self._command_map[key] in (CURSOR_UP, CURSOR_DOWN):
            self.highlight = None

            x,y = self.get_cursor_coords((maxcol,))
            pref_col = self.get_pref_col((maxcol,))
            assert pref_col is not None
            #if pref_col is None:
            #    pref_col = x

            if self._command_map[key] == CURSOR_UP: y -= 1
            else: y += 1

            if not self.move_cursor_to_coords((maxcol,),pref_col,y):
                return key

        elif key=="backspace":
            self.pref_col_maxcol = None, None
            if not self._delete_highlighted():
                if p == 0: return key
                p = move_prev_char(self.edit_text,0,p)
                self.set_edit_text( self.edit_text[:p] +
                    self.edit_text[self.edit_pos:] )
                self.set_edit_pos( p )

        elif key=="delete":
            self.pref_col_maxcol = None, None
            if not self._delete_highlighted():
                if p >= len(self.edit_text):
                    return key
                p = move_next_char(self.edit_text,p,len(self.edit_text))
                self.set_edit_text( self.edit_text[:self.edit_pos] +
                    self.edit_text[p:] )

        elif self._command_map[key] in (CURSOR_MAX_LEFT, CURSOR_MAX_RIGHT):
            self.highlight = None
            self.pref_col_maxcol = None, None

            x,y = self.get_cursor_coords((maxcol,))

            if self._command_map[key] == CURSOR_MAX_LEFT:
                self.move_cursor_to_coords((maxcol,), LEFT, y)
            else:
                self.move_cursor_to_coords((maxcol,), RIGHT, y)
            return

        else:
            # key wasn't handled
            return key

    def move_cursor_to_coords(self, size, x, y):
        """
        Set the cursor position with (x,y) coordinates.
        Returns True if move succeeded, False otherwise.

        >>> size = (10,)
        >>> e = Edit("","edit\\ntext")
        >>> e.move_cursor_to_coords(size, 5, 0)
        True
        >>> e.edit_pos
        4
        >>> e.move_cursor_to_coords(size, 5, 3)
        False
        >>> e.move_cursor_to_coords(size, 0, 1)
        True
        >>> e.edit_pos
        5
        """
        (maxcol,) = size
        trans = self.get_line_translation(maxcol)
        top_x, top_y = self.position_coords(maxcol, 0)
        if y < top_y or y >= len(trans):
            return False

        pos = calc_pos( self.get_text()[0], trans, x, y )
        e_pos = pos - len(self.caption)
        if e_pos < 0: e_pos = 0
        if e_pos > len(self.edit_text): e_pos = len(self.edit_text)
        self.edit_pos = e_pos
        self.pref_col_maxcol = x, maxcol
        self._invalidate()
        return True

    def mouse_event(self, size, event, button, x, y, focus):
        """
        Move the cursor to the location clicked for button 1.

        >>> size = (20,)
        >>> e = Edit("","words here")
        >>> e.mouse_event(size, 'mouse press', 1, 2, 0, True)
        True
        >>> e.edit_pos
        2
        """
        (maxcol,) = size
        if button==1:
            return self.move_cursor_to_coords( (maxcol,), x, y )


    def _delete_highlighted(self):
        """
        Delete all highlighted text and update cursor position, if any
        text is highlighted.
        """
        if not self.highlight: return
        start, stop = self.highlight
        btext, etext = self.edit_text[:start], self.edit_text[stop:]
        self.set_edit_text( btext + etext )
        self.edit_pos = start
        self.highlight = None
        return True


    def render(self, size, focus=False):
        """
        Render edit widget and return canvas.  Include cursor when in
        focus.

        >>> c = Edit("? ","yes").render((10,), focus=True)
        >>> c.text # ... = b in Python 3
        [...'? yes     ']
        >>> c.cursor
        (5, 0)
        """
        (maxcol,) = size
        self._shift_view_to_cursor = bool(focus)

        canv = Text.render(self,(maxcol,))
        if focus:
            canv = CompositeCanvas(canv)
            canv.cursor = self.get_cursor_coords((maxcol,))

        # .. will need to FIXME if I want highlight to work again
        #if self.highlight:
        #    hstart, hstop = self.highlight_coords()
        #    d.coords['highlight'] = [ hstart, hstop ]
        return canv


    def get_line_translation(self, maxcol, ta=None ):
        trans = Text.get_line_translation(self, maxcol, ta)
        if not self._shift_view_to_cursor:
            return trans

        text, ignore = self.get_text()
        x,y = calc_coords( text, trans,
            self.edit_pos + len(self.caption) )
        if x < 0:
            return ( trans[:y]
                + [shift_line(trans[y],-x)]
                + trans[y+1:] )
        elif x >= maxcol:
            return ( trans[:y]
                + [shift_line(trans[y],-(x-maxcol+1))]
                + trans[y+1:] )
        return trans


    def get_cursor_coords(self, size):
        """
        Return the (*x*, *y*) coordinates of cursor within widget.

        >>> Edit("? ","yes").get_cursor_coords((10,))
        (5, 0)
        """
        (maxcol,) = size

        self._shift_view_to_cursor = True
        return self.position_coords(maxcol,self.edit_pos)


    def position_coords(self,maxcol,pos):
        """
        Return (*x*, *y*) coordinates for an offset into self.edit_text.
        """

        p = pos + len(self.caption)
        trans = self.get_line_translation(maxcol)
        x,y = calc_coords(self.get_text()[0], trans,p)
        return x,y


class IntEditFix(EditFix):
    """Edit widget for integer values"""

    def valid_char(self, ch):
        """
        Return true for decimal digits.
        """
        return len(ch)==1 and ch in "0123456789"

    def __init__(self,caption="",default=None):
        """
        caption -- caption markup
        default -- default edit value

        >>> IntEdit(u"", 42)
        <IntEdit selectable flow widget '42' edit_pos=2>
        """
        if default is not None: val = str(default)
        else: val = ""
        self.__super.__init__(caption,val)

    def keypress(self, size, key):
        """
        Handle editing keystrokes.  Remove leading zeros.

        >>> e, size = IntEdit(u"", 5002), (10,)
        >>> e.keypress(size, 'home')
        >>> e.keypress(size, 'delete')
        >>> print e.edit_text
        002
        >>> e.keypress(size, 'end')
        >>> print e.edit_text
        2
        """
        (maxcol,) = size
        unhandled = Edit.keypress(self,(maxcol,),key)

        if not unhandled:
        # trim leading zeros
            while self.edit_pos > 0 and self.edit_text[:1] == "0":
                self.set_edit_pos( self.edit_pos - 1)
                self.set_edit_text(self.edit_text[1:])

        return unhandled

    def value(self):
        """
        Return the numeric value of self.edit_text.

        >>> e, size = IntEdit(), (10,)
        >>> e.keypress(size, '5')
        >>> e.keypress(size, '1')
        >>> e.value() == 51
        True
        """
        if self.edit_text:
            return long(self.edit_text)
        else:
            return 0


# LineBox changes to specify title alignment and go borderless
# https://github.com/urwid/urwid/pull/215
def lb__init__(self, original_widget, title="", title_align="center",
               tlcorner=u'┌', tline=u'─', lline=u'│',
               trcorner=u'┐', blcorner=u'└', rline=u'│',
               bline=u'─', brcorner=u'┘'):
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

        If empty string is specified for one of the lines/corners, then no
        character will be output there.  This allows for seamless use of
        adjoining LineBoxes.
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
            raise ValueError('Cannot have a title when tline is empty string')

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
                box_columns=[0, 2], focus_column=focus_col)

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

def lb_set_title(self, text):
    if not self.title_widget:
        raise ValueError('Cannot set title when tline is unset')
    self.title_widget.set_text(self.format_title(text))
    self.tline_widget._invalidate()


LineBox.__init__ = lb__init__
LineBox.set_title = lb_set_title
