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

class Page(object):
    # Subclasses should define this as
    path = None

    def __init__(self, driver, base_url, language_code='en', navigate=True):
        self.driver = driver
        self.base_url = base_url
        self.language_code = language_code
        if navigate:
            self.navigate()

    def full_url(self):
        assert self.path is not None
        return '{}{}/{}'.format(self.base_url, self.language_code, self.path)

    def navigate(self):
        self.driver.get(self.full_url())
