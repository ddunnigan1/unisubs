# Amara, universalsubtitles.org
#
# Copyright (C) 2013 Participatory Culture Foundation
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
import cgi
from textwrap import wrap
from django import template
from django.template.loader import render_to_string
from django.utils.translation import get_language

from messages.models import Message

register = template.Library()

@register.simple_tag(takes_context=True)
def messages(context, futureui=False):
    user = context['user']
    request = context['request']
    hidden_message_id = request.COOKIES.get(Message.hide_cookie_name)
    if not user.is_authenticated():
        return ''
    if hidden_message_id == '':
        hidden_message_id = None

    if futureui:
        cache_key = 'messages-future-{}'.format(get_language())
        template_name = 'future/messages.html'
    else:
        cache_key = 'messages-{}'.format(get_language())
        template_name = 'messages/_messages.html'

    cached = user.cache.get(cache_key)
    if isinstance(cached, tuple) and cached[0] == hidden_message_id:
        return cached[1]

    last_unread = user.last_unread_message_id(hidden_message_id)
    if last_unread < hidden_message_id:
        last_unread = ''
    count = user.unread_messages_count(hidden_message_id)
    
    content = render_to_string(template_name,  {
        'msg_count': count,
        'last_unread': last_unread,
        'cookie_name': Message.hide_cookie_name
    })
    user.cache.set(cache_key, (hidden_message_id, content), 30 * 60)
    return content

@register.simple_tag(takes_context=True)
def futureui_messages(context):
    return messages(context, futureui=True)

@register.filter
def encode_html_email(message):
    return "<br/>".join(
        map(
            lambda x: cgi.escape("\n".join(wrap(x, 40, break_long_words=False))).encode('ascii', 'xmlcharrefreplace'),
            message.split("\n")
        ))
