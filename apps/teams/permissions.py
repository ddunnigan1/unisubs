# Universal Subtitles, universalsubtitles.org
#
# Copyright (C) 2011 Participatory Culture Foundation
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

from django.db.models import Q
from teams.models import Team, MembershipNarrowing, Workflow, TeamMember, Task

from teams.permissions_const import (
    ROLES_ORDER, ROLE_OWNER, ROLE_CONTRIBUTOR, ROLE_ADMIN, ROLE_MANAGER,
    ROLE_OUTSIDER
)


def _perms_equal_or_lower(role, include_outsiders=False):
    """Return a list of roles equal to or less powerful than the given role.

    If `include_outsiders` is given ROLE_OUTSIDER may be included.

    """
    roles = ROLES_ORDER

    if include_outsiders:
        roles = roles + [ROLE_OUTSIDER]

    return roles[roles.index(role):]

def _perms_equal_or_greater(role, include_outsiders=False):
    """Return a list of roles equal to or more powerful than the given role.

    If `include_outsiders` is given ROLE_OUTSIDER may be included.

    """
    roles = ROLES_ORDER

    if include_outsiders:
        roles = roles + [ROLE_OUTSIDER]

    return roles[:roles.index(role) + 1]


# Utility functions
def get_member(user, team):
    """Return the TeamMember object (or None) for the given user/team."""

    if not user.is_authenticated():
        return None

    if hasattr(user, '_cached_teammember') and user._cached_teammember.get(team.pk):
        return user._cached_teammember[team.pk]
    else:
        if not hasattr(user, '_cached_teammember'):
            user._cached_teammember = {}

        try:
            user._cached_teammember[team.pk] = team.members.get(user=user)
        except TeamMember.DoesNotExist:
            user._cached_teammember[team.pk] = None

        return user._cached_teammember[team.pk]

def get_role(member):
    """Return the member's general role in the team.

    Does NOT take narrowings into account!

    """
    if not member:
        return ROLE_OUTSIDER
    else:
        return member.role

def get_role_for_target(user, team, project=None, lang=None):
    """Return the role the given user effectively has for the given target.

    `lang` should be a string (the language code).

    """
    member = get_member(user, team)
    role = get_role(member)
    narrowings = get_narrowings(member)

    # If the user has no narrowings, just return their overall role.
    if not narrowings:
        return role

    # Otherwise the narrowings must match the target.
    project_narrowings = [n.project for n in narrowings if n.project]
    lang_narrowings = [n.language for n in narrowings if n.language]

    # The default project is the same as "no project".
    if project and project.is_default_project:
        project = None

    if project_narrowings and project not in project_narrowings:
        return ROLE_CONTRIBUTOR

    if lang_narrowings and lang not in lang_narrowings:
        return ROLE_CONTRIBUTOR

    return role


def roles_user_can_assign(team, user, to_user=None):
    """Return a list of the roles the given user can assign for the given team.

    Rules:

        * Unrestricted admins and owners can assign any role but owners.
        * No one else can assign any roles.
        * Admins cannot change the role of an owner.

    """
    user_role = get_role_for_target(user, team)

    if user_role == ROLE_OWNER:
        return ROLES_ORDER[1:]
    elif user_role == ROLE_ADMIN:
        if to_user:
            if get_role(get_member(to_user, team)) == ROLE_OWNER:
                return []
        return ROLES_ORDER[1:]
    else:
        return []

def roles_user_can_invite(team, user):
    """Return a list of the roles the given user can invite for the given team.

    Rules:

        * Unrestricted owners and admins can invite all roles but owner.
        * Everyone else can only invite contributors.

    """
    user_role = get_role_for_target(user, team)

    if user_role in [ROLE_OWNER, ROLE_ADMIN]:
        return ROLES_ORDER[1:]
    else:
        return [ROLE_CONTRIBUTOR]

def save_role(team, member, role, projects, languages, user=None):

    languages = languages or []

    if can_assign_role(team, user, role, member.user):
        member.role = role
        member.save()

        set_narrowings(member, projects, languages, user)
        return True
    return False


# Narrowings
def get_narrowings(member):
    """Return narrowings for the given member in the given team."""

    if not member:
        return []
    else:
        return list(member.narrowings_fast())

