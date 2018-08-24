# Amara, universalsubtitles.org
#
# Copyright (C) 2018 Participatory Culture Foundation
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

from auth.models import get_amara_anonymous_user
from styleguide.models import StyleguideData
from ui.forms import AmaraImageField, AmaraChoiceField, SwitchInput

class StyleguideForm(forms.Form):
    def __init__(self, request, **kwargs):
        self.user = request.user
        if self.user.is_anonymous():
            self.user = get_amara_anonymous_user()
        super(StyleguideForm, self).__init__(**kwargs)
        self.setup_form()

    # override these in the subclasses to customize form handling
    def setup_form(self):
        pass

    def save(self):
        pass

    def get_styleguide_data(self):
        try:
            return StyleguideData.objects.get(user=self.user)
        except StyleguideData.DoesNotExist:
            return StyleguideData(user=self.user)

class SwitchForm(StyleguideForm):
    choice = forms.BooleanField(label='Visibility', required=False,
                                widget=SwitchInput('Public', 'Private'))
    inline_choice = forms.BooleanField(
        label='Inline Example', required=False,
        widget=SwitchInput('ON', 'OFF', inline=True))

class MultiFieldForm(StyleguideForm):
    animal_color = AmaraChoiceField(choices=[
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('yellow', 'Yellow'),
    ], label='Color')
    animal_species = AmaraChoiceField(choices=[
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('horse', 'Horse'),
    ], label='Species')

    role_admin = forms.BooleanField(label='Admin', required=False,
                                    initial=True)
    role_manager = forms.BooleanField(label='Manager', required=False)
    role_any = forms.BooleanField(label='Any Team Member', required=False)

    subtitles_public = forms.BooleanField(
        label='Completed', required=False, initial=True,
        widget=SwitchInput('Public', 'Private'))
    drafts_public = forms.BooleanField(
        label='Drafts', required=False,
        widget=SwitchInput('Public', 'Private'))

    translate_time_limit = forms.CharField(label='Translate', initial=2,
                                           widget=forms.NumberInput)
    review_time_limit = forms.CharField(label='Review', initial=1,
                                        widget=forms.NumberInput)
    approval_time_limit = forms.CharField(label='Approval', initial=1,
                                          widget=forms.NumberInput)

    def clean(self):
        if (self.cleaned_data.get('animal_color') == 'yellow' and
                self.cleaned_data.get('animal_species') == 'dog'):
            self.add_error('animal_species', "Dog's can't be yellow!")

class ImageUpload(StyleguideForm):
    thumbnail = AmaraImageField(label='Image', preview_size=(169, 100),
                                help_text=('upload an image to test'),
                                required=False)
    def setup_form(self):
        styleguide_data = self.get_styleguide_data()
        if styleguide_data.thumbnail:
            self.initial = {
                'thumbnail': styleguide_data.thumbnail
            }

    def save(self):
        styleguide_data = self.get_styleguide_data()
        if self.cleaned_data['thumbnail'] == False:
            styleguide_data.thumbnail = None
        else:
            styleguide_data.thumbnail = self.cleaned_data['thumbnail']
        styleguide_data.save()
