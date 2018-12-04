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

from datetime import timedelta

import mock
import pytest

from usernotifications.tests.test_notify_users import MockNotification
from teams.member_notifications import notify_members
from teams.const import *
from teams.permissions_const import *
from utils.bunch import Bunch
from utils.factories import *

@pytest.fixture
def team():
    team = TeamFactory()

    team.admins = [
        TeamMemberFactory(team=team, role=ROLE_OWNER,
                          user__first_name='owner').user,
        TeamMemberFactory(team=team, role=ROLE_ADMIN,
                          user__first_name='admin').user,
    ]
    team.managers = [
        TeamMemberFactory(team=team, role=ROLE_MANAGER,
                          user__first_name='manager-{}'.format(i)).user
        for i in range(2)
    ]
    team.contributors = [
        TeamMemberFactory(team=team, role=ROLE_CONTRIBUTOR,
                          user__first_name='contributor-{}'.format(i)).user
        for i in range(2)
    ]

    team.project = ProjectFactory(team=team)
    team.project_video = TeamVideoFactory(team=team, project=team.project,
                                          added_by=team.admins[0]).video
    return team

@pytest.fixture
def patch_notify_users(patch_for_test):
    mock_notify_users = patch_for_test('teams.member_notifications.notify_users')
    def check_call(correct_users, rate_limit_by_type=None):
        assert mock_notify_users.called
        assert mock_notify_users.call_args == mock.call(
            MockNotification(), mock.ANY,
            rate_limit_by_type=rate_limit_by_type)

        user_list_arg = mock_notify_users.call_args[0][1]
        assert set(user_list_arg) == set(u.id for u in correct_users)
    return Bunch(mock_notify_users=mock_notify_users,
                 check_call=check_call)

def test_notify_members(team, patch_notify_users):
    notify_members(MockNotification(), team, TeamNotify.MEMBERS)
    patch_notify_users.check_call(
        team.admins + team.managers + team.contributors)

def test_notify_managers(team, patch_notify_users):
    notify_members(MockNotification(), team, TeamNotify.MANAGERS)
    patch_notify_users.check_call(team.admins + team.managers)

def test_project_managers(team, patch_notify_users):
    project_manager = team.contributors[0]
    team.get_member(project_manager).make_project_manager(team.project)
    notify_members(MockNotification(), team, TeamNotify.MANAGERS,
                   video=team.project_video)
    patch_notify_users.check_call(team.admins + team.managers +
                                  [project_manager])

def test_language_managers(team, patch_notify_users):
    language_manager = team.contributors[0]
    team.get_member(language_manager).make_language_manager('en')
    notify_members(MockNotification(), team, TeamNotify.MANAGERS,
                   language_code='en')
    patch_notify_users.check_call(team.admins + team.managers +
                                  [language_manager])

def test_language_and_project_managers_with_other_settings(
        team, patch_notify_users):
    # for settings other than TeamNotify.MANAGERS, we should ignore project
    # managers
    language_manager = team.contributors[0]
    team.get_member(language_manager).make_language_manager('en')
    project_manager = team.contributors[1]
    team.get_member(project_manager).make_project_manager(team.project)

    notify_members(MockNotification(), team, TeamNotify.MEMBERS,
                   language_code='en', video=team.project_video)
    patch_notify_users.check_call(team.admins + team.managers +
                                  team.contributors)

    patch_notify_users.mock_notify_users.reset()
    notify_members(MockNotification(), team, TeamNotify.ADMINS,
                   language_code='en', video=team.project_video)
    patch_notify_users.check_call(team.admins)

def test_notify_admins(team, patch_notify_users):
    notify_members(MockNotification(), team, TeamNotify.ADMINS)
    patch_notify_users.check_call(team.admins)

def test_exclude(team, patch_notify_users):
    notify_members(MockNotification(), team, TeamNotify.MANAGERS,
                   exclude=[team.admins[0]])

    patch_notify_users.check_call(team.admins[1:] + team.managers)

def test_rate_limit_by_type(team, patch_notify_users):
    notify_members(MockNotification(), team, TeamNotify.MANAGERS,
                   rate_limit_by_type=timedelta(hours=1))

    patch_notify_users.check_call(team.admins + team.managers,
                                  rate_limit_by_type=timedelta(hours=1))

def test_other_values_is_noop(team, patch_notify_users):
    notify_members(MockNotification(), team, TeamNotify.ASSIGNEES)

    assert not patch_notify_users.mock_notify_users.called
