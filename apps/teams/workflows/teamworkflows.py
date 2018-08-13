# Amara, universalsubtitles.org
#
# Copyright (C) 2014 Participatory Culture Foundation
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

"""
Team Workflows
==============

Team workflows are ways for teams to get their subtitling work done.  Team
workflows compliment the :doc:`subtitle-workflows` and add team-specific
features.

Team workflows are responsible for:
    - Providing a SubtitleWorkflow for team videos
    - Handling the workflow settings page
    - Handling the dashboard page
    - Creating extra tabs or the teams section

..  autoclass:: TeamWorkflow
    :members: label, dashboard_view, workflow_settings_view,
              setup_team, get_subtitle_workflow, extra_pages,
              extra_settings_pages

.. autoclass:: TeamPage

..  autoclass:: teams.workflows.old.workflow.OldTeamWorkflow
"""

from collections import namedtuple

from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.translation import ungettext

from subtitles.models import SubtitleLanguage
from utils.behaviors import DONT_OVERRIDE
from utils.text import fmt

class TeamWorkflow(object):
    label = NotImplemented
    """Human-friendly name for this workflow.  This is what appears on the
    team creation form.
    """
    dashboard_view = NotImplemented
    member_view = NotImplemented
    """
    view function for the dashboard page.
    """
    user_dashboard_extra = None
    """
    Team-specific extra data to render in user dashboard page.
    """
    workflow_settings_view = NotImplemented
    """
    view function for the workflow settings page.

    .. note::
      All workflows should allow the user to change membership_policy and
      video_policy in their workflow settings page.
    """
    def __init__(self, team):
        self.team = team

    def setup_team(self):
        """Do any additional setup for newly created teams."""
        pass

    def get_subtitle_workflow(self, team_video):
        """Get the SubtitleWorkflow for a video with this workflow.  """
        raise NotImplementedError()

    def extra_pages(self, user):
        """Get extra team pages to handle this workflow.

        These pages will be listed as tabs in the team section.  Workflows
        will typically use this for things like dashboard pages.

        Args:
            user -- user viewing the page

        Returns:
            list of :class:`TeamPage` objects
        """
        return []

    def extra_settings_pages(self, user):
        """Get extra team settings pages to handle this workflow.

        This works just like extra_pages(), but the pages will show up as
        tabs under the settings section.

        Args:
            user -- user viewing the page

        Returns:
            list of :class:`TeamPage` objects
        """
        return []

    def team_page(self, name, title, view_name):
        """Convenience function to create an TeamPage object

        This method automatically generates the URL from view_name using
        reverse()
        """
        url = reverse(view_name, kwargs={'slug': self.team.slug})
        return TeamPage(name, title,  url)

    def video_page_customize(self, request, video):
        """Add extra content to the video page when viewing from the context
        of a team."""
        return DONT_OVERRIDE

    def subtitles_page_customize(self, request, video, subtitle_language):
        """Add extra content to the subtitles page when viewing from the context
        of a team."""
        return DONT_OVERRIDE

    def team_video_page_extra_tabs(self, request):
        """Add extra sub tabs to the team video page.

        These appear near the top of the page.
        """
        return []

    def management_page_extra_tabs(self, request, *args, **kwargs):
        """Add extra sub tabs to the team management page.

        These appear near the top of the page.
        """
        return []

    def team_video_page_default(self, request):
        extra_tabs = self.team_video_page_extra_tabs(request)
        if extra_tabs:
            return extra_tabs[0].url
        else:
            return reverse("teams:videos", kwargs={
                'slug': self.team.slug,
            })

    def management_page_default(self, request):
        extra_tabs = self.management_page_extra_tabs(request)
        if extra_tabs:
            return extra_tabs[0].url
        else:
            return reverse("teams:manage_videos", kwargs={
                'slug': self.team.slug,
            })

    def video_management_add_counts(self, videos):
        """Add the subtitle counts for the videos management page

        By default we add the number of completed subtitles, but other
        workflows may want to add other/different counts.

        For each video you can set the counts attribute to a list of strings.
        Each string should describe a count of something, like the number of
        completed subtitles.  The number should be wrapped in a <strong> tag
        (and the whole thing should be wrapped in a mark_safe() call).
        You can also set the counts2 attribute to create a
        second line of counts.

        Args:
            videos -- List of Video instances.
        """
        counts = SubtitleLanguage.count_completed_subtitles(videos)
        for v in videos:
            incomplete_count, completed_count = counts[v.id]
            v.counts = []
            if completed_count > 0:
                msg = ungettext(
                    (u'<strong>%(count)s</strong> subtitle completed'),
                    (u'<strong>%(count)s</strong> subtitles completed'),
                    completed_count)
                v.counts.append(mark_safe(fmt(msg, count=completed_count)))
            if incomplete_count > 0:
                msg = ungettext(
                    (u'<strong>%(count)s</strong> subtitle started'),
                    (u'<strong>%(count)s</strong> subtitles started'),
                    incomplete_count)
                v.counts.append(mark_safe(fmt(msg, count=incomplete_count)))

    def video_management_alter_context_menu(self, video, menu):
        """Alter the context menu for the video management page."""

    def video_management_extra_forms(self):
        """Add extra forms to the video management page """
        return []

    def activity_type_filter_options(self):
        """
        Get possible activity type filter values

        This is used on the activity page to populate the type dropdown.
        """
        return [
            'video-added',
            'comment-added',
            'version-added',
            'video-url-added',
            'member-joined',
            'member-left',
            'video-title-changed',
            'video-deleted',
            'video-url-edited',
            'video-url-deleted',
            'video-moved-from-team',
            'video-moved-to-team',
            'team-settings-changed',
            'language-changed',
        ]

    # these can be used to customize the content in the project/language
    # manager pages
    def render_project_page(self, request, team, project, page_data):
        page_data['videos'] = (team.videos
                             .filter(teamvideo__project=project)
                             .order_by('-id'))[:5]

        return render(request, 'new-teams/project-page.html', page_data)

    def render_all_languages_page(self, request, team, page_data):
        return render(request, 'new-teams/all-languages-page.html', page_data)

    def render_language_page(self, request, team, language_code, page_data):
        qs = (self.team.videos
              .filter(primary_audio_language_code=language_code)
              .order_by('-id'))
        page_data['videos']= qs[:5]
        return render(request, 'new-teams/language-page.html', page_data)

    # map type codes to subclasses
    _type_code_map = {}
    # map API codes to type codes
    _api_code_map = {}

    @classmethod
    def get_workflow(cls, team):
        """Get a TeamWorkflow subclass for a team."""
        klass = cls._type_code_map[team.workflow_type]
        return klass(team)

    @classmethod
    def get_choices(cls):
        choices = [(type_code, subclass.label)
                   for (type_code, subclass) in cls._type_code_map.items()]
        cls._sort_choices(choices)
        return choices

    @classmethod
    def get_api_choices(cls):
        choices = [
            (type_code, api_code)
            for (api_code, type_code) in cls._api_code_map.items()
        ]
        cls._sort_choices(choices)
        return choices

    @classmethod
    def _sort_choices(cls, choices):
        """Sort workflow type choices

        We sort choices so that:
           - unisubs choices are first, then extensions (unisubs choices are
             1-char)
           - after that it's sorted alphabeticaly by code
        """
        choices.sort(key=lambda (code, _): (len(code), code))

    @classmethod
    def register(cls, type_code, api_code=None):
        """Register a TeamWorkflow subclass.

        Calling this class method will enable it for teams whose
        workflow_type value is type_code

        Args:
            type_code: string code value for this workflow.  Workflows in the
                unisubs repository should be 1 char long.  Workflows on other
                repositories should be 2 chars with the first char being
                unique to the repository.
            api_code: API code value for this workflow.  Pass in a non-None
                value to enable creating this workflow via the API
        """
        TeamWorkflow._type_code_map[type_code] = cls
        if api_code is not None:
            TeamWorkflow._api_code_map[api_code] = type_code

TeamPage = namedtuple('TeamPage', 'name title url')
"""Represents a page in the team's section

Attributes:
    name: machine-name for this tuple.  This is value to use for current in
        the _teams/tabs.html template
    title: human friendly tab title
    url: URL for the page
"""
