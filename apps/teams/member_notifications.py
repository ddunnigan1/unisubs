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

from django.db.models import Exists, OuterRef
from django.utils.translation import ugettext as _

from auth.models import CustomUser as User
from usernotifications.notifications import (
    notify_users, notify_user, Notification, NotificationType)
from teams.const import *
from teams.permissions_const import *
from utils.taskqueue import job
from utils.text import fmt

def notify_members(notification, team, setting, video=None,
                   language_code=None, exclude=None, with_languages=None,
                   rate_limit_by_type=None):
    """
    Generic team notification code

    This method handles sending notifications for the generic TeamNotify
    values (MEMBERS, MANAGERS, ADMINS).

    Other TeamNotify values need to be handled with custom code.  This
    function is a no-op for those values.

    Args:
        notification: Notification instance to send
        team: team to notify
        setting: One of the TeamNotify fields from the team object
        video: Video related to the notificaton.  This controls which project
            managers get counted as managers
        language_code: Language related to the notificaton.  This controls
            which language managers get counted as managers
        exclude: list of users to exclude from the notification
        with_languages: Only notify users who have these languages set in
           their profile
        rate_limit_by_type: rate_limit_by_type argument (see notify_users)
    """
    project = None
    if video:
        team_video = video.get_team_video()
        if team_video:
            project = team_video.project
    if setting == TeamNotify.MEMBERS:
        qs = team.members.all()
    elif setting == TeamNotify.MANAGERS:
        qs = team.members.managers(language_code=language_code,
                                   project=project)
    elif setting == TeamNotify.ADMINS:
        qs = team.members.admins()
    else:
        return

    if exclude:
        qs = qs.exclude(user__in=exclude)
    if with_languages:
        user_query = (
            User.objects.all()
            .annotate(speaks_language=Exists(User.objects.filter(
                pk=OuterRef('pk'),
                userlanguage__language__in=with_languages)))
            .filter(speaks_language=True))
        qs = qs.filter(user__in=user_query)

    user_ids = list(qs.values_list('user_id', flat=True))

    notify_users(notification, user_ids, rate_limit_by_type=rate_limit_by_type)

class MemberRoleChangedNotification(Notification):
    """
    Sent to other team members when a manage changes a member's role
    """
    notification_type = NotificationType.ROLE_CHANGED

    def __init__(self, member, old_member_info, managing_user):
        self.member = member
        self.old_member_info = old_member_info
        self.managing_user = managing_user
        self.team = member.team

    def subject(self):
        return _('Member role changed on the {} team').format(
            unicode(self.team))

    template_name = 'messages/team-role-changed.html'
    def get_template_context(self):
        return {
            'team': self.team,
            'member': self.member,
            'old_role_name': self.old_member_info.role_name,
            'new_role_name': self.member.get_role_name(),
            'team_name': unicode(self.team),
            'custom_message': self.team.get_message_for_role(self.member.role),
            'management_url': self.team.new_workflow.management_page_default(self.member.user),
            'was_a_project_or_language_manager': self.old_member_info.project_or_language_manager,
            'languages_managed': self.member.get_languages_managed(),
            'projects_managed': self.member.get_projects_managed(),
        }

class YourRoleChangedNotification(MemberRoleChangedNotification):
    """
    Sent to members when a manager changes their role
    """

    def subject(self):
        if self.was_promotion():
            return fmt(_('You have been promoted on the %(team)s team'),
                       team=unicode(self.member.team))
        else:
            return fmt(_('Your role has been changed on the %(team)s team'),
                       team=unicode(self.member.team))

    def was_promotion(self):
        if (ROLES_ORDER.index(self.old_member_info.role) >
                ROLES_ORDER.index(self.member.role)):
            return True
        if (self.old_member_info.role == ROLE_CONTRIBUTOR and
                not self.old_member_info.project_or_language_manager and
                self.member.is_a_project_or_language_manager()):
            return True
        return False

    template_name = 'messages/team-role-changed-user.html'

def send_role_changed_message(member, old_member_info, managing_user):
    team = member.team

    notify_user(
        YourRoleChangedNotification(member, old_member_info, managing_user),
        member.user,
    )

    notify_members(
        MemberRoleChangedNotification(member, old_member_info, managing_user),
        team, team.notify_team_role_changed,
        exclude=[member.user, managing_user])

class YouHaveBeenInvitedNotification(Notification):
    notification_type = NotificationType.TEAM_INVITATION

    def __init__(self, invite):
        self.invite = invite

    def subject(self):
        return fmt(_(u"You've been invited to the %(team)s team"),
                team=unicode(self.invite.team))

    template_name = 'messages/team-invitation.html'
    def get_template_context(self):
        return {
            'invite': self.invite,
            'role': self.invite.role,
            "user":self.invite.user,
            "inviter":self.invite.author,
            "team": self.invite.team,
            'note': self.invite.note,
            'custom_message': self.invite.team.get_message('messages_invite'),
        }

def team_sends_notification(team, notification_setting_name):
    from teams.models import Setting
    # FIXME update this code
    return not team.settings.filter(key=Setting.KEY_IDS[notification_setting_name]).exists()

def send_invitation_message(invite):
    if not team_sends_notification(invite.team,'block_invitation_sent_message'):
        return False

    notify_user(YouHaveBeenInvitedNotification(invite), invite.user)
