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

from __future__ import absolute_import

from django import template
from django.utils.safestring import mark_safe

import ui.siteheader
import ui.dates

register = template.Library()

@register.filter
def date(dt):
    return ui.dates.date(dt)

@register.filter
def elapsed_time(dt):
    return ui.dates.elapsed_time(dt)

@register.filter
def format_time(dt):
    return ui.dates.format_time(dt)

@register.simple_tag(takes_context=True)
def header_links(context):
    nav = context.get('nav')
    parts = []
    parts.append(u'<ul>')
    for tab in ui.siteheader.navlinks():
        if tab.name == nav:
            parts.append(u'<li class="active">{}</li>'.format(unicode(tab)))
        else:
            parts.append(u'<li>{}</li>'.format(tab))
    parts.append(u'</ul>')
    return u'\n'.join(parts)
