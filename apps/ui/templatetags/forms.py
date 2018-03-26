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

from django import template
from django.template.loader import render_to_string
from django import forms

register = template.Library()

@register.filter
def render_field(field):
    return render_to_string('future/forms/field.html', {
        'field': field,
        'widget_type': calc_widget_type(field),
    })

@register.filter
def render_filter_field(field):
    return render_to_string('future/forms/filter-field.html', {
        'field': field,
        'widget_type': calc_widget_type(field),
    })

def calc_widget_type(field):
    if field.is_hidden:
        return 'hidden'
    try:
        widget = field.field.widget
    except StandardError:
        return 'default'
    if isinstance(widget, forms.RadioSelect):
        return 'radio'
    elif isinstance(widget, forms.SelectMultiple):
        return 'select-multiple'
    elif isinstance(widget, forms.Select):
        return 'select'
    elif isinstance(widget, forms.CheckboxInput):
        return 'checkbox'
    elif isinstance(widget, forms.Textarea):
        widget.attrs['class'] = 'form-control'
        return 'default'
    else:
        return 'default'
