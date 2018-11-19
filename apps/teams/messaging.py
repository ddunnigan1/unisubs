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

"""
teams.messaging -- Handles formatting team messages to the user

This module takes the various localized messages settings and uses them to
format messages to the user.  There are 2 cases here:

  - If we're rendering a request, then we look for a message that matches the
    language we're rendering the requset in.

  - If we're sending the user a notification email, we don't actually have a
    great way to know what language they want it in.  So in this case, we find
    a message that match one of the user's languages and combine that with the
    default message
"""

from django.utils import translation
from django.utils.html import format_html_join, format_html
from django.utils.safestring import mark_safe

def format_message_for_request(team, setting_name):
    messages = {
        setting.language_code: setting.data
        for setting in team.settings.with_name(setting_name)
    }
    language_code = translation.get_language()
    if language_code in messages:
        return format_html(u'<p>{}</p>', messages[language_code])
    elif '' in messages:
        return format_html(u'<p>{}</p>', messages[''])
    else:
        return ''

def format_message_for_notification(team, user, setting_name,
                                    old_format=False):
    messages = {
        setting.language_code: setting.data
        for setting in team.settings.with_name(setting_name)
    }
    parts = []
    # get the default message
    if '' in messages:
        parts.append(messages[''])
    # try to get one localized message to combine with the default
    for language_code in user.get_languages():
        if language_code in messages:
            parts.append(messages[language_code])
            break
    if parts:
        if old_format:
            return u'\n\n----------------\n\n'.join(parts)
        else:
            return format_html_join(mark_safe(u'<hr>'), u'<p>{}</p>',
                                    ((message,) for message in parts))
    else:
        return ''
