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

from itertools import chain

from django.forms import widgets
from django.forms.util import flatatt
from django.template.loader import render_to_string
from django.utils.encoding import force_unicode, force_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

class AmaraLanguageSelectMixin(object):
    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        if attrs is None:
            attrs = {}
        if isinstance(value, basestring):
            # single-select
            attrs['data-initial'] = value
        else:
            # multi-select
            attrs['data-initial'] = ':'.join(value)
        return super(AmaraLanguageSelectMixin, self).render(
            name, value, attrs, choices)

    def render_options(self, choices, selected_choices):
        # The JS code populates the options
        return ''

class AmaraLanguageSelect(AmaraLanguageSelectMixin, widgets.Select):
    pass

class AmaraLanguageSelectMultiple(AmaraLanguageSelectMixin,
                                  widgets.SelectMultiple):
    pass

class AmaraRadioSelect(widgets.RadioSelect):
    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        choices = list(chain(self.choices, choices))
        output = [u'<ul>']
        for i, choice in enumerate(choices):
            input_id = '{}_{}'.format(attrs['id'], i)
            output.extend([
                u'<li><div class="radio">',
                self.render_input(name, value, choice, input_id),
                self.render_label(name, value, choice, input_id),
                u'</div></li>',
            ])
        output.append(u'</ul>')
        return mark_safe(u''.join(output))

    def render_input(self, name, value, choice, input_id):
        attrs = {
            'id': input_id,
            'type': 'radio',
            'name': name,
            'value': force_unicode(choice[0]),
        }
        if choice[0] == value:
            attrs['checked'] = 'checked'
        return u'<input{}>'.format(flatatt(attrs))

    def render_label(self, name, value, choice, input_id):
        return u'<label for="{}"><span></span>{}</label>'.format(
            input_id, force_unicode(choice[1]))

class SearchBar(widgets.TextInput):
    def render(self, name, value, attrs=None):
        input = super(SearchBar, self).render(name, value, attrs)
        return mark_safe(u'<div class="searchbar">'
                         '<label class="sr-only">Search</label>'
                         '{}'
                         '</div>'.format(input))

class AmaraFileInput(widgets.FileInput):
    template_name = "widget/file_input.html"
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            final_attrs['value'] = force_text(self._format_value(value))
        return mark_safe(render_to_string(self.template_name, dictionary=final_attrs))

class AmaraClearableFileInput(widgets.ClearableFileInput):
    template_name = "widget/clearable_file_input.html"
    def render(self, name, value, attrs=None):
        context = {
                'initial_text': self.initial_text,
                'input_text': self.input_text,
                'clear_checkbox_label': self.clear_checkbox_label,
        }
        if value is None:
            value = ''
        context.update(self.build_attrs(attrs, type=self.input_type, name=name))
        if value != '':
            context['value'] = force_text(self._format_value(value))

        # if is_initial
        if bool(value and hasattr(value, 'url')):
            # context.update(self.get_template_substitution_values(value))
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                context['checkbox_name'] = conditional_escape(checkbox_name)
                context['checkbox_id'] = conditional_escape(checkbox_id)

        return mark_safe(render_to_string(self.template_name, dictionary=context))

__all__ = [
    'AmaraRadioSelect', 'SearchBar', 'AmaraFileInput', 'AmaraClearableFileInput',
]
