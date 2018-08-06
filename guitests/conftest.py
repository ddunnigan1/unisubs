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

import os

import pytest
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

@pytest.fixture(scope="session")
def driver(request):
    driver = webdriver.Remote(command_executor='http://selenium:4444/wd/hub',
                              desired_capabilities=DesiredCapabilities.FIREFOX)
    request.node.driver = driver
    return driver

# Uncomment to create screenshots for failed tests.  Also make sure to chmod
# 777 guitests/screenshots
#
# @pytest.hookimpl(tryfirst=True, hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     # execute all other hooks to obtain the report object
#     outcome = yield
#     rep = outcome.get_result()
#
#     if (rep.when == "call" and rep.failed):
#         basename = item.nodeid.replace('/', '__')
#         path = '{}/guitests/screenshots/{}.png'.format(
#             settings.PROJECT_ROOT, basename)
#         png_data = item.session.driver.get_screenshot_as_png()
#         with open(path, 'w') as f:
#             f.write(png_data)

@pytest.fixture(scope="session")
def base_url():
    return 'http://{}/'.format(os.environ.get('GUITEST_HOSTNAME'))

def pytest_sessionfinish(session, exitstatus):
    if hasattr(session, 'driver'):
        session.driver.quit()