def add_narrowing_to_member(member, project=None, language=None, added_by=None):
    """Add a narrowing to the given member for the given project or language.

    `project` must be a Project object.
    `language` must be a language code like 'en'.
    `added_by` must be a TeamMember object.

    """
    if not language:
        language = ''

    narrowing = MembershipNarrowing(member=member, project=project, language=language, added_by=added_by)
    narrowing.save()

    return narrowing


def _add_project_narrowings(member, project_pks, author):
    for project_pk in project_pks:
        project = member.team.project_set.get(pk=project_pk)
        MembershipNarrowing(project=project, member=member, added_by=author).save()

def _del_project_narrowings(member, project_pks):
    project_narrowings = member.narrowings.filter(project__isnull=False)

    for project_pk in project_pks:
        project_narrowings.get(project=project_pk).delete()

def _add_language_narrowings(member, languages, author):
    for language in languages:
        MembershipNarrowing(language=language, member=member, added_by=author).save()

def _del_language_narrowings(member, languages):
    for language in languages:
        MembershipNarrowing.objects.get(language=language, member=member).delete()


def can_set_language_narrowings(team, user, target):
    # role = get_role_for_target(user, team)
    target_role = get_role(get_member(target, team))

    if target_role not in [ROLE_MANAGER]:
        return False

    return True

def can_set_project_narrowings(team, user, target):
    # role = get_role_for_target(user, team)
    target_role = get_role(get_member(target, team))

    if target_role not in [ROLE_MANAGER, ROLE_ADMIN]:
        return False

    return True


def set_narrowings(member, project_pks, languages, author=None):
    if author:
        author = TeamMember.objects.get(team=member.team, user=author)
    # Projects
    existing_projects = set(narrowing.project.pk for narrowing in
                            member.narrowings.filter(project__isnull=False))
    desired_projects = set(project_pks)

    projects_to_create = desired_projects - existing_projects
    projects_to_delete = existing_projects - desired_projects

    _add_project_narrowings(member, projects_to_create, author)
    _del_project_narrowings(member, projects_to_delete)

    # Languages
    existing_languages = set(narrowing.language for narrowing in
                             member.narrowings.filter(project__isnull=True))
    desired_languages = set(languages)

    languages_to_create = desired_languages - existing_languages
    languages_to_delete = existing_languages - desired_languages

    _add_language_narrowings(member, languages_to_create, author)
    _del_language_narrowings(member, languages_to_delete)


# Roles
def add_role(team, cuser, added_by, role, project=None, lang=None):
    from teams.models import TeamMember

    member, created = TeamMember.objects.get_or_create(
        user=cuser, team=team, defaults={'role': role})
    member.role = role
    member.save()

    if project or lang:
        add_narrowing_to_member(member, project, lang, added_by)

    return member

def remove_role(team, user, role, project=None, lang=None):
    role = role or ROLE_CONTRIBUTOR
    team.members.filter(user=user, role=role).delete()


# Various permissions
def can_assign_role(team, user, role, to_user):
    """Return whether the given user can assign the given role to the given other user.

    Only unrestricted owners can ever assign the owner role.

    Only unrestricted admins (and owners, of course) can assign any other role
    (for now).

    Admins cannot change the roles of Owners.

    """
    return role in roles_user_can_assign(team, user, to_user)

def can_join_team(team, user):
    """Return whether the given user can join a team.

    Users can join a team iff:

    * They are not already a member.
    * The team has an open joining policy.

    Otherwise they need to be invited or fill out an application.

    """
    role = get_role_for_target(user, team)
    if role != ROLE_OUTSIDER:
        return False

    if team.membership_policy != Team.OPEN:
        return False

    return True

def can_rename_team(team, user):
    """Return whether the given user can edit the name of a team.

    Only team owners can rename teams.

    """
    role = get_role_for_target(user, team)
    return role == ROLE_OWNER


def can_add_video(team, user, project=None):
    """Return whether the given user can add a video to the given target."""

    role = get_role_for_target(user, team, project)
    role_required = {
        1: ROLE_CONTRIBUTOR,
        2: ROLE_MANAGER,
        3: ROLE_ADMIN,
    }[team.video_policy]

    return role in _perms_equal_or_greater(role_required)

def can_add_video_somewhere(team, user):
    """Return whether the given user can add a video somewhere in the given team."""

    # TODO: Make this faster.
    return any(can_add_video(team, user, project)
               for project in team.project_set.all())

