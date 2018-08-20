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

from django.core.files import File
from django.forms import widgets
from django.forms.util import flatatt
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import force_unicode, force_text
from django.utils.html import (conditional_escape, format_html,
                               format_html_join)
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from utils import datauri
from utils.amazon.fields import S3ImageFieldFile

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

class AmaraProjectSelectMultiple(widgets.SelectMultiple):
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
        return (u'<label for="{}"><span class="radio-icon"></span>'
                '{}</label>'.format(input_id, force_unicode(choice[1])))

class SearchBar(widgets.TextInput):
    def render(self, name, value, attrs=None):
        input = super(SearchBar, self).render(name, value, attrs)
        return mark_safe(u'<div class="searchbar">'
                         '<label class="sr-only">{}</label>'
                         '{}'
                         '</div>'.format(_('Search'), input))

class AmaraFileInput(widgets.FileInput):
    template_name = "widget/file_input.html"
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        if value != '':
            final_attrs['value'] = force_text(self._format_value(value))
        return mark_safe(render_to_string(self.template_name, dictionary=final_attrs))

class UploadOrPasteWidget(widgets.TextInput):
    template_name = "future/forms/widgets/upload-or-paste.html"

    def render(self, name, value, attrs=None):
        context = {
            'name': name,
            'initial_text': '',
        }
        if isinstance(value, basestring):
            context['initial_text'] = value
        return mark_safe(render_to_string(self.template_name, context))

    def value_from_datadict(self, data, files, name):
        selector = data.get(name + '-selector')
        if selector == 'upload':
            return files.get(name + '-upload')
        else:
            return data.get(name + '-paste')

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

class DependentCheckboxes(widgets.Widget):
    def render(self, name, value, attrs=None, choices=()):
        choices = list(chain(self.choices, choices))

        checked = self.calc_checked(choices, value)
        choices_html = format_html_join(
            '\n',
            '<input type="checkbox" id="{0}-{3}" name="{0}" value="{1}" '
            '{4}><label for="{0}-{3}"> '
            '<span class="checkbox-icon"></span> {2}</label>',
            [
                (name, choice_value, choice_label, i,
                 ' checked' if choice_value in checked else '')
                for i, (choice_value, choice_label) in enumerate(choices)
            ])
        return format_html('<div class="dependentCheckboxes">{}</div>',
                           choices_html)

    def calc_checked(self, choices, value):
        # calculate which checkboxes should be checked
        checked = set()
        saw_checked = False
        for (choice_value, choice_label) in reversed(choices):
            if choice_value == value:
                saw_checked = True
            if saw_checked:
                checked.add(choice_value)
        return checked

    def value_from_datadict(self, data, files, name):
        if not isinstance(data, MultiValueDict):
            return data.get(name)
        selected_values = set(data.getlist(name))
        # find the first selected choice, going from right to left
        for value, label in reversed(self.choices):
            if value in selected_values:
                return value
        return None

class AmaraImageInput(widgets.FileInput):
    def __init__(self):
        super(AmaraImageInput, self).__init__()
        # default size, overwritten by AmaraImageField
        self.preview_size = (100, 100)

    def render(self, name, value, attrs=None):
        if isinstance(value, S3ImageFieldFile):
            thumb_url = value.thumb_url(*self.preview_size)
        elif isinstance(value, File):
            thumb_url = datauri.from_django_file(value)
        else:
            thumb_url = None
        return mark_safe(render_to_string('future/forms/widgets/image-input.html', {
            'thumb_url': thumb_url,
            'name': name,
            'preview_width': self.preview_size[0],
            'preview_height': self.preview_size[1],
        }))

__all__ = [
    'AmaraRadioSelect', 'SearchBar', 'AmaraFileInput',
    'AmaraClearableFileInput', 'UploadOrPasteWidget',
    'DependentCheckboxes', 'AmaraImageInput',
]
