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

import mock
import pytest

from messages.notify import Notifications
from teams import notifymembers
from teams.const import *
from teams.permissions_const import *
from utils.factories import *

TEST_NOTIFICATION = Notifications.ROLE_CHANGED
TEST_SUBJECT = 'test-subject'
TEST_TEMPLATE = 'test-template'
TEST_CONTEXT = {'test': 'context'}

@pytest.fixture
def team():
    team = TeamFactory()

    team.admins = [
        TeamMemberFactory(team=team, role=ROLE_ADMIN,
                          user__first_name='admin-{}'.format(i)).user
        for i in range(2)
    ]
    team.admins.append(TeamMemberFactory(team=team, role=ROLE_OWNER,
                                         user__first_name='owner').user)
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
    return team

@pytest.fixture
def mock_notify_users(patch_for_test):
    return patch_for_test('teams.notifymembers.notify_users')

def check_mock_notify_call(mock_notify_users, correct_users, send_email=None):
    assert mock_notify_users.called
    args, kwargs = mock_notify_users.call_args

    assert args[0] == TEST_NOTIFICATION
    assert set(args[1]) == set(u.id for u in correct_users)
    assert args[2] == TEST_SUBJECT
    assert args[3] == TEST_TEMPLATE
    assert args[4] == TEST_CONTEXT
    assert kwargs == {'send_email': send_email}

def test_notify_members(team, mock_notify_users):
    notifymembers.generic_team_notify(
        TEST_NOTIFICATION, team, TeamNotify.MEMBERS, TEST_SUBJECT,
        TEST_TEMPLATE, TEST_CONTEXT)

    check_mock_notify_call(mock_notify_users,
                           team.admins + team.managers + team.contributors)

def test_notify_managers(team, mock_notify_users):
    notifymembers.generic_team_notify(
        TEST_NOTIFICATION, team, TeamNotify.MANAGERS, TEST_SUBJECT,
        TEST_TEMPLATE, TEST_CONTEXT)

    check_mock_notify_call(mock_notify_users, team.admins + team.managers)

def test_notify_admins(team, mock_notify_users):
    notifymembers.generic_team_notify(
        TEST_NOTIFICATION, team, TeamNotify.ADMINS, TEST_SUBJECT,
        TEST_TEMPLATE, TEST_CONTEXT)

    check_mock_notify_call(mock_notify_users, team.admins)

def test_exclude(team, mock_notify_users):
    notifymembers.generic_team_notify(
        TEST_NOTIFICATION, team, TeamNotify.MANAGERS, TEST_SUBJECT,
        TEST_TEMPLATE, TEST_CONTEXT, exclude=[team.admins[0]])

    check_mock_notify_call(mock_notify_users,
                           team.admins[1:] + team.managers)

def test_other_values_is_noop(team, mock_notify_users):
    notifymembers.generic_team_notify(
        TEST_NOTIFICATION, team, TeamNotify.ASSIGNEES, TEST_SUBJECT,
        TEST_TEMPLATE, TEST_CONTEXT, exclude=[team.admins[0]])

    assert not mock_notify_users.called
