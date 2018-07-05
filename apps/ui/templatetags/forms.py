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

from django import forms
from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe

from ui.forms import HelpTextList
from utils.text import fmt

register = template.Library()

@register.filter
def render_field(field):
    return render_to_string('future/forms/field.html', {
        'field': field,
        'widget_type': calc_widget_type(field),
        'no_help_block': isinstance(field.help_text, HelpTextList),
        'label': calc_label(field),
    })

@register.filter
def render_field_reverse_required(field):
    return render_to_string('future/forms/field.html', {
        'field': field,
        'widget_type': calc_widget_type(field),
        'no_help_block': isinstance(field.help_text, HelpTextList),
        'label': calc_label(field, reverse_required=True),
    })

@register.filter
def render_filter_field(field):
    return render_to_string('future/forms/filter-field.html', {
        'field': field,
        'widget_type': calc_widget_type(field),
        'label': field.label,
    })

@register.inclusion_tag('future/forms/button-field.html')
def button_field(field, button_label, button_class="cta"):
    return {
        'field': field,
        'widget_type': calc_widget_type(field),
        'no_help_block': isinstance(field.help_text, HelpTextList),
        'button_label': button_label,
        'button_class': button_class,
    }

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
        return 'default'
    else:
        return 'default'

def calc_label(field, reverse_required=False):
    if not field.label:
        return ''
    elif isinstance(field.field.widget, forms.CheckboxInput):
        return field.label
    elif not field.field.required and not reverse_required:
        return mark_safe(fmt(
            _('%(field_label)s <span class="fieldOptional">(optional)</span>'),
            field_label=field.label))
    elif field.field.required and reverse_required:
        return mark_safe(fmt(
            _('%(field_label)s <span class="fieldOptional">(required)</span>'),
            field_label=field.label))
    else:
        return field.label
