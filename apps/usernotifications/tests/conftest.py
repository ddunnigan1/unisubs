from datetime import datetime

import mock
import pytest

from utils.test_utils import mock_now

@pytest.fixture(autouse=True)
def mock_send_mail(monkeypatch):
    mock_send_mail = mock.Mock()
    with mock.patch('usernotifications.notifications.send_mail',
                    mock_send_mail):
        yield mock_send_mail

@pytest.fixture(name='check_mail_sent_to')
def check_mail_sent_to_fixture(mock_send_mail):
    def check_mail_sent_to(user, reset=True):
        assert mock_send_mail.called
        assert mock_send_mail.call_args == mock.call(
            mock.ANY, mock.ANY, mock.ANY, [user.email], html_message=mock.ANY)
        if reset:
            mock_send_mail.reset_mock()
    return check_mail_sent_to

@pytest.fixture(autouse=True)
def setup_settings(settings):
    settings.DEFAULT_FROM_EMAIL = 'test@example.com'
    settings.HOSTNAME = 'test.amara.org'
    settings.DEFAULT_PROTOCOL  = 'https'

@pytest.fixture(autouse=True)
def set_now():
    mock_now.set(2018, 1, 1)
