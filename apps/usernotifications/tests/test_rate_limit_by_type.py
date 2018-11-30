from datetime import datetime, timedelta

from usernotifications import notifications
from usernotifications.models import LastSentNotification
from utils.factories import *
from utils.test_utils import mock_now
from .test_notify_users import MockNotification

def test_rate_limit_by_type(mock_send_mail, check_mail_sent_to):
    user = UserFactory(notify_by_email=True)
    notifications.notify_users(MockNotification(), [user],
                               rate_limit_by_type=timedelta(hours=1))
    check_mail_sent_to(user)

    # The second notification before an hour goes by should not be sent
    notifications.notify_users(MockNotification(), [user],
                               rate_limit_by_type=timedelta(hours=1))
    assert not mock_send_mail.called

    # After an hour has passed, though notifications should go through again
    mock_now.increment(timedelta(hours=1, minutes=1))
    notifications.notify_users(MockNotification(), [user],
                               rate_limit_by_type=timedelta(hours=1))
    check_mail_sent_to(user)
