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
""" Handle the display of Markets and Commodities"""

from collections import OrderedDict
from abc import abstractmethod
from functools import partial

import attr
import urwid

from .abcwidget import ABCWidget
from .indexed_menu import IndexedMenuButton, IndexedMenuEnumerator
from .numbers import format_number
from .sideless_linebox import SidelessLineBox


@attr.s
class CatalogColumn:
    """Describes a column in the catalog."""
    title = attr.ib(validator=attr.validators.instance_of(str))
    space = attr.ib(validator=attr.validators.instance_of(int))
    widget_list = attr.ib(validator=attr.validators.instance_of(urwid.ListWalker),
            default=attr.Factory(lambda: urwid.SimpleFocusListWalker([])))
    data_map = attr.ib(validator=attr.validators.instance_of(OrderedDict),
                       default=attr.Factory(OrderedDict))
    money = attr.ib(validator=attr.validators.instance_of(bool),
                    default=False)


class CommodityCatalog(urwid.WidgetWrap, metaclass=ABCWidget):
    """Display a catalog of commodities to buy and sell"""
    _selectable = True

    """
    Must have a signals attribute that is a list containing at least two urwid signal names.

    (1) The signal to close the display
    (2) The signal to open an orderdialog

    These are referenced by offset into the list so it's important to keep
    these in order.  Other widgets interested in these two events may
    depend upon the order they appear in the signals list.  No other
    signals in the list may be referenced by their offset.  If the widget
    implements more urwid signals, define them afterwards.  Example::

        signals = ['close_market_display', 'open_order_dialog']

    .. warn:: Different CommodityCatalog implementations **must not**
        share the same signal names.

    .. note: This may be implemented as a **class** attribute rather than
        a property
    """

    @abstractmethod
    def __init__(self, pubpen, order_info_signal, primary_title='Commodity',
                 auxiliary_cols=None, price_col_idx=0):
        """
        CommodityCatalogs give the information needed to purchase or sell a commodity

        :arg pubpen: PubPen to use to signal events
        :arg order_info_signal: The signal to publish when the user is ready
            to fill out an order
        :kwarg primary_title: The title of the primary column.  The primary
            column holds the name of the commodity being sold and UI to tell
            the user what key to press to activate that column.
        :kwarg auxiliary_cols: List of other columns to display in addition to
            the column naming the commodity.  The default is to have a column
            for the price of the commodity.
        :kwarg price_col_idx: Offset into the list for the column listing the
            price.
        """
        self.pubpen = pubpen
        self.order_info_signal = order_info_signal
        self.location = None
        self.keypress_map = IndexedMenuEnumerator()
        self._market_query_sub_id = None

        # Primary column -- names the commodity and will be formatted to
        # allow hotkeys to select it
        self.commodity_col = CatalogColumn(primary_title, -1)

        # All other columns -- implementations will likely add to this.
        # Helper methods will iterate the columns to update things like focus
        # and keeping the data in the correct order with respect to the
        # commodity_col
        if auxiliary_cols is None:
            self.auxiliary_cols = [CatalogColumn('Price', 13, money=True), ]

            #
            # Indexes to special columns
            #
            # implementations may have handlers that update specific columns.
            # implementations need to store indexes to the columns so handlers
            # know where the columns they care about exist
            #
            self.price_col_idx = 0
        else:
            self.auxiliary_cols = auxiliary_cols
            self.price_col_idx = price_col_idx

        #
        # Set up the widgets
        #
        self.commodity = urwid.ListBox(self.commodity_col.widget_list)
        auxiliaries = []
        for cat_col in self.auxiliary_cols:
            auxiliaries.append(urwid.ListBox(cat_col.widget_list))
            auxiliaries[-1]._selectable = False  #pylint: disable=protected-access

        ui_columns = []
        ui_columns.append(('weight', 2, SidelessLineBox(self.commodity, title_align='left',
                                                        title=self.commodity_col.title,
                                                        lline=None, tlcorner='─', trcorner='─',
                                                        rline=None, blcorner='─', brcorner='─')))
        if len(self.auxiliary_cols) > 1:
            for cat_col_idx, cat_col in enumerate(self.auxiliary_cols[:-1]):
                ui_columns.append((cat_col.space,
                                   SidelessLineBox(auxiliaries[cat_col_idx], title_align='left',
                                                   title=cat_col.title,
                                                   lline=None, tlcorner='\u2500', blcorner='\u2500',
                                                   rline=None, trcorner='\u2500', brcorner='\u2500')))
        ui_columns.append((self.auxiliary_cols[-1].space,
                           SidelessLineBox(auxiliaries[-1], title_align='left',
                                           title=self.auxiliary_cols[-1].title,
                                           lline=None, tlcorner='\u2500', blcorner='\u2500',
                                           trcorner='\u252c', brcorner='\u2524')))

        self.market_display = urwid.Columns(ui_columns)

        super().__init__(self.market_display)

        #
        # Event handlers
        #
        self.pubpen.subscribe('ship.moved', self.handle_new_location)

    #
    # Helpers
    #
    def _highlight_focused_line(self):
        """Highlight the other portions of the commodity line that match with the commodity that's in focus"""
        try:
            idx = self.commodity.focus_position
        except IndexError:
            # The commodity list hasn't been refreshed yet.
            return

        for column in self.auxiliary_cols:
            # Reset the auxilliary lists
            for entry in column.widget_list:
                entry.set_attr_map({})

            # Highlight the appropriate line in each auxilliary list
            column.widget_list[idx].set_attr_map({None: 'reversed'})

    def _sync_data_maps(self):
        """
        Make sure the data_map for each column contains the same commodities
        in the same order as the main commodity map
        """
        for column in self.auxiliary_cols:
            new_commodity_map = OrderedDict()
            for commodity in self.commodity_col.data_map:
                new_value = column.data_map.get(commodity, None)
                if column.money:
                    if new_value is None:
                        new_value = 0
                else:
                    if new_value == 0:
                        new_value = None
                new_commodity_map[commodity] = new_value

            column.data_map = new_commodity_map

    def _sync_widget_lists(self):
        """
        Make sure the widget_list for each column contains the same
        commodities in the same order as the main commodity map
        """
        for column in self.auxiliary_cols:
            column.widget_list.clear()
            for commodity, value in column.data_map.items():
                if isinstance(value, int):
                    formatted_number = format_number(value)
                    if column.money:
                        button = IndexedMenuButton('${}'.format(formatted_number))
                    else:
                        button = IndexedMenuButton('{}'.format(formatted_number))
                else:
                    if value is None:
                        value = " "
                    button = IndexedMenuButton(value)
                urwid.connect_signal(button, 'click', partial(self.handle_commodity_select, commodity))
                column.widget_list.append(urwid.AttrMap(button, None))

    def _construct_commodity_list(self, commodities):
        """
        Display the commodities that can be bought and sold

        :arg commodities: iterable of commodity names sold at this market
        """
        for commodity in commodities:
            if commodity not in self.commodity_col.data_map:
                idx = self.keypress_map.set_next(commodity)

                button = IndexedMenuButton('({}) {}'.format(idx, commodity))
                self.commodity_col.widget_list.append(urwid.AttrMap(button, None, focus_map='reversed'))
                urwid.connect_signal(button, 'click', partial(self.handle_commodity_select, commodity))

                self.commodity_col.data_map[commodity] = len(self.commodity_col.widget_list) - 1

        self._sync_data_maps()
        self._sync_widget_lists()

        self._highlight_focused_line()

    #
    # Handle updates to the displayed info
    #
    def handle_market_info(self, prices):
        """
        Update the display with prices about all commodities in a market

        :arg prices: a dict mapping commodity names to prices
        """
        self.pubpen.unsubscribe(self._market_query_sub_id)
        self._market_query_sub_id = None
        for commodity, price in prices.items():
            self.auxiliary_cols[self.price_col_idx].data_map[commodity] = price
        self._construct_commodity_list(self.auxiliary_cols[self.price_col_idx].data_map)

    @abstractmethod
    def handle_new_location(self, new_location, *args):
        """
        Update the market display when the ship moves

        :arg new_location: The location the ship has moved to
        """
        self.location = new_location
        self.keypress_map.clear()
        self.commodity_col.widget_list.clear()
        self.commodity_col.data_map.clear()
        self.auxiliary_cols[self.price_col_idx].widget_list.clear()
        self.auxiliary_cols[self.price_col_idx].data_map.clear()

    def handle_commodity_select(self, commodity, *args):
        """
        Create a buy/sell dialog when the commodity is selected

        :arg commodity: The name of the commodity selected
        """
        # If the user selected the line via the mouse, then we need to sync
        # the highlighted line
        self.commodity.set_focus(self.commodity_col.data_map[commodity])
        self._highlight_focused_line()

        self.pubpen.publish('ui.urwid.order_info', commodity,
                            self.auxiliary_cols[self.price_col_idx].data_map[commodity],
                            self.location)
        urwid.emit_signal(self, self.signals[1])

    def keypress(self, size, key):
        """Handle all keyboard shortcuts for the market menu"""
        if key in self.keypress_map:
            # Open up the order dialog to buy sell this item
            commodity = self.keypress_map[key]
            self.pubpen.publish(self.order_info_signal, commodity,
                                self.auxiliary_cols_map[self.price_col_idx].data_map[commodity],
                                self.location)
            urwid.emit_signal(self, self.signals[1])
        elif key in ('left', 'right'):
            # Ignore keys that might move focus to a widget to the side
            return
        elif key in ('up', 'down', 'page up', 'page down'):
            # First let the children handle the change in focus...
            super().keypress(size, key)  #pylint: disable=not-callable
            # Then highlight the same entry in other columns
            self._highlight_focused_line()
        else:
            super().keypress(size, key)  #pylint: disable=not-callable
        return key