def can_remove_video(team_video, user):
    """Return whether the given user can remove the given video."""

    role = get_role_for_target(user, team_video.team, team_video.project)

    role_required = {
        1: ROLE_CONTRIBUTOR,
        2: ROLE_MANAGER,
        3: ROLE_ADMIN,
    }[team_video.team.video_policy]

    return role in _perms_equal_or_greater(role_required)

def can_edit_video(team_video, user):
    """Return whether the given user can edit the given video."""

    role = get_role_for_target(user, team_video.team, team_video.project)

    role_required = {
        1: ROLE_CONTRIBUTOR,
        2: ROLE_MANAGER,
        3: ROLE_ADMIN,
    }[team_video.team.video_policy]

    return role in _perms_equal_or_greater(role_required)


def can_view_settings_tab(team, user):
    """Return whether the given user can view (and therefore edit) the team's settings.

    The user must be an unrestricted admin or an owner to do so.

    """
    role = get_role_for_target(user, team)

    return role in [ROLE_ADMIN, ROLE_OWNER]

def can_change_team_settings(team, user):
    return can_view_settings_tab(team, user)

def can_view_tasks_tab(team, user):
    """Return whether the given user can view the tasks tab for the given team.

    Only team members can see the tasks tab.

    """
    if not user or not user.is_authenticated():
        return False

    return team.members.filter(user=user).exists()

def can_invite(team, user):
    """Return whether the given user can send an invite for the given team."""

    role = get_role_for_target(user, team)

    role_required = {
        4: ROLE_CONTRIBUTOR,  # Open (but you have to be a member to send an invite)
        1: ROLE_ADMIN,        # Application (reviewed by admins, so only admins can invite)
        3: ROLE_CONTRIBUTOR,  # Invitation by any team member
        2: ROLE_MANAGER,      # Invitation by manager
        5: ROLE_ADMIN,        # Invitation by admin
    }[team.membership_policy]

    return role in _perms_equal_or_greater(role_required)

def can_change_video_settings(user, team_video):
    role = get_role_for_target(user, team_video.team, team_video.project, None)
    return role in [ROLE_MANAGER, ROLE_ADMIN, ROLE_OWNER]

def can_review(team_video, user, lang=None):
    workflow = Workflow.get_for_team_video(team_video)
    role = get_role_for_target(user, team_video.team, team_video.project, lang)

    # For now, don't allow review if it's disabled in the workflow.
    # TODO: Change this to allow one-off reviews?
    if not workflow.review_allowed:
        return False

    role_req = {
        10: ROLE_CONTRIBUTOR,
        20: ROLE_MANAGER,
        30: ROLE_ADMIN,
    }[workflow.review_allowed]

    return role in _perms_equal_or_greater(role_req)

def can_approve(team_video, user, lang=None):
    workflow = Workflow.get_for_team_video(team_video)
    role = get_role_for_target(user, team_video.team, team_video.project, lang)

    if not workflow.approve_allowed:
        return False

    role_req = {
        10: ROLE_MANAGER,
        20: ROLE_ADMIN,
    }[workflow.approve_allowed]

    return role in _perms_equal_or_greater(role_req)

def can_message_all_members(team, user):
    role = get_role_for_target(user, team)
    return role in [ROLE_ADMIN, ROLE_OWNER]

def can_edit_project(team, user, project):
    # when checking for the permission to create a project
    # project will be none
    if project and project.is_default_project:
        return False

    role = get_role_for_target(user, team, project, None)
    return role in [ROLE_ADMIN, ROLE_OWNER]

def can_create_and_edit_subtitles(user, team_video, lang=None):
    role = get_role_for_target(user, team_video.team, team_video.project, lang)

    role_req = {
        10: ROLE_OUTSIDER,
        20: ROLE_CONTRIBUTOR,
        30: ROLE_MANAGER,
        40: ROLE_ADMIN,
    }[team_video.team.subtitle_policy]

    return role in _perms_equal_or_greater(role_req, include_outsiders=True)

def can_create_and_edit_translations(user, team_video, lang=None):
    role = get_role_for_target(user, team_video.team, team_video.project, lang)

    role_req = {
        10: ROLE_OUTSIDER,
        20: ROLE_CONTRIBUTOR,
        30: ROLE_MANAGER,
        40: ROLE_ADMIN,
    }[team_video.team.translate_policy]

    return role in _perms_equal_or_greater(role_req, include_outsiders=True)


