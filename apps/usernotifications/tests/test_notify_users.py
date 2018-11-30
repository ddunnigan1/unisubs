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

from lxml import etree
import mock
import re

from usernotifications import notifications
from messages.models import Message
from utils.factories import *

class MockNotification(notifications.Notification):
    notification_type = notifications.NotificationType.ROLE_CHANGED
    template_name = 'tests/test-message.html'

    def subject(self):
        return 'Test subject'

    def get_template_context(self):
        return {}

    def __eq__(self, other):
        return isinstance(other, MockNotification)

def test_should_send_email():
    # notify_by_email flag set
    assert notifications.should_send_email(
        UserFactory(notify_by_email=True), None)

    # notify_by_email flag set, but no email set
    assert not notifications.should_send_email(
        UserFactory(notify_by_email=True, email=''), None)

    # notify_by_email flag unset
    assert not notifications.should_send_email(
        UserFactory(notify_by_email=False), None)

    # notify_by_email flag unset, but send_email flag set
    assert notifications.should_send_email(
        UserFactory(notify_by_email=False), True)

    # notify_by_email flag set, but send_email flag set to false
    assert not notifications.should_send_email(
        UserFactory(notify_by_email=True), False)

def test_text_rendering(mock_send_mail):
    user = UserFactory(notify_by_email=True)
    notifications.notify_users(MockNotification(), [user])
    text = mock_send_mail.call_args[0][1]
    assert text == """\
Here's a link: Home (https://test.amara.org/)

Here's a table:

  - one
  - two

Here's a paragraph with a really really really really really really
really really really really really really really really really long
line.
"""

def test_message():
    user = UserFactory(notify_by_message=True)
    notifications.notify_users(MockNotification(), [user])
    # test that we send an message
    assert Message.objects.for_user(user).count() == 1
    last_message = Message.objects.for_user(user).order_by('-id')[:1].get()
    assert last_message.subject == 'Test subject'

def test_notify_by_message_unset():
    user = UserFactory(notify_by_message=False)
    notifications.notify_users(MockNotification(), [user])
    # test that we don't send a message
    assert Message.objects.for_user(user).count() == 0

def test_inactive_user(mock_send_mail):
    user = UserFactory(notify_by_message=True, notify_by_email=True,
                       is_active=False)
    notifications.notify_users(MockNotification(), [user])
    # test that we don't send a message or an email
    assert Message.objects.for_user(user).count() == 0
    assert not mock_send_mail.called
