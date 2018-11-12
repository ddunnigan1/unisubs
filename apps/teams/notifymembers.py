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

from django.utils.translation import ugettext as _

from messages.notify import notify_users, Notifications
from teams.const import *
from teams.permissions_const import *
from utils.taskqueue import job
from utils.text import fmt

def generic_team_notify(notification, team, team_notify, subject, template_name, context,
                        send_email=None, exclude=None):
    """
    Generic team notification code

    This method handles sending notifications for the more general TeamNotify
    values (MEMBERS, MANAGERS, ADMINS).

    Other TeamNotify values need to be handled with custom code.  This
    function is a no-op for those values.
    """
    if team_notify == TeamNotify.MEMBERS:
        qs = team.members.all()
    elif team_notify == TeamNotify.MANAGERS:
        qs = team.members.managers()
    elif team_notify == TeamNotify.ADMINS:
        qs = team.members.admins()
    else:
        return

    if exclude:
        qs = qs.exclude(user__in=exclude)
    user_ids = list(qs.values_list('user_id', flat=True))
    notify_users(notification, user_ids, subject, template_name, context,
                 send_email=send_email)

def send_role_changed_message(member, old_member_info, managing_user):
    team = member.team
    context = {
        'team': team,
        'member': member,
        'old_role_name': old_member_info.role_name,
        'new_role_name': member.get_role_name(),
        'team_name': unicode(team),
        'custom_message': team.get_message_for_role(member.role),
        'management_url': team.new_workflow.management_page_default(member.user),
        'was_a_project_or_language_manager': old_member_info.project_or_language_manager,
        'languages_managed': member.get_languages_managed(),
        'projects_managed': member.get_projects_managed(),
    }
    if was_promotion(member, old_member_info):
        subject = fmt(_('You have been promoted on the %(team)s team'),
                      team=unicode(team))
    else:
        subject = fmt(_('Your role has been changed on the %(team)s team'),
                      team=unicode(team))
    notify_users(Notifications.ROLE_CHANGED, [member.user], subject,
                 'messages/team-role-changed-user.html', context)

    generic_team_notify(
        Notifications.ROLE_CHANGED, team, team.notify_team_role_changed,
        _('Member role changed on the {} team').format(unicode(team)),
        'messages/team-role-changed.html', context,
        exclude=[member.user, managing_user])

def was_promotion(member, old_member_info):
    if (ROLES_ORDER.index(old_member_info.role) >
            ROLES_ORDER.index(member.role)):
        return True
    if (old_member_info.role == ROLE_CONTRIBUTOR and
            not old_member_info.project_or_language_manager and
            member.is_a_project_or_language_manager()):
        return True
    return False

def team_sends_notification(team, notification_setting_name):
    from teams.models import Setting
    # FIXME update this code
    return not team.settings.filter(key=Setting.KEY_IDS[notification_setting_name]).exists()

def send_invitation_message(invite):
    if not team_sends_notification(invite.team,'block_invitation_sent_message'):
        return False

    context = {
        'invite': invite,
        'role': invite.role,
        "user":invite.user,
        "inviter":invite.author,
        "team": invite.team,
        'note': invite.note,
        'custom_message': invite.team.get_message('messages_invite'),
    }
    title = fmt(_(u"You've been invited to the %(team)s team"),
                team=unicode(invite.team))

    notify_users(Notifications.TEAM_INVITATION, [invite.user], title,
                 'messages/team-invitation.html', context)
