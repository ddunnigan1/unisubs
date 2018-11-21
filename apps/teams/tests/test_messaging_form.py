import mock
import pytest

from teams import forms
from teams.models import Setting
from utils.factories import *

@pytest.fixture(name='team_factory')
def team_factory_fixture():
    def create_team(messages):
        team = TeamFactory()
        for language_code, name, text in messages:
            team.settings.create(
                team=team,
                key=Setting.KEY_IDS[name],
                language_code=language_code,
                data=text)
        return team
    return create_team

def check_team_messages(team, correct_message_settings):
    team_message_settings = []
    for setting in team.settings.messaging():
        if setting.data:
            team_message_settings.append(
                (setting.language_code, setting.key_name, setting.data))

    assert sorted(team_message_settings) == sorted(correct_message_settings)

def test_initial_data(team_factory):
    team = team_factory([
        ('', 'messages_joins', 'Hello'),
        ('es', 'messages_joins', 'Hola'),
        ('', 'messages_invite', 'Please join'),
    ])
    formset = forms.MessagingFormSet(team)
    assert formset.forms[0].initial == {
        'language_code': '',
        'messages_joins': 'Hello',
        'messages_invite': 'Please join',
    }
    assert formset.forms[1].initial == {
        'language_code': 'es',
        'messages_joins': 'Hola',
    }

def test_save_new_messages(team_factory):
    team = team_factory([])
    formset = forms.MessagingFormSet(team, data={
        'form-TOTAL_FORMS': '2',
        'form-INITIAL_FORMS': '2',

        'form-0-language_code': '',
        'form-0-messages_joins': 'Hi',
        'form-0-messages_invite': 'Join our team',

        'form-1-language_code': 'fr',
        'form-1-messages_joins': 'Bonjour',
    })

    assert formset.is_valid()
    formset.save()

    check_team_messages(team, [
        ('', 'messages_joins', 'Hi'),
        ('', 'messages_invite', 'Join our team'),
        ('fr', 'messages_joins', 'Bonjour'),
    ])

def test_update_existing_messages(team_factory):
    team = team_factory([
        ('', 'messages_joins', 'Hiya'),
        ('es', 'messages_joins', 'Hola'),
    ])
    formset = forms.MessagingFormSet(team, data={
        'form-TOTAL_FORMS': '2',
        'form-INITIAL_FORMS': '2',

        'form-0-language_code': '',
        'form-0-messages_joins': 'Hi',

        'form-1-language_code': 'fr',
        'form-1-messages_joins': 'Bonjour',
    })

    assert formset.is_valid()
    formset.save()

    check_team_messages(team, [
        ('', 'messages_joins', 'Hi'),
        ('fr', 'messages_joins', 'Bonjour'),
    ])


def check_guideline_fields(team, correct_fields):
    formset = forms.MessagingFormSet(team)
    form_fields = [
        key for key in formset.main_form().fields.keys()
        if key.startswith('guidelines_')
    ]
    assert form_fields == correct_fields

    # Also check out the settings_names method, which we use to delete
    # old settings when the form is submitted.
    settings_names = set(
        name for name in formset.settings_names()
        if name.startswith('guidelines_')
    )
    assert settings_names == set(correct_fields)

def test_editor_guideline_fields(team_factory):
    team = team_factory([])
    team.new_workflow.review_enabled = mock.Mock(return_value=True)
    team.new_workflow.approve_enabled = mock.Mock(return_value=True)
    check_guideline_fields(team, [
        'guidelines_subtitle',
        'guidelines_translate',
        'guidelines_review',
        'guidelines_approve',
    ])

    team.new_workflow.review_enabled.return_value = False
    check_guideline_fields(team, [
        'guidelines_subtitle',
        'guidelines_translate',
        'guidelines_approve',
    ])

    team.new_workflow.approve_enabled.return_value = False
    check_guideline_fields(team, [
        'guidelines_subtitle',
        'guidelines_translate',
    ])
