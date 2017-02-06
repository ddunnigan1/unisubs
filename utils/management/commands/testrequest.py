# Amara, universalsubtitles.org
#
# Copyright (C) 2017 Participatory Culture Foundation
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

from urlparse import urlparse, parse_qs

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.management.base import BaseCommand
from django.core.urlresolvers import resolve
from django.test import RequestFactory

from auth.models import CustomUser as User
from localeurl.utils import strip_path
from auth.middleware import AmaraAuthenticationMiddleware

middleware_to_apply = [
    SessionMiddleware(),
    AmaraAuthenticationMiddleware(),
]

class Command(BaseCommand):
    help = u'Run a test request'
    
    def handle(self, *args, **kwargs):
        try:
            url = args[0]
        except IndexError:
            self.stderr.write("manage testrequest url [username]\n")
            return
        try:
            username = args[1]
        except IndexError:
            user = AnonymousUser()
        else:
            user = User.objects.get(username=username)
        path, query = self.parse_url(url)
        request = RequestFactory().get(path, query)
        request.LANGUAGE_CODE = 'en'
        request.user = user
        for middleware in middleware_to_apply:
            middleware.process_request(request)
        match = resolve(path)
        response = match.func(request, *match.args, **match.kwargs)
        if hasattr(response, 'render'):
            response.render()
        print response.status_code
        print response.content

    def parse_url(self, url):
        parsed = urlparse(url)
        locale, path = strip_path(parsed.path)
        return path, parse_qs(parsed.query)