# Task permissions
def can_create_tasks(team, user, project=None):
    # for now, use the same logic as assignment
    return can_assign_tasks(team, user, project)

def can_delete_tasks(team, user, project=None, lang=None):
    # for now, use the same logic as assignment, minus contributors
    role = get_role_for_target(user, team, project, lang)
    if role == ROLE_CONTRIBUTOR:
        return False
    return can_assign_tasks(team, user, project, lang)

def can_assign_tasks(team, user, project=None, lang=None):
    """Return whether the given user has permission to assign tasks at all."""

    role = get_role_for_target(user, team, project, lang)

    role_required = {
        10: ROLE_CONTRIBUTOR,
        20: ROLE_MANAGER,
        30: ROLE_ADMIN,
    }[team.task_assign_policy]

    return role in _perms_equal_or_greater(role_required)


def can_perform_task_for(user, type, team_video, language):
    """Return whether the given user can perform the given type of task."""

    if type == Task.TYPE_IDS['Subtitle']:
        return can_create_and_edit_subtitles(user, team_video)
    elif type == Task.TYPE_IDS['Translate']:
        return can_create_and_edit_translations(user, team_video, language)
    elif type == Task.TYPE_IDS['Review']:
        return can_review(team_video, user, language)
    elif type == Task.TYPE_IDS['Approve']:
        return can_approve(team_video, user, language)

def can_perform_task(user, task):
    """Return whether the given user can perform the given task."""

    return can_perform_task_for(user, task.type, task.team_video, task.language)

def can_assign_task(task, user):
    """Return whether the given user can assign the given task.

    Users can assign tasks iff:

    * They are a high enough role to do so according to the team permissions.
    * They can perform the task themselves.

    """
    team, project, lang = task.team, task.team_video.project, task.language


    return can_assign_tasks(team, user, project, lang) and can_perform_task(user, task)

def can_delete_task(task, user):
    """Return whether the given user can delete the given task."""

    team, project, lang = task.team, task.team_video.project, task.language

    return can_delete_tasks(team, user, project, lang) and can_perform_task(user, task)


def _user_can_create_task_subtitle(user, team_video):
    role = get_role_for_target(user, team_video.team, team_video.project, None)

    role_req = {
        10: ROLE_CONTRIBUTOR,
        20: ROLE_MANAGER,
        30: ROLE_ADMIN,
    }[team_video.team.task_assign_policy]

    return role in _perms_equal_or_greater(role_req)

def _user_can_create_task_translate(user, team_video):
    # TODO: Take language into account here
    role = get_role_for_target(user, team_video.team, team_video.project, None)

    role_req = {
        10: ROLE_CONTRIBUTOR,
        20: ROLE_MANAGER,
        30: ROLE_ADMIN,
    }[team_video.team.task_assign_policy]

    return role in _perms_equal_or_greater(role_req)

def _user_can_create_task_review(user, team_video, workflows=None):
    workflow = Workflow.get_for_team_video(team_video, workflows)

    if not workflow.review_enabled:
        # TODO: Allow users to create on-the-fly review tasks even if reviewing
        #       is not enabled in the workflow?
        return False

    # TODO: Take language into account here
    role = get_role_for_target(user, team_video.team, team_video.project, None)

    role_req = {
        10: ROLE_CONTRIBUTOR,
        20: ROLE_MANAGER,
        30: ROLE_ADMIN,
    }[workflow.review_allowed]

    return role in _perms_equal_or_greater(role_req)

def _user_can_create_task_approve(user, team_video, workflows=None):
    workflow = Workflow.get_for_team_video(team_video, workflows)

    if not workflow.approve_enabled:
        return False

    # TODO: Take language into account here
    role = get_role_for_target(user, team_video.team, team_video.project, None)

    role_req = {
        10: ROLE_MANAGER,
        20: ROLE_ADMIN,
    }[workflow.approve_allowed]

    return role in _perms_equal_or_greater(role_req)


def can_create_task_subtitle(team_video, user=None, workflows=None):
    """Return whether the given video can have a subtitle task created for it.

    If a user is given, return whether *that user* can create the task.

    A subtitle task can be created iff:

    * There are no subtitles for the video already.
    * There are no subtitle tasks for it already.
    * The user has permission to create subtitle tasks.

    """
    if user and not _user_can_create_task_subtitle(user, team_video):
        return False

    if team_video.subtitles_started():
        return False

    if team_video.task_set.all_subtitle().exists():
        return False

    return True

