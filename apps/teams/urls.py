# Amara, universalsubtitles.org
#
# Copyright (C) 2013 Participatory Culture Foundation
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

from django.views.generic.base import TemplateView
from django.conf.urls import url, patterns
from teams.rpc import rpc_router

urlpatterns = patterns('teams.views',
    url(r'^$', 'index', name='index'),
    url(r'^my/$', 'index', {'my_teams': True}, name='user_teams'),
    url(r'^create/$', 'create', name='create'),
    url(r'^router/$', rpc_router, name='rpc_router'),
    url(r'^router/api/$', rpc_router.api, name='rpc_api'),
    url(r'^tasks/perform/$', 'perform_task', name='perform_task'),
    url(r'^invite/accept/(?P<invite_pk>\d+)/$', 'accept_invite', name='accept_invite'),
    url(r'^invite/deny/(?P<invite_pk>\d+)/$', 'accept_invite', {'accept': False}, name='deny_invite'),
    url(r'^leave_team/(?P<slug>[-\w]+)/$', 'leave_team', name='leave'),
    url(r'^highlight/(?P<slug>[-\w]+)/$', 'highlight', name='highlight'),
    url(r'^unhighlight/(?P<slug>[-\w]+)/$', 'highlight', {'highlight': False}, name='unhighlight'),
    url(r'^(?P<slug>[-\w]+)/approvals/$', 'approvals', name='approvals'),
    url(r'^(?P<slug>[-\w]+)/application/approve/(?P<application_pk>\d+)/$', 'approve_application', name='approve_application'),
    url(r'^(?P<slug>[-\w]+)/application/deny/(?P<application_pk>\d+)/$', 'deny_application', name='deny_application'),
    url(r'^move/$', 'move_video', name='move_video'),
    url(r'^(?P<slug>[-\w]+)/move-videos/$', 'move_videos', name='move_videos'),
    url(r'^add/video/(?P<slug>[-\w]+)/$', 'add_video', name='add_video'),
    url(r'^add/videos/(?P<slug>[-\w]+)/$', 'add_videos', name='add_videos'),
    url(r'^add-video-to-team/(?P<video_id>(\w|-)+)/', 'add_video_to_team', name='add_video_to_team'),
    url(r'^edit/video/(?P<team_video_pk>\d+)/$', 'team_video', name='team_video'),
    url(r'^remove/video/(?P<team_video_pk>\d+)/$', 'remove_video', name='remove_video'),
    url(r'^remove/members/(?P<slug>[-\w]+)/(?P<user_pk>\d+)/$', 'remove_member', name='remove_member'),
    url(r'^(?P<slug>[-\w]+)/members/role-saved/$', 'role_saved', name='role_saved'),
    url(r'^(?P<slug>[-\w]+)/members/search/$', 'search_members', name='search_members'),
    url(r'^(?P<slug>[-\w]+)/members/(?P<role>(admin|manager|contributor))/$', 'detail_members', name='detail_members_role'),
    url(r'^(?P<slug>[-\w]+)/projects/$', 'project_list', name='project_list'),
    url(r'^(?P<slug>[-\w]+)/tasks/$', 'team_tasks', name='team_tasks'),
    url(r'^(?P<slug>[-\w]+)/create-task/(?P<team_video_pk>\d+)/$', 'create_task', name='create_task'),
    url(r'^(?P<slug>[-\w]+)/delete-task/$', 'delete_task', name='delete_task'),
    url(r'^(?P<slug>[-\w]+)/upload-draft/(?P<video_id>\w+)/$', 'upload_draft', name='upload_draft'),
    url(r'^(?P<slug>[-\w]+)/(?P<task_pk>\d+)/download/(?P<type>[-\w]+)/$', 'download_draft', name='download_draft'),
    url(r'^(?P<slug>[-\w]+)/assign-task/$', 'assign_task', name='assign_task'),
    url(r'^(?P<slug>[-\w]+)/assign-task/a/$', 'assign_task_ajax', name='assign_task_ajax'),
    url(r'^(?P<slug>[-\w]+)/tasks/(?P<task_pk>\d+)/perform/$', 'perform_task', name='perform_task'),
    url(r'^(?P<slug>[-\w]+)/tasks/(?P<task_pk>\d+)/perform/$', 'perform_task', name='perform_task'),
    url(r'^(?P<slug>[-\w]+)/feeds/(?P<feed_id>\d+)$', 'video_feed', name='video_feed'),
    url(r'^(?P<slug>[-\w]+)/settings/projects/add/$', 'add_project', name='add_project'),
    url(r'^(?P<slug>[-\w]+)/settings/languages/$', 'settings_languages', name='settings_languages'),
    # just /p/ will bring all videos on any projects
    url(r'^(?P<slug>[-\w]+)/p/(?P<project_slug>[-\w]+)?/?$', 'detail', name='project_video_list'),
    # TODO: Review these...
    url(r'^(?P<slug>[-\w]+)/p/(?P<project_slug>[-\w]+)/tasks/?$', 'team_tasks', name='project_tasks'),
    url(r'^(?P<slug>[-\w]+)/delete-language/(?P<lang_id>[\w\-]+)/', 'delete_language', name='delete-language'),
    url(r'^(?P<slug>[-\w]+)/auto-captions-status/$', 'auto_captions_status', name='auto-captions-status'),
)

