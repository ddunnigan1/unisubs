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
from ui.forms import AmaraImageField, DependentCheckboxField

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

class DependentCheckboxes(StyleguideForm):
    role = DependentCheckboxField(choices=(
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('any-team-member', 'Any Team Member'),
    ))

class ImageUpload(StyleguideForm):
    thumbnail = AmaraImageField(label='Image', preview_size=(169, 100),
                                help_text=('upload an image to test'))

    def setup_form(self):
        styleguide_data = self.get_styleguide_data()
        if styleguide_data.thumbnail:
            self.initial = {
                'thumbnail': styleguide_data.thumbnail
            }

    def save(self):
        styleguide_data = self.get_styleguide_data()
        styleguide_data.thumbnail = self.cleaned_data['thumbnail']
        styleguide_data.save()