def can_create_task_translate(team_video, user=None, workflows=None):
    """Return a list of languages for which a translate task can be created for the given video.

    If a user is given, filter that list to contain only languages the user can
    create tasks for.

    A translation task can be created for a given language iff:

    * There is at least one set of complete subtitles for another language (to
      translate from).
    * There are no translation tasks for that language.
    * The user has permission to create the translation task.

    Note: you *can* create translation tasks if subtitles for that language
    already exist (but not if they're done!).  The task will simply "take over"
    that language from that point forward.

    Languages are returned as strings (language codes like 'en').

    """
    if user and not _user_can_create_task_translate(user, team_video):
        return []

    if hasattr(team_video, 'completed_langs'):
        if not team_video.completed_langs:
            return False
    else:
        if not team_video.subtitles_finished():
            return []

    candidate_languages = set(team_video.team.get_writable_langs())

    existing_translate_tasks = team_video.task_set.all_translate()
    existing_translate_languages = set(t.language for t in existing_translate_tasks)

    if hasattr(team_video, 'completed_langs'):
        existing_languages = set(team_video.completed_langs)
    else:
        existing_languages = set(
                sl.language for sl in team_video.video.completed_subtitle_languages())

    # TODO: Order this for individual users?
    return list(candidate_languages - existing_translate_languages - existing_languages)

def can_create_task_review(team_video, user=None, workflows=None):
    """Return a list of languages for which a review task can be created for the given video.

    If a user is given, filter that list to contain only languages the user can
    create tasks for.

    A review task can be created for a given language iff:

    * There is a set of complete subtitles for that language.
    * There are no open translation tasks for that language.
    * There are no review tasks for that language.
    * There are no approve tasks for that language.
    * The user has permission to create the review task.

    Languages are returned as strings (language codes like 'en').

    """
    if user and not _user_can_create_task_review(user, team_video, workflows):
        return []

    # Find all languages that have a complete set of subtitles.
    # These are the ones we *might* be able to create a review task for.
    candidate_langs = set(sl.language for sl in team_video.video.completed_subtitle_languages())

    # Find all the languages that have a task which prevents a review task creation.
    existing_task_langs = set(team_video.task_set.not_deleted().filter(
            Q(completed=None, type=Task.TYPE_IDS['Translate']) # Incomplete Translate tasks
          | Q(type=Task.TYPE_IDS['Review'])                    # Any Review task
          | Q(type=Task.TYPE_IDS['Approve'])                   # Any Approve task
    ).values_list('language', flat=True))

    # Return the candidate languages that don't have a review-preventing task.
    return list(candidate_langs - existing_task_langs)

def can_create_task_approve(team_video, user=None, workflows=None):
    """Return a list of languages for which an approve task can be created for the given video.

    If a user is given, filter that list to contain only languages the user can
    create tasks for.

    An approve task can be created for a given language iff:

    * If reviewing is enabled in the workflow:
        * There is a review task marked as accepted for that language.
    * If reviewing is NOT enabled in the workflow:
        * There is a set of complete subtitles for that language.
    * There are no open translation tasks for that language.
    * There are no approve tasks for that language.
    * The user has permission to create the approve task.

    Languages are returned as strings (language codes like 'en').

    """
    if user and not _user_can_create_task_approve(user, team_video, workflows):
        return []

    tasks = team_video.task_set

    # Find all languages we *might* be able to create an approve task for.
    workflow = Workflow.get_for_team_video(team_video, workflows)
    if workflow.review_enabled:
        candidate_langs = set(t.language for t in tasks.complete_review('Approved'))
    else:
        candidate_langs = set(sl.language for sl in team_video.video.completed_subtitle_languages())

    # Find all the languages that have a task which prevents an approve task creation.
    existing_task_langs = set(team_video.task_set.not_deleted().filter(
            Q(completed=None, type=Task.TYPE_IDS['Translate']) # Incomplete Translate tasks
          | Q(type=Task.TYPE_IDS['Approve'])                   # Any Approve task
    ).values_list('language', flat=True))

    # Return the candidate languages that don't have a review-preventing task.
    return list(candidate_langs - existing_task_langs)

