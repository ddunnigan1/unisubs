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

import re
import textwrap

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from lxml import html

from auth.models import CustomUser as User
from messages.models import Message, SYSTEM_NOTIFICATION
from utils.enum import Enum
from utils.taskqueue import job

NotificationType = Enum('NotificationType', [
    ('ROLE_CHANGED', _('Role changed')),
    ('TEAM_INVITATION', _('Team invitation')),
    ('NEW_ACTIVE_ASSIGNMENT', _(u'New active assignment')),
    ('REQUEST_UPDATED', _(u'Request updated')),
    ('REQUEST_COMPLETED', _(u'Request completed by team')),
    ('REQUEST_SENDBACK', _(u'Request sent back to team')),
])

class Notification(object):
    """
    Base class for rendering the emails/messages for a notification
    """

    # Subclasses need to define these:

    notification_type = NotImplemented

    # Template to render the message.  Note that we use the same template to
    # render both the HTML and plaintext version of the message.  Here's the
    # system we use to make this work.
    #
    #     - Templates are written in simplified HTML
    #     - The only block-level tags supported are <p>, <ul>, and <li>
    #     - The only inline tags supported are <a>, <em>, and <strong>
    #     - For <a> tags make sure to use the {% universal_url %} tag or filter
    template_name = NotImplemented

    # set to True to always send email.  Set to False to never send email
    send_email = None

    def get_template_context(self):
        raise NotImplementedError()

    def subject(self):
        raise NotImplementedError()

    # Base class behavior
    def render_messages(self):
        """
        Renders a text and HTML version of the message body
        """
        source = render_to_string(self.template_name,
                                  self.get_template_context())
        html_message = render_to_string('messages/html-email.html', {
            'subject': self.subject(),
            'body': source,
        })
        text_message = TextEmailRenderer(source).text

        return text_message, html_message

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join('{}={}'.format(name, value)
                      for name, value in self.__dict__.items()))

def notify_users(notification, user_list):
    """
    Send notification messages to a list of users

    Arguments:
        notification: Instance of a Notification subclass
        user_list: list/iterable of CustomUser objects to notify

    """
    message, html_message = notification.render_messages()
    user_ids = [
        u.id if isinstance(u, User) else u
        for u in user_list
    ]
    do_notify_users.delay(notification.notification_type, user_ids,
                          notification.subject(), message, html_message,
                          notification.send_email)

def notify_user(notification, user):
    return notify_users(notification, [user])

@job
def do_notify_users(notification_type, user_ids, subject, message, html_message,
                    send_email):
    user_list = User.objects.filter(id__in=user_ids)
    for user in user_list:
        if not user.is_active:
            continue
        if should_send_email(user, send_email):
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                      [user.email], html_message=html_message)
        if user.notify_by_message:
            Message.objects.create(user=user, subject=subject,
                                   message_type=SYSTEM_NOTIFICATION,
                                   content=html_message, html_formatted=True)

def should_send_email(user, send_email):
    """
    Logic to decide if we should send an email to the user for notify_users()
    """
    return (user.email and
            (send_email == True or
             send_email is None and user.notify_by_email))

class TextEmailRenderer(object):
    """
    Handles converting the HTML emails to plaintext
    """

    def __init__(self, source):
        self.parts = []
        self.process_source(source)
        self.text = ''.join(self.parts)

    def process_source(self, source):
        tree = html.fragment_fromstring(source, create_parent=True)

        self.check_no_text(tree.text)
        for i, elt in enumerate(tree):
            if i > 0:
                self.parts.append('\n') # extra newline to separate paragraphs
            self.process_blocklevel(elt)

    def process_blocklevel(self, elt):
        self.check_no_text(elt.tail)

        if elt.tag == 'p':
            self.process_inline_text(elt)
            self.parts.append('\n')
        elif elt.tag == 'ul':
            self.process_list(elt)

    def process_inline_text(self, elt):
        inline_parts = []
        if elt.text:
            inline_parts.append(elt.text)
        for child in elt:
            if child.tag == 'a':
                inline_parts.append(self.format_link(child))
            else:
                raise ValueError(
                    "Don't know how to process inline {} "
                    "elements for the plaintext email".format(child.tag))
            if child.tail:
                inline_parts.append(child.tail)
        self.parts.append(textwrap.fill(
            ''.join(inline_parts), 70, break_long_words=False,
            break_on_hyphens=False))

    def process_list(self, elt):
        for child in elt:
            if child.tag == 'li':
                self.parts.append('  - ')
                self.process_inline_text(child)
                self.parts.append('\n')
            else:
                raise ValueError(
                    "Invalid ul child: {}".format(elt.tag))

    def format_link(self, elt):
        return '{} ({})'.format(elt.text, elt.get('href'))

    def check_no_text(self, text_or_tail):
        if text_or_tail and not text_or_tail.isspace():
            raise ValueError(
                "Can't process text outside <p> tags for the "
                "plaintext email: {}".format(text_or_tail))

__all__ = [
    'NotificationType', 'Notification', 'notify_users', 'do_notify_users',
]