urlpatterns += patterns('teams.new_views',
    url(r'^email_invite/(?P<signed_pk>[0-9]+/[A-Za-z0-9_=-]+)/$', 'email_invite', name='email_invite'),
    url(r'^email_invite/invalid/', 'email_invite_invalid', name='email_invite_invalid'),
    url(r'^(?P<slug>[-\w]+)/applications/$', 'applications', name='applications'),
    url(r'^(?P<slug>[-\w]+)/$', 'dashboard', name='dashboard'),
    url(r'^(?P<slug>[-\w]+)/join/$', 'join', name='join'),
    url(r'^(?P<slug>[-\w]+)/videos/$', 'videos', name='videos'),
    url(r'^(?P<slug>[-\w]+)/videos/ajax-search/$', 'ajax_video_search',
        name='ajax-video-search'),
    url(r'^(?P<slug>[-\w]+)/members/$', 'members', name='members'),
    url(r'^(?P<slug>[-\w]+)/member/(?P<username>.+)/$', 'member_profile', name='member-profile'),
    url(r'^(?P<slug>[-\w]+)/members/ajax-search/$', 'ajax_member_search',
        name='ajax-member-search'),
    url(r'^(?P<slug>[-\w]+)/inviteable_users/ajax-search/$', 'ajax_inviteable_users_search',
        name='ajax-inviteable-users-search'),
    url(r'^(?P<slug>[-\w]+)/inviteable_users/ajax-search/multiple/$', 'ajax_inviteable_users_multiple_search',
        name='ajax-inviteable-users-multiple-search'),
    url(r'^(?P<slug>[-\w]+)/members/invite/$', 'invite', name='invite'),
    url(r'^(?P<slug>[-\w]+)/members/add/$', 'add_members', name='add-members'),
    url(r'^(?P<slug>[-\w]+)/members/invite/autocomplete-user/$',
        'autocomplete_invite_user', name='autocomplete-invite-user'),
    url(r'^(?P<slug>[-\w]+)/admins/$', 'admin_list', name='admin-list'),
    url(r'^(?P<slug>[-\w]+)/activity/$', 'activity', name='activity'),
    url(r'^(?P<slug>[-\w]+)/activity/videosstatistics/$', 'statistics',
        {'tab': 'videosstats'}, name='videosstatistics-activity'),
    url(r'^(?P<slug>[-\w]+)/activity/teamstatistics/$', 'statistics',
        {'tab': 'teamstats', }, name='teamstatistics-activity'),
    url(r'^(?P<slug>[-\w]+)/projects/(?P<project_slug>[-\w]+)/$', 'project', name='project'),
    url(r'^(?P<slug>[-\w]+)/projects/(?P<project_slug>[-\w]+)/autocomplete-manager$', 'autocomplete_project_manager', name='autocomplete-project-manager'),
    url(r'^(?P<slug>[-\w]+)/languages/$', 'all_languages_page', name='all-languages-page'),
    url(r'^(?P<slug>[-\w]+)/languages/(?P<language_code>[-\w]+)/$', 'language_page', name='language-page'),
    url(r'^(?P<slug>[-\w]+)/languages/(?P<language_code>[-\w]+)/autocomplete-manager$', 'autocomplete_language_manager', name='autocomplete-language-manager'),
    url(r'^(?P<slug>[-\w]+)/manage/videos/$', 'manage_videos',
        name='manage_videos'),
    url(r'^(?P<slug>[-\w]+)/manage/videos/project/(?P<project_id>[\d]+)/$', 'manage_videos',
        name='manage_videos_project'),
    url(r'^(?P<slug>[-\w]+)/resources/$', 'resources', name='resources'),
    url(r'^(?P<slug>[-\w]+)/settings/$', 'settings_basic', name='settings_basic'),
    url(r'^(?P<slug>[-\w]+)/settings/messages/$', 'settings_messages', name='settings_messages'),
    url(r'^(?P<slug>[-\w]+)/settings/lang-messages/$', 'settings_lang_messages', name='settings_lang_messages'),
    url(r'^(?P<slug>[-\w]+)/settings/feeds/$', 'settings_feeds', name='settings_feeds'),
    url(r'^(?P<slug>[-\w]+)/settings/projects/$', 'settings_projects', name='settings_projects'),
    url(r'^(?P<slug>[-\w]+)/settings/projects/(?P<project_slug>[-\w]+)/edit/$', 'edit_project', name='edit_project'),
    url(r'^(?P<slug>[-\w]+)/settings/workflows/$', 'settings_workflows', name='settings_workflows'),
    url(r'^(?P<slug>[-\w]+)/video-durations/$', 'video_durations',
        name='video-durations'),
    url(r'^(?P<slug>[-\w]+)/debug-stats/$', 'debug_stats', name='debug-stats'),
)

# settings views that are handled by other apps
urlpatterns += patterns('',
    url(r'^(?P<slug>[-\w]+)/settings/accounts/$', 'externalsites.views.team_settings_tab', name='settings_externalsites'),
    url(r'^(?P<slug>[-\w]+)/settings/sync/$', 'externalsites.views.team_settings_sync_errors_tab', name='settings_sync_externalsites'),
)
