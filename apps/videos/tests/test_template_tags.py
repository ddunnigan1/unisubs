# -*- coding: utf-8 -*-
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

from django.contrib.sites.models import Site
from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.test import TestCase

from utils.factories import *
from videos.models import Video
from videos.templatetags.subtitles_tags import language_url
from videos.templatetags.videos_tags import shortlink_for_video
from videos.tests.data import get_video, make_subtitle_language
from videos.tests.videotestutils import WebUseTest

class TestTemplateTags(TestCase):
    def test_language_url_for_empty_lang(self):
        v = get_video(1)
        sl = make_subtitle_language(v, 'en')
        self.assertIsNotNone(language_url(None, sl))

class ShortUrlTest(TestCase):
    def setUp(self):
        self.video = VideoFactory(video_url__url="http://example.com/hey.mp4")
        site = Site.objects.get_current()
        site.domain = "www.amara.org"
        site.save()
        # on production our domain might have www,
        # make sure we have such domain and that
        # www is not present
        self.short_url = shortlink_for_video(self.video)
        Site.objects.clear_cache()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_short_url(self):
        response = self.client.get(self.short_url, follow=True)
        location = response.redirect_chain[-1][0]
        self.assertTrue(location.endswith(self.video.get_absolute_url()))

    def test_short_url_no_locale(self):
        self.assertFalse('/en/' in self.short_url)

    def test_short_url_no_www(self):
        self.assertTrue(self.short_url.startswith('%s://amara.org' % settings.DEFAULT_PROTOCOL))

class PaginatorTest(WebUseTest):
    def setUp(self):
        self.objects = list(range(0, 9))
        self.ITEMS_PER_PAGE = 12

    def test_paginator_object_counts_single_page(self):
        context = dict()
        context['paginator'] = Paginator(self.objects, self.ITEMS_PER_PAGE)
        context['page'] = context['paginator'].page(1)
        response = render_to_string('future/paginator.html', context)

        self.assertIn('{} out of {}'.format(len(self.objects), len(self.objects)), response)

    def test_paginator_object_counts(self):
        context = dict()
        pages = len(self.objects)/self.ITEMS_PER_PAGE + 1
        self.objects += list(range(9, 30))
        context['paginator'] = Paginator(self.objects, self.ITEMS_PER_PAGE)

        # doesn't include last page
        for page_num in range(1, pages):
            context['page'] = context['paginator'].page(page_num)
            start = (page_num-1) * self.ITEMS_PER_PAGE + 1
            end = start + self.ITEMS_PER_PAGE - 1
            response = render_to_string('future/paginator.html', context)
            self.assertIn('{}-{} out of {}'.format(start, end, len(self.objects)), response)

    def test_paginator_object_counts_last(self):
        self.objects += list(range(9, 30))
        context = dict()
        page_num = len(self.objects)/self.ITEMS_PER_PAGE + 1
        context['paginator'] = Paginator(self.objects, self.ITEMS_PER_PAGE)
        context['page'] = context['paginator'].page(page_num)
        response = render_to_string('future/paginator.html', context)

        start = (page_num-1) * self.ITEMS_PER_PAGE + 1
        end = start + (len(self.objects) % self.ITEMS_PER_PAGE) - 1
        self.assertIn('{}-{} out of {}'.format(start, end, len(self.objects)), response)
