# Amara, universalsubtitles.org
#
# Copyright (C) 2016 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

"""ui.utils -- frontend-related classes

This module contains a few utility classes that's used by the views code.
"""

from __future__ import absolute_import
from copy import copy
from collections import deque
from urllib import urlencode

from collections import namedtuple
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from utils.text import fmt

class Link(object):
    def __init__(self, label, view_name, *args, **kwargs):
        self.label = label
        query = kwargs.pop('query', None)
        self.class_ = kwargs.pop('class_', None)
        if '/' in view_name or view_name == '#':
            # URL path passed in, don't try to reverse it
            self.url = view_name
        else:
            self.url = reverse(view_name, args=args, kwargs=kwargs)
        if query:
            self.url += '?' + urlencode(query)

    def __unicode__(self):
        if self.class_:
            return format_html(u'<a href="{}" class="{}">{}</a>', self.url,
                               self.class_, self.label)
        else:
            return format_html(u'<a href="{}">{}</a>', self.url, self.label)

    def active(self):
        if self.class_:
            class_ = self.class_ + ' active'
        else:
            class_ = 'active'
        return self.clone(class_=class_)

    def clone(self, **new_attrs):
        rv = copy(self)
        rv.__dict__.update(new_attrs)
        return rv

    def __eq__(self, other):
        return (type(self) == type(other) and
                self.label == other.label and
                self.url == other.url)

class AjaxLink(Link):
    def __init__(self, label, **query_params):
        # All of our ajax links hit the current page, adding some query
        # parameters, so this constructor is optimized for that use.
        self.label = label
        self.url = '?' + urlencode(query_params)

    def __unicode__(self):
        return format_html(u'<a class="ajaxLink" data-href="{}">{}</a>', self.url, self.label)

class CTA(Link):
    def __init__(self, label, icon, view_name, block=False,
                 disabled=False, tooltip='', *args, **kwargs):
        super(CTA, self).__init__(label, view_name, *args, **kwargs)
        self.disabled = disabled
        self.icon = icon
        self.block = block
        self.tooltip = tooltip

    def __unicode__(self):
        return self.render()

    def as_block(self):
        return self.render(block=True)

    def render(self, block=False):
        tooltip_element = u'<span data-toggle="tooltip" data-placement="top" title="{}">{}</span>'
        link_element = u'<a href="{}" class="{}"><i class="icon {}"></i> {}</a>'
        css_class = "button"
        if self.disabled:
            css_class += " disabled"
        else:
            css_class += " cta"
        if block:
            css_class += " block"
        link = link_element.format(self.url, css_class, self.icon, self.label)
        if len(self.tooltip) > 0:
            link = tooltip_element.format(self.tooltip, link)
        return mark_safe(link)

    def __eq__(self, other):
        return (isinstance(other, Link) and
                self.label == other.label and
                self.icon == other.icon and
                self.url == other.url)

class Tab(Link):
    def __init__(self, name, label, view_name, *args, **kwargs):
        self.name = name
        super(Tab, self).__init__(label, view_name, *args, **kwargs)

    def __eq__(self, other):
        return (isinstance(other, Tab) and
                self.name == other.name and
                self.label == other.label and
                self.url == other.url)

class SectionWithCount(list):
    """Section that contains a list of things with a count in the header
    """
    header_template = _('%(header)s <span class="count">(%(count)s)</span>')
    def __init__(self, header_text):
        self.header_text = header_text

    def header(self):
        return mark_safe(fmt(self.header_template, header=self.header_text,
                             count=len(self)))

class ContextMenu(object):
    """Context menu

    Each child of ContextMenu should be a Link or MenuSeparator item
    """
    def __init__(self, initial_items=None):
        self.items = deque()
        if initial_items:
            self.extend(initial_items)

    def append(self, item):
        self.items.append(item)

    def extend(self, items):
        self.items.extend(items)

    def prepend(self, item):
        self.items.appendleft(item)

    def prepend_list(self, items):
        self.items.extendleft(reversed(items))

    def __unicode__(self):
        output = []
        output.append(u'<div class="context-menu">')
        output.append(u'<a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false"><span class="caret"></span></a>')
        output.append(u'<ul class="dropdown-menu">')
        for item in self.items:
            if isinstance(item, MenuSeparator):
                output.append(u'<li class="divider"></li>')
            else:
                output.append(u'<li>{}<li>'.format(unicode(item)))
        output.append(u'</ul></div>')
        return mark_safe(u'\n'.join(output))

class MenuSeparator(object):
    """Display a line to separate items in a ContextMenu."""

__all__ = [
    'Link', 'AjaxLink', 'CTA', 'Tab', 'SectionWithCount', 'ContextMenu',
    'MenuSeparator',
]
