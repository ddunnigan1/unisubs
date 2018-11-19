from django.utils import translation
import pytest

from teams import messaging
from teams.models import Setting
from utils.factories import *

@pytest.fixture(name='team')
def team_fixture():
    team = TeamFactory()
    team.settings.create(
        team=team,
        key=Setting.KEY_IDS['messages_joins'],
        data='Hello')
    team.settings.create(
        team=team,
        key=Setting.KEY_IDS['messages_joins'],
        language_code='es', data='Hola')
    team.settings.create(
        team=team,
        key=Setting.KEY_IDS['messages_joins'],
        language_code='ja', data='Konichiwa')
    team.settings.create(
        team=team,
        key=Setting.KEY_IDS['messages_joins'],
        language_code='fr', data='Bonjour')
    return team

def test_format_message_for_notification(team):
    # format_message_for_notification should combine the unlocalized message
    # with all localized messages.  This is because we don't have a good way
    # to know which one the user prefers
    user = UserFactory(languages=['en', 'es', 'ja'])
    message = messaging.format_message_for_notification(
        team, user, 'messages_joins')
    assert message == '<p>Hello</p><hr><p>Hola</p>'

def test_format_message_for_notification_no_matches(team):
    # If none of the user languages matches, we should just use the
    # unlocalized message
    user = UserFactory(languages=['en'])
    message = messaging.format_message_for_notification(
        team, user, 'messages_joins')
    assert message == '<p>Hello</p>'

def test_format_message_for_request(team):
    # localize_message_for_request should get use translation.get_language(),
    # which uses the same logic we use to localize the rest of the page.
    with translation.override('es'):
        message = messaging.format_message_for_request(
            team, 'messages_joins')
        assert message == '<p>Hola</p>'

def test_format_message_for_request_no_matches(team):
    # If none of the user languages matches, we should just use the
    # unlocalized message
    with translation.override('pt-br'):
        message = messaging.format_message_for_request(
            team, 'messages_joins')
        assert message == '<p>Hello</p>'

def test_no_settings_at_all(team):
    # If there are no settings at all, even unlocalized settings, the
    # functinons should return the empty string
    user = UserFactory(languages=['en'])

    message = messaging.format_message_for_notification(
        team, user, 'messages_invite')
    assert message == ''

    with translation.override('en'):
        message = messaging.format_message_for_request(
            team, 'messages_invite')
        assert message == ''

def test_format_message_for_notification_old_format(team):
    # When the old_format string is True, then we should render the message as
    # text, separated by a line of "--------'
    user = UserFactory(languages=['en', 'es', 'ja'])
    message = messaging.format_message_for_notification(
        team, user, 'messages_joins', old_format=True)
    assert message == """\
Hello

----------------

Hola"""
