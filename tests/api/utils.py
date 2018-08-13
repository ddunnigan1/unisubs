# Amara, universalsubtitles.org
#
# Copyright (C) 2015 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program.  If not, see http://www.gnu.org/licenses/agpl-3.0.html.

from django.utils import timezone
from rest_framework.test import APIRequestFactory
from rest_framework.reverse import reverse
import pytz

def format_datetime_field(datetime):
    if datetime is None:
        return None
    tz = timezone.get_default_timezone()
    isoformat = tz.localize(datetime).astimezone(pytz.utc).isoformat()
    return isoformat.replace('+00:00', 'Z')

def format_datetime_field_as_date(datetime):
    if datetime is None:
        return None
    return datetime.date().isoformat()

def user_field_data(user):
    if user:
        return {
            'username': user.username,
            'id': user.secure_id(),
            'uri': reverse('api:users-detail', kwargs={
                'identifier': 'id$' + user.secure_id(),
            }, request=APIRequestFactory().get('/')),
        }
    else:
        return None
