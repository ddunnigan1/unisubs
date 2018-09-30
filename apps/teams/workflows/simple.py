# Amara, universalsubtitles.org
#
# Copyright (C) 2015 Participatory Culture Foundation
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

from __future__ import absolute_import

from django.contrib import messages
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from teams import views as old_views
from teams import forms
from teams.models import Team
from teams.workflows import TeamWorkflow
from utils.breadcrumbs import BreadCrumb
from .subtitleworkflows import TeamVideoWorkflow
from videos.behaviors import VideoPageCustomization, SubtitlesPageCustomization

def render_team_header(request, team):
    return render_to_string('future/header.html', {
        'team': team,
        'brand': 'future/teams/brand.html',
        'brand_url': team.get_absolute_url(),
        'primarynav': 'future/teams/primarynav.html',
    }, request)

class SimpleVideoPageCustomization(VideoPageCustomization):
    def __init__(self, team, request, video):
        self.team = team
        self.request = request
        self.sidebar = None
        self.setup_header()

    def setup_header(self):
        if self.team:
            self.header = render_team_header(self.request, self.team)
        else:
            self.header = None

class SimpleSubtitlesPageCustomization(SubtitlesPageCustomization):
    def __init__(self, request, video, subtitle_language, team):
        try:
            team_slug = request.GET.get('team', None)
        except KeyError:
            team_slug = None

        super(SimpleSubtitlesPageCustomization, self).__init__(request.user, video, subtitle_language, team_slug)
        self.request = request
        self.team = team
        self.setup_header()

    def setup_header(self):
        if self.team:
            self.header = render_team_header(self.request, self.team)
        else:
            self.header = None

class SimpleTeamWorkflow(TeamWorkflow):
    """Workflow for basic public/private teams

    This class implements a basic workflow for teams:  Members can edit any
    subtitles, non-members can't edit anything.
    """

    type_code = 'S'
    label = _('Simple')
    api_slug = 'simple'
    dashboard_view = staticmethod(old_views.old_dashboard)
    member_view = NotImplemented

    def get_subtitle_workflow(self, team_video):
        """Get the SubtitleWorkflow for a video with this workflow.  """
        return TeamVideoWorkflow(team_video)

    def workflow_settings_view(self, request, team):
        if request.method == 'POST':
            form = forms.SimplePermissionsForm(instance=team,
                                               data=request.POST)
            if form.is_valid():
                form.save(request.user)
                messages.success(request, _(u'Workflow updated'))
                return redirect('teams:settings_workflows', team.slug)
            else:
                messages.error(request, form.errors.as_text())
        else:
            form = forms.SimplePermissionsForm(instance=team)

        return render(request, "new-teams/settings-simple-workflow.html", {
            'team': team,
            'form': form,
            'breadcrumbs': [
                BreadCrumb(team, 'teams:dashboard', team.slug),
                BreadCrumb(_('Settings'), 'teams:settings_basic', team.slug),
                BreadCrumb(_('Workflow')),
            ],
        })

    def video_page_customize(self, request, video):
        team = self.find_team_for_page(request)
        return SimpleVideoPageCustomization(team, request, video)

    def subtitles_page_customize(self, request, video, subtitle_language):
        team = self.find_team_for_page(request)
        return SimpleSubtitlesPageCustomization(request, video, subtitle_language, team)

    def find_team_for_page(self, request):
        slug = request.GET.get('team')
        if slug == self.team.slug:
            team = self.team
        else:
            try:
                team = Team.objects.get(slug=slug)
            except Team.DoesNotExist:
                return None
        if team.user_is_member(request.user):
            return team
        else:
            return None
